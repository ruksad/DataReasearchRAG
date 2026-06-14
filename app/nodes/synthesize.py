import json
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from app import config
from app.graph_state import AgentState

_SYSTEM = """You are a data analyst writing a concise insight for a business director.
You will be given a question, the SQL that was run, and the result rows as JSON.

Rules:
- Write 1–3 sentences.
- Use ONLY numbers present in the result rows. Never invent figures.
- If the rows don't answer the question, say so plainly.
- Do not repeat the SQL in your answer."""

_llm = ChatOllama(base_url=config.OLLAMA_BASE_URL, model=config.OLLAMA_MODEL, temperature=0)


def synthesize(state: AgentState) -> dict:
    if state.get("error") and not state.get("rows"):
        return {"answer": f"I was unable to answer that question. Error: {state['error']}"}

    rows_preview = state["rows"][:20]
    user_content = (
        f"Question: {state['question']}\n\n"
        f"SQL executed:\n{state['sql']}\n\n"
        f"Result ({len(state['rows'])} rows, showing first {len(rows_preview)}):\n"
        f"{json.dumps(rows_preview, indent=2, default=str)}"
    )

    messages = [SystemMessage(content=_SYSTEM), HumanMessage(content=user_content)]
    response = _llm.invoke(messages)
    return {"answer": response.content.strip()}
