from app.db import run_query
from app.graph_state import AgentState


def execute(state: AgentState) -> dict:
    if state.get("error"):
        return {}

    try:
        rows = run_query(state["sql"])
        return {"rows": rows, "error": ""}
    except Exception as exc:
        return {"rows": [], "error": str(exc)}
