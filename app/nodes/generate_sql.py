import re
import contextlib
import io
from app.vanna_setup import get_vanna
from app.graph_state import AgentState

_vn = get_vanna()
_FENCE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE) # to make only raw sql no text in it


def _call_vanna(question: str) -> str:
    """Call vanna.generate_sql() silencing its stdout debug prints."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): # to keep verbose output in buf, this keeps console clean
        sql = _vn.generate_sql(question)
    return _FENCE.sub("", sql).strip()


def generate_sql(state: AgentState) -> dict:
    if state.get("error") and state.get("attempts", 0) > 0:
        question = (
            f"{state['question']}\n\n"
            f"Previous SQL failed:\n{state['sql']}\n"
            f"Database error: {state['error']}\n"
            "Fix the SQL and return only the corrected query."
        )
    else:
        question = state["question"]

    sql = _call_vanna(question)

    return {
        "sql": sql,
        "error": "",
        "attempts": state.get("attempts", 0) + 1,
    }
