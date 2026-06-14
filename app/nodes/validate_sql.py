import re
from app.graph_state import AgentState
from app import config

_BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|EXEC|EXECUTE|MERGE|TRUNCATE|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def validate_sql(state: AgentState) -> dict:
    sql = state["sql"].strip()

    if not sql.upper().startswith("SELECT"):
        return {"error": "Validation failed: query must start with SELECT."}

    if _BLOCKED.search(sql):
        keyword = _BLOCKED.search(sql).group(0).upper()
        return {"error": f"Validation failed: forbidden keyword '{keyword}'."}

    # inject TOP if missing to cap result size
    if not re.search(r"\bTOP\s+\d+\b", sql, re.IGNORECASE):
        sql = re.sub(r"^SELECT\b", f"SELECT TOP {config.SQL_MAX_ROWS}", sql, count=1, flags=re.IGNORECASE)

    return {"sql": sql, "error": ""}
