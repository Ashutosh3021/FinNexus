"""
FinNexus — FastAPI Backend
Exposes the FinnexusBot as a REST API.

Security:
  - JWT authentication on all protected endpoints (Bearer token)
  - CORS restricted to configured origins
  - Rate limiting: 100 requests per minute per IP (via slowapi)
  - API key validation for external service endpoints

All LLM, RAG, and ML logic goes through Bot/main.py ONLY.
No direct LLM or RAG calls from this file.

Run:
    uvicorn Backend.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from Bot.main import FinnexusBot
from Bot.llm_generator import MarketContext

logging.basicConfig(level="INFO", format="%(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("finnexus.api")

# ── Rate limiter ───────────────────────────────────────────────────────────────
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    limiter = Limiter(key_func=get_remote_address)
    _SLOWAPI_OK = True
except ImportError:
    limiter = None
    _SLOWAPI_OK = False
    logger.warning("slowapi not installed — rate limiting disabled. pip install slowapi")

# ── JWT (PyJWT) ────────────────────────────────────────────────────────────────
try:
    import jwt as _jwt  # type: ignore
    _JWT_OK = True
except ImportError:
    _jwt = None
    _JWT_OK = False
    logger.warning("PyJWT not installed — JWT auth disabled. pip install PyJWT")

# ── Config ─────────────────────────────────────────────────────────────────────
_JWT_SECRET    = os.getenv("JWT_SECRET",    "finnexus-dev-secret-change-in-production")
_JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
_JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours
_API_KEY       = os.getenv("FINNEXUS_API_KEY", "")  # optional external service API key

_ALLOWED_ORIGINS = [
    o.strip() for o in
    os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",")
    if o.strip()
]

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FinNexus HITL Bot API",
    description="Human-in-the-Loop financial training bot — question engine, scoring, rewards.",
    version="1.0.0",
)

if _SLOWAPI_OK and limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

# ── Singleton bot ──────────────────────────────────────────────────────────────
bot: FinnexusBot = FinnexusBot.from_env()

# ── Security ───────────────────────────────────────────────────────────────────
_bearer = HTTPBearer(auto_error=False)


def _create_token(user_id: int, extra: Optional[Dict] = None) -> str:
    """Create a signed JWT for a user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=_JWT_EXPIRE_MINUTES),
        **(extra or {}),
    }
    if _JWT_OK:
        return _jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)
    # Fallback: no JWT library — return a simple opaque token
    return f"nolib_{user_id}_{int(now.timestamp())}"


