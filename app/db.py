import logging
import time

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from app import config

logger = logging.getLogger(__name__)

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = URL.create(
            "mssql+pymssql",
            username=config.MSSQL_USER,
            password=config.MSSQL_PASSWORD,
            host=config.MSSQL_HOST,
            port=config.MSSQL_PORT,
            database=config.MSSQL_DATABASE,
        )
        _engine = create_engine(url, pool_pre_ping=True)
        logger.info("DB engine created — %s:%s/%s", config.MSSQL_HOST, config.MSSQL_PORT, config.MSSQL_DATABASE)
    return _engine


def run_query(sql: str) -> list[dict]:
    engine = get_engine()
    sql_preview = sql.replace("\n", " ")[:120]
    logger.debug("Executing SQL: %s", sql_preview)
    t0 = time.perf_counter()
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("Query returned %d rows in %.1f ms", len(rows), elapsed)
    return rows
