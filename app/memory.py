import logging

from sqlalchemy import text
from app.db import get_engine

logger = logging.getLogger(__name__)


def persist_turn(
    session_id: str,
    turn_order: int,
    question: str,
    sql: str,
    answer: str,
    row_count: int,
) -> None:
    """Write a completed conversation turn to dbo.Conversations.
    Failures are swallowed so a DB write error never breaks the agent response.
    """
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO dbo.Conversations
                        (SessionId, TurnOrder, Question, SqlQuery, Answer, [RowCount])
                    VALUES
                        (:session_id, :turn_order, :question, :sql, :answer, :row_count)
                """),
                {
                    "session_id": session_id,
                    "turn_order": turn_order,
                    "question": question,
                    "sql": sql,
                    "answer": answer,
                    "row_count": row_count,
                },
            )
        logger.debug("memory — persisted turn %d for session %s", turn_order, session_id[:8])
    except Exception as exc:
        logger.warning("memory — failed to persist turn: %s", exc)
