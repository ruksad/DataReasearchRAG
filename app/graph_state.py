from typing import TypedDict


class AgentState(TypedDict, total=False):
    question: str
    sql: str
    rows: list[dict]
    error: str
    answer: str
    attempts: int
    history: list[dict]   # [{question, sql, answer}, ...] capped at MAX_HISTORY_TURNS
    session_id: str       # UUID generated once per CLI session; used to group turns in dbo.Conversations
    citation: dict        # {sql, columns, row_count, sample_rows, executed_at, source}
