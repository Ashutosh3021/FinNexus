"""
FinNexus — FastAPI Backend
Exposes the FinnexusBot as a REST API.
All endpoints return JSON.  No auth middleware — add JWT/API-key layer on top.

All LLM, RAG, and ML logic goes through Bot/main.py ONLY.
No direct LLM or RAG calls from this file.

Run:
    uvicorn Backend.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from Bot.main import FinnexusBot
from Bot.llm_generator import MarketContext

logging.basicConfig(level="INFO", format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("finnexus.api")

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FinNexus HITL Bot API",
    description="Human-in-the-Loop financial training bot — question engine, scoring, rewards.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singleton bot ──────────────────────────────────────────────────────────────
bot: FinnexusBot = FinnexusBot.from_env()


# ── Request / Response schemas (Pydantic) ─────────────────────────────────────

class StartSessionRequest(BaseModel):
    user_id: int = Field(..., description="Unique user identifier")
    level: int = Field(1, ge=1, le=20, description="Level 1-5 or 20 for global events")
    asset_context: str = Field("", description="Optional asset context hint for LLM generation")
    force_new: bool = Field(False, description="Force a brand-new session even if one exists")
    # Market context fields (all optional — bot degrades gracefully without them)
    regime: str = Field("neutral", description="bull|bear|volatile|neutral")
    vix_level: float = Field(18.0, description="Current VIX level")
    dxy_trend: str = Field("flat", description="rising|falling|flat")
    news: List[str] = Field(default_factory=list, description="Recent news headlines")
    prices: Dict[str, float] = Field(default_factory=dict, description="Key price snapshots")
    trends: Dict[str, str] = Field(default_factory=dict, description="Trend context per symbol")
    user_portfolio: str = Field("", description="User's current portfolio description")
    user_history_summary: str = Field("", description="Summary of user's past performance")


class SubmitAnswerRequest(BaseModel):
    user_id: int
    answer: Any = Field(..., description="String for MCQ/SAQ, list[str] for MCQ_MULTIPLE")


class AssessRequest(BaseModel):
    user_id: int
    proficiency_score: float = Field(..., ge=0.0, le=1.0)


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check() -> Dict:
    """Liveness probe."""
    return {"status": "ok", "service": "finnexus-bot-api"}


@app.get("/health/ml", tags=["System"])
def ml_health() -> Dict:
    """Returns ML model stats."""
    return bot.get_ml_stats()


# ── Session endpoints ──────────────────────────────────────────────────────────

@app.post("/session/start", tags=["Session"])
def start_session(req: StartSessionRequest) -> Dict:
    """
    Start or resume a HITL session for a user at a specific level.
    Returns the session metadata and the first question.
    """
    try:
        ctx = MarketContext(
            regime=req.regime,
            vix_level=req.vix_level,
            dxy_trend=req.dxy_trend,
            news=req.news,
            prices=req.prices,
            trends=req.trends,
            user_level=req.level,
            user_portfolio=req.user_portfolio,
            user_history_summary=req.user_history_summary,
        )
        resp = bot.start_session(
            user_id=req.user_id,
            level=req.level,
            asset_context=req.asset_context,
            force_new=req.force_new,
            market_context=ctx,
        )
        return resp.to_dict()
    except Exception as exc:
        logger.error("start_session error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/session/question", tags=["Session"])
def get_current_question(user_id: int = Query(..., description="User ID")) -> Dict:
    """
    Return the current (unanswered) question for the user's active session.
    """
    q = bot.get_current_question(user_id)
    if q is None:
        raise HTTPException(status_code=404, detail="No active session or session complete.")
    return q


@app.post("/session/answer", tags=["Session"])
def submit_answer(req: SubmitAnswerRequest) -> Dict:
    """
    Submit an answer for the current question.
    Returns score, feedback, next question (if any), or level result if complete.
    """
    try:
        resp = bot.submit_answer(user_id=req.user_id, answer=req.answer)
        return resp.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("submit_answer error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── User endpoints ─────────────────────────────────────────────────────────────

@app.get("/user/{user_id}/stats", tags=["User"])
def get_user_stats(user_id: int) -> Dict:
    """
    Return aggregated performance stats for a user:
    levels completed, cash earned, accuracy, proficiency, recent activity.
    """
    try:
        stats = bot.get_user_stats(user_id)
        return stats.to_dict()
    except Exception as exc:
        logger.error("get_user_stats error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/user/{user_id}/cash", tags=["User"])
def get_paper_cash(user_id: int) -> Dict:
    """Return current paper cash balance for a user."""
    cash = bot._db.get_paper_cash(user_id)
    return {"user_id": user_id, "paper_cash": cash}


@app.get("/user/{user_id}/predict", tags=["User"])
def predict_improvement(user_id: int) -> Dict:
    """
    Use the ML model to predict how much this user's current session
    answers improve the prediction pipeline confidence.
    Requires an active session.
    """
    score = bot.predict_improvement(user_id)
    return {"user_id": user_id, "predicted_improvement": round(score, 4)}


# ── Onboarding ─────────────────────────────────────────────────────────────────

@app.post("/assess", tags=["Onboarding"])
def assess_starting_level(req: AssessRequest) -> Dict:
    """
    Map a user's proficiency quiz score (0-1) to a recommended starting level.
    Call this after an initial onboarding assessment quiz.
    """
    level = bot.assess_starting_level(req.proficiency_score)
    return {
        "user_id": req.user_id,
        "proficiency_score": req.proficiency_score,
        "recommended_level": level,
    }


# ── RAG / Context ──────────────────────────────────────────────────────────────

@app.get("/rag/stats", tags=["RAG"])
def rag_stats() -> Dict:
    """Return RAG retriever collection stats."""
    return bot._evaluator.retriever.stats()


@app.get("/rag/retrieve", tags=["RAG"])
def rag_retrieve(
    query: str = Query(..., description="Search query"),
    collection: str = Query("trading_theories", description="market_data|news_events|trading_theories"),
) -> Dict:
    """
    Retrieve top-3 context chunks for a query from the specified collection.
    Routes to the appropriate domain method on RAGRetriever.
    """
    try:
        retriever = bot._evaluator.retriever
        if collection == "market_data":
            result = retriever.get_market_context(query)
        elif collection == "news_events":
            result = retriever.get_news_context(query)
        else:
            result = retriever.get_theory_context(query)
        return {"query": query, "collection": collection, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── V2 async endpoints ─────────────────────────────────────────────────────────

class StartSessionV2Request(BaseModel):
    user_id: int = Field(..., description="Unique user identifier")
    level: int = Field(1, ge=1, le=20, description="Level 1-5 or 20 for global events")
    force_new: bool = Field(False, description="Force a brand-new session")


class SubmitAnswersV2Request(BaseModel):
    session_id: str = Field(..., description="Session ID from start_session_v2")
    answers: Dict[str, Any] = Field(
        ..., description="Map of question_id → answer value (index int for MCQ, str for SAQ)"
    )


@app.post("/v2/session/start", tags=["Session V2"])
async def start_session_v2(req: StartSessionV2Request) -> Dict:
    """
    Async session start. Returns session_id + all 19 questions.
    Context and question generation happen via the full RAG pipeline.
    """
    try:
        session_id, questions = await bot.async_start_session(
            user_id=req.user_id,
            level=req.level,
            force_new=req.force_new,
        )
        return {
            "session_id": session_id,
            "level": req.level,
            "total_questions": len(questions),
            "questions": questions,
        }
    except Exception as exc:
        logger.error("start_session_v2 error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/v2/session/answers", tags=["Session V2"])
async def submit_answers_v2(req: SubmitAnswersV2Request) -> Dict:
    """
    Submit all (or partial) answers for a session.
    When all 19 answers are received, runs Steps 3-5:
      - RAG-based scoring (evaluate_answers)
      - HITL feature extraction
      - DB + ML update
    Returns score, reward, level_result, and hitl_features.
    """
    try:
        result = await bot.async_submit_answers(
            session_id=req.session_id,
            answers=req.answers,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("submit_answers_v2 error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Entry point (dev) ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Backend.main:app", host="0.0.0.0", port=8000, reload=True)