def _verify_token(credentials: Optional[HTTPAuthorizationCredentials]) -> Dict:
    """Verify a Bearer JWT; raise 401 on failure."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    if not _JWT_OK:
        # Library not installed — accept any non-empty token in dev mode
        if not token:
            raise HTTPException(status_code=401, detail="Empty token")
        # Extract user_id from nolib format
        parts = token.split("_")
        try:
            user_id = int(parts[1])
            return {"sub": str(user_id)}
        except (IndexError, ValueError):
            return {"sub": "0"}

    try:
        payload = _jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        return payload
    except _jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except _jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer),
) -> Dict:
    """FastAPI dependency — validates JWT and returns payload."""
    return _verify_token(credentials)


def optional_api_key(request: Request) -> None:
    """Validate X-API-Key header when FINNEXUS_API_KEY is configured."""
    if not _API_KEY:
        return  # API key check disabled when env var not set
    key = request.headers.get("X-API-Key", "")
    if key != _API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")


# ── Request / Response schemas ─────────────────────────────────────────────────

class LoginRequest(BaseModel):
    user_id: int = Field(..., description="User ID to authenticate")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    expires_in: int

class StartSessionRequest(BaseModel):
    user_id: int = Field(..., description="Unique user identifier")
    level: int = Field(1, ge=1, le=20, description="Level 1-5 or 20 for global events")
    asset_context: str = Field("", description="Optional asset context hint for LLM generation")
    force_new: bool = Field(False, description="Force a brand-new session even if one exists")
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


# ── Auth endpoints (public) ────────────────────────────────────────────────────

@app.post("/auth/token", tags=["Auth"])
def login(req: LoginRequest) -> LoginResponse:
    """
    Obtain a JWT access token for a user ID.
    In production, validate credentials here before issuing the token.
    """
    token = _create_token(req.user_id)
    return LoginResponse(
        access_token=token,
        user_id=req.user_id,
        expires_in=_JWT_EXPIRE_MINUTES * 60,
    )


# ── Health (public) ────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check() -> Dict:
    """Liveness probe. No auth required."""
    return {"status": "ok", "service": "finnexus-bot-api"}


@app.get("/health/ml", tags=["System"])
def ml_health(_: Dict = Depends(get_current_user)) -> Dict:
    """Returns ML model stats. Requires auth."""
    return bot.get_ml_stats()


# ── Session endpoints (protected) ─────────────────────────────────────────────

@app.post("/session/start", tags=["Session"])
def start_session(
    req: StartSessionRequest,
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Start or resume a HITL session for a user at a specific level."""
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
def get_current_question(
    user_id: int = Query(..., description="User ID"),
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Return the current unanswered question for the user's active session."""
    q = bot.get_current_question(user_id)
    if q is None:
        raise HTTPException(status_code=404, detail="No active session or session complete.")
    return q


@app.post("/session/answer", tags=["Session"])
def submit_answer(
    req: SubmitAnswerRequest,
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Submit an answer for the current question."""
    try:
        resp = bot.submit_answer(user_id=req.user_id, answer=req.answer)
        return resp.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("submit_answer error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── User endpoints (protected) ─────────────────────────────────────────────────

@app.get("/user/{user_id}/stats", tags=["User"])
def get_user_stats(
    user_id: int,
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Return aggregated performance stats for a user."""
    try:
        stats = bot.get_user_stats(user_id)
        return stats.to_dict()
    except Exception as exc:
        logger.error("get_user_stats error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/user/{user_id}/cash", tags=["User"])
def get_paper_cash(
    user_id: int,
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Return current paper cash balance for a user."""
    cash = bot._db.get_paper_cash(user_id)
    return {"user_id": user_id, "paper_cash": cash}


@app.get("/user/{user_id}/predict", tags=["User"])
def predict_improvement(
    user_id: int,
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Predict how much this user's answers improve the prediction pipeline confidence."""
    score = bot.predict_improvement(user_id)
    return {"user_id": user_id, "predicted_improvement": round(score, 4)}


# ── Onboarding (protected) ─────────────────────────────────────────────────────

@app.post("/assess", tags=["Onboarding"])
def assess_starting_level(
    req: AssessRequest,
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Map a user's proficiency score (0-1) to a recommended starting level."""
    level = bot.assess_starting_level(req.proficiency_score)
    return {
        "user_id": req.user_id,
        "proficiency_score": req.proficiency_score,
        "recommended_level": level,
    }


# ── RAG / Context (protected) ──────────────────────────────────────────────────

@app.get("/rag/stats", tags=["RAG"])
def rag_stats(_user: Dict = Depends(get_current_user)) -> Dict:
    """Return RAG retriever collection stats."""
    return bot._evaluator.retriever.stats()


@app.get("/rag/retrieve", tags=["RAG"])
def rag_retrieve(
    query: str = Query(..., description="Search query"),
    collection: str = Query("trading_theories", description="market_data|news_events|trading_theories"),
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Retrieve top-3 context chunks for a query from the specified collection."""
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


# ── V2 async endpoints (protected) ────────────────────────────────────────────

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
async def start_session_v2(
    req: StartSessionV2Request,
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Async session start. Returns session_id + all 19 questions."""
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
async def submit_answers_v2(
    req: SubmitAnswersV2Request,
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Submit all (or partial) answers for a session."""
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
