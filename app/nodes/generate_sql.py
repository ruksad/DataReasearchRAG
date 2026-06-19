import contextlib
import io
import logging
import re
import time

from app.vanna_setup import get_vanna
from app.graph_state import AgentState

logger = logging.getLogger(__name__)

_vn = get_vanna()
_FENCE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _call_vanna(question: str) -> str:
    """Call vanna.generate_sql() silencing its stdout debug prints."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sql = _vn.generate_sql(question)
    return _FENCE.sub("", sql).strip()


def _build_question(state: AgentState) -> str:
    """Prepend conversation history so the LLM can resolve follow-up references."""
    history = state.get("history") or []
    parts = []

    if history:
        parts.append("Conversation so far:")
        for turn in history:
            parts.append(f"  Q: {turn['question']}")
            parts.append(f"  A: {turn['answer']}")
        parts.append("")

    if state.get("error") and state.get("attempts", 0) > 0:
        parts.append(f"Question: {state['question']}")
        parts.append(f"\nPrevious SQL failed:\n{state['sql']}")
        parts.append(f"Database error: {state['error']}")
        parts.append("Fix the SQL and return only the corrected query.")
    else:
        parts.append(f"Question: {state['question']}")

    return "\n".join(parts)


def generate_sql(state: AgentState) -> dict:
    attempt = state.get("attempts", 0) + 1
    is_repair = bool(state.get("error") and attempt > 1)
    label = f"repair attempt {attempt}" if is_repair else f"attempt {attempt}"
    logger.info("generate_sql — %s | question: %s", label, state["question"][:80])

    t0 = time.perf_counter()
    sql = _call_vanna(_build_question(state))
    elapsed = (time.perf_counter() - t0) * 1000

    sql_preview = sql.replace("\n", " ")[:120]
    logger.info("generate_sql — done in %.1f ms | sql: %s", elapsed, sql_preview)

    return {
        "sql": sql,
        "error": "",
        "attempts": attempt,
    }
