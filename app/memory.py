from sqlalchemy import text
from app.db import get_engine


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
    except Exception as exc:
        print(f"[memory] Failed to persist turn: {exc}")
