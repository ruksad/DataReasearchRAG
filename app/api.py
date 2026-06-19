import logging
import time
import uuid

# setup_logging must run before any other app import — module-level code in
# synthesize.py calls get_llm() and vanna_setup.py calls get_vanna() at import
# time, so the handler must exist before those modules are loaded.
from app import config
from app.logging_config import setup_logging
setup_logging(config.LOG_LEVEL)

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text

from app.graph import graph
from app.db import get_engine

logger = logging.getLogger(__name__)

app = FastAPI(title="DataResearchRAG", version="1.0")


# ── Request timing middleware ─────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("%s %s → %d  (%.1f ms)", request.method, request.url.path, response.status_code, elapsed)
    return response


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
    logger.info("ask — session=%s | question: %s", session_id[:8], req.question[:100])

    t0 = time.perf_counter()
    result = graph.invoke({
        "question": req.question,
        "attempts": 0,
        "rows": [],
        "error": "",
        "history": req.history,
        "session_id": session_id,
    })
    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("ask — done in %.1f ms | rows=%d | session=%s",
                elapsed, len(result.get("rows") or []), session_id[:8])

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
        logger.error("feedback — DB error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    if rows_affected == 0:
        raise HTTPException(status_code=404, detail="Turn not found")

    logger.info("feedback — session=%s turn=%d rating=%+d",
                req.session_id[:8], req.turn_order, req.rating)
    return {"status": "ok", "rating": req.rating}
