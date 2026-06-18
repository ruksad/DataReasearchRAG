import json
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
- Use ONLY numbers present in the result rows. Never invent figures.
- If the rows don't answer the question, say so plainly.
- If prior turns are provided, you may reference them for context (e.g. "Compared to the previous result...").
- Do not repeat the SQL in your answer."""

_llm = get_llm()


def synthesize(state: AgentState) -> dict:
    if state.get("error") and not state.get("rows"):
        answer = f"I was unable to answer that question. Error: {state['error']}"
        return {"answer": answer}

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
        row_count=len(state["rows"]),
    )

    # Append to in-context history (capped at MAX_HISTORY_TURNS)
    new_turn = {"question": state["question"], "sql": state["sql"], "answer": answer}
    updated_history = (history + [new_turn])[-config.MAX_HISTORY_TURNS:]

    return {"answer": answer, "history": updated_history}
