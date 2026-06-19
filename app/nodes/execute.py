import logging

from app.db import run_query
from app.graph_state import AgentState

logger = logging.getLogger(__name__)


def execute(state: AgentState) -> dict:
    if state.get("error"):
        logger.debug("execute — skipped (validation error upstream)")
        return {}

    try:
        rows = run_query(state["sql"])
        logger.info("execute — OK, %d row(s) returned", len(rows))
        return {"rows": rows, "error": ""}
    except Exception as exc:
        logger.error("execute — query failed: %s", exc)
        return {"rows": [], "error": str(exc)}
