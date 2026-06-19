import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.graph import graph
from app.db import get_engine

app = FastAPI(title="DataResearchRAG", version="1.0")


# ── Request / Response models ─────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str
    session_id: str | None = None
    history: list[dict] = []


class AskResponse(BaseModel):
    answer: str
    sql: str
    table: list[dict]
    citation: dict
    session_id: str
    history: list[dict]


class FeedbackRequest(BaseModel):
    session_id: str
    turn_order: int
    rating: int  # 1 = thumbs up, -1 = thumbs down


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    session_id = req.session_id or str(uuid.uuid4())

    result = graph.invoke({
        "question": req.question,
        "attempts": 0,
        "rows": [],
        "error": "",
        "history": req.history,
        "session_id": session_id,
    })

    return AskResponse(
        answer=result.get("answer", ""),
        sql=result.get("sql", ""),
        table=result.get("rows", []),
        citation=result.get("citation") or {},
        session_id=session_id,
        history=result.get("history") or [],
    )


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    if req.rating not in (1, -1):
        raise HTTPException(status_code=422, detail="rating must be 1 (👍) or -1 (👎)")

    try:
        engine = get_engine()
        with engine.begin() as conn:
            rows_affected = conn.execute(
                text("""
                    UPDATE dbo.Conversations
                    SET Rating = :rating
                    WHERE SessionId = :session_id AND TurnOrder = :turn_order
                """),
                {"rating": req.rating, "session_id": req.session_id, "turn_order": req.turn_order},
            ).rowcount
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Turn not found")

    return {"status": "ok", "rating": req.rating}
