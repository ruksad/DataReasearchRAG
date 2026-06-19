import json
from datetime import datetime, timezone
from langchain_core.messages import SystemMessage, HumanMessage
from app.llm import get_llm
from app.graph_state import AgentState
from app.memory import persist_turn
from app import config

_SYSTEM = """You are a data analyst writing a concise insight for a business director.
You will be given the conversation history, the current question, the SQL that was run,
and the result rows as JSON.

Rules:
- Write 1–3 sentences.
- Use ONLY numbers from the result rows. Quote them exactly — do not round or restate.
- If a figure appears in your answer it must be present in the provided rows JSON.
- If the rows do not answer the question, say so plainly. Do not guess.
- If prior turns are provided, you may reference them for context (e.g. "Compared to the previous result...").
- Do not repeat the SQL in your answer."""

_llm = get_llm()


def _build_citation(state: AgentState) -> dict:
    rows = state.get("rows") or []
    columns = list(rows[0].keys()) if rows else []
    return {
        "sql": state.get("sql", ""),
        "columns": columns,
        "row_count": len(rows),
        "sample_rows": rows[:5],
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "source": f"MS SQL · {config.MSSQL_DATABASE}",
    }


def synthesize(state: AgentState) -> dict:
    if state.get("error") and not state.get("rows"):
        answer = f"I was unable to answer that question. Error: {state['error']}"
        return {"answer": answer, "citation": {}}

    citation = _build_citation(state)

    history = state.get("history") or []
    history_text = ""
    if history:
        lines = ["Prior conversation:"]
        for turn in history:
            lines.append(f"  Q: {turn['question']}")
            lines.append(f"  A: {turn['answer']}")
        history_text = "\n".join(lines) + "\n\n"

    rows_preview = state["rows"][:20]
    user_content = (
        f"{history_text}"
        f"Current question: {state['question']}\n\n"
        f"SQL executed:\n{state['sql']}\n\n"
        f"Result ({len(state['rows'])} rows, showing first {len(rows_preview)}):\n"
        f"{json.dumps(rows_preview, indent=2, default=str)}"
    )

    messages = [SystemMessage(content=_SYSTEM), HumanMessage(content=user_content)]
    response = _llm.invoke(messages)
    answer = response.content.strip()

    # Persist this turn to dbo.Conversations
    persist_turn(
        session_id=state.get("session_id", "unknown"),
        turn_order=len(history),
        question=state["question"],
        sql=state["sql"],
        answer=answer,
        row_count=citation["row_count"],
    )

    # Append to in-context history (capped at MAX_HISTORY_TURNS)
    new_turn = {"question": state["question"], "sql": state["sql"], "answer": answer}
    updated_history = (history + [new_turn])[-config.MAX_HISTORY_TURNS:]

    return {"answer": answer, "citation": citation, "history": updated_history}
