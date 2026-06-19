import logging
import re

from app.graph_state import AgentState
from app import config

logger = logging.getLogger(__name__)

_BLOCKED = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|EXEC|EXECUTE|MERGE|TRUNCATE|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def validate_sql(state: AgentState) -> dict:
    sql = state["sql"].strip()

    if not sql.upper().startswith("SELECT"):
        logger.warning("validate_sql — REJECTED: query does not start with SELECT | sql: %s", sql[:80])
        return {"error": "Validation failed: query must start with SELECT."}

    if _BLOCKED.search(sql):
        keyword = _BLOCKED.search(sql).group(0).upper()
        logger.warning("validate_sql — REJECTED: forbidden keyword '%s'", keyword)
        return {"error": f"Validation failed: forbidden keyword '{keyword}'."}

    if not re.search(r"\bTOP\s+\d+\b", sql, re.IGNORECASE):
        sql = re.sub(r"^SELECT\b", f"SELECT TOP {config.SQL_MAX_ROWS}", sql, count=1, flags=re.IGNORECASE)
        logger.debug("validate_sql — injected TOP %d", config.SQL_MAX_ROWS)

    logger.info("validate_sql — OK")
    return {"sql": sql, "error": ""}
