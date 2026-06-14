from typing import TypedDict


class AgentState(TypedDict, total=False):
    question: str
    sql: str
    rows: list[dict]
    error: str
    answer: str
    attempts: int
