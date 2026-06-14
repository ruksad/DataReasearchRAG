from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from app import config

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
    return _engine


def run_query(sql: str) -> list[dict]:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in result.fetchall()]
