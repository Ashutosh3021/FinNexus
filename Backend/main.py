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
import sys
import time
import glob
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from Bot.main import FinnexusBot
from Bot.llm_generator import MarketContext
import Bot.config as cfg

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
# FIX #1 — JWT secret: no hardcoded fallback. Server refuses to start without a
#           real secret in production (ENV=production).
_JWT_SECRET = os.getenv("JWT_SECRET", "")
_JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
_JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours
_API_KEY = os.getenv("FINNEXUS_API_KEY", "")  # optional external service API key

_ENV = os.getenv("ENV", "development").lower()  # "production" | "development"

# FIX #1 — Enforce non-default secret in production at startup.
_INSECURE_SECRETS = {
    "", "finnexus-dev-secret-change-in-production",
    "change-this-to-a-secure-random-string-in-production",
    "secret", "changeme",
}
if _ENV == "production" and _JWT_SECRET in _INSECURE_SECRETS:
    logger.critical(
        "STARTUP ABORTED: JWT_SECRET is missing or insecure in production. "
        "Set a strong random JWT_SECRET in your environment."
    )
    sys.exit(1)

# Use a dev-only fallback so the server still starts in development without .env
if not _JWT_SECRET:
    _JWT_SECRET = "finnexus-dev-only-do-not-use-in-production"
    logger.warning(
        "JWT_SECRET not set — using insecure dev default. "
        "Set JWT_SECRET in your .env before deploying."
    )

# FIX #3 — CORS: in production, CORS_ORIGINS MUST be set and must not contain
#           localhost. The server refuses to start if this rule is violated.
_ALLOWED_ORIGINS = [
    o.strip() for o in
    os.getenv("CORS_ORIGINS", "").split(",")
    if o.strip()
]

_LOCALHOST_ORIGINS = {"localhost", "127.0.0.1", "0.0.0.0"}

if _ENV == "production":
    _cors_has_localhost = any(
        any(loc in origin for loc in _LOCALHOST_ORIGINS)
        for origin in _ALLOWED_ORIGINS
    )
    if not _ALLOWED_ORIGINS:
        logger.critical(
            "STARTUP ABORTED: CORS_ORIGINS is not set in production. "
            "Set CORS_ORIGINS to your frontend domain(s)."
        )
        sys.exit(1)
    if _cors_has_localhost:
        logger.critical(
            "STARTUP ABORTED: CORS_ORIGINS contains a localhost origin in production: %s. "
            "Remove localhost entries before deploying.",
            _ALLOWED_ORIGINS,
        )
        sys.exit(1)

# Development fallback — allow localhost so local dev works without a .env
if not _ALLOWED_ORIGINS:
    _ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    logger.warning(
        "CORS_ORIGINS not set — defaulting to localhost dev origins. "
        "Set CORS_ORIGINS in production."
    )

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

# FIX #2 — Rate limiting decorators applied to all public + session endpoints.
# slowapi requires the decorated function to accept `request: Request` as a
# parameter. The `limiter.limit()` decorator is only applied when slowapi is
# available; otherwise the route registers normally with no rate limiting
# (a warning was already emitted at startup).

def _rate_limit(rate: str):
    """Return slowapi limit decorator if available, else a no-op pass-through."""
    if _SLOWAPI_OK and limiter:
        return limiter.limit(rate)
    return lambda f: f


@app.post("/auth/token", tags=["Auth"])
@_rate_limit("20/minute")
def login(request: Request, req: LoginRequest) -> LoginResponse:
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
@_rate_limit("60/minute")
def health_check(request: Request) -> Dict:
    """
    FIX #9 — Real liveness + readiness probe.
    Checks DB connectivity, ChromaDB (RAG), ML model, and LLM availability.
    No auth required.
    """
    checks: Dict[str, Any] = {}

    # DB
    try:
        _ = bot._db.get_paper_cash(0)
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {exc}"

    # RAG / ChromaDB
    try:
        rag_stats = bot._evaluator.retriever.stats()
        counts = rag_stats.get("collection_counts", {})
        checks["rag"] = {
            "chroma_available": rag_stats.get("chroma_available", False),
            "collection_counts": counts,
        }
    except Exception as exc:
        checks["rag"] = f"error: {exc}"

    # ML model
    try:
        ml_stats = bot.get_ml_stats()
        checks["ml"] = {
            "model_available": ml_stats.get("model_available", False),
            "n_trained": ml_stats.get("n_trained", 0),
        }
    except Exception as exc:
        checks["ml"] = f"error: {exc}"

    # LLM
    checks["llm"] = {
        "provider": cfg.LLM_PROVIDER,
        "available": bot._qgen.llm.available if bot._qgen.llm else False,
    }

    # Overall status — "degraded" if any non-critical subsystem is unhealthy
    db_ok = checks["db"] == "ok"
    overall = "ok" if db_ok else "degraded"

    return {
        "status": overall,
        "service": "finnexus-bot-api",
        "env": _ENV,
        "subsystems": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ml", tags=["System"])
def ml_health(_: Dict = Depends(get_current_user)) -> Dict:
    """Returns ML model stats. Requires auth."""
    return bot.get_ml_stats()


# ── Session endpoints (protected) ─────────────────────────────────────────────

@app.post("/session/start", tags=["Session"])
@_rate_limit("100/minute")
def start_session(
    request: Request,
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
@_rate_limit("100/minute")
def get_current_question(
    request: Request,
    user_id: int = Query(..., description="User ID"),
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Return the current unanswered question for the user's active session."""
    q = bot.get_current_question(user_id)
    if q is None:
        raise HTTPException(status_code=404, detail="No active session or session complete.")
    return q


@app.post("/session/answer", tags=["Session"])
@_rate_limit("100/minute")
def submit_answer(
    request: Request,
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
@_rate_limit("100/minute")
async def start_session_v2(
    request: Request,
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
@_rate_limit("100/minute")
async def submit_answers_v2(
    request: Request,
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


# ── Market Data endpoints (public — no auth required) ──────────────────────────
# Reads from Data/Cleaned CSVs so the frontend gets real historical price data.
# Falls back gracefully to empty lists when CSV files are missing.

_DATA_ROOT = cfg.PROJECT_ROOT / "Data" / "Cleaned"

# ── Asset catalogue ─────────────────────────────────────────────────────────────
# Maps each frontend asset id → (csv_relative_path, display_name, asset_class)
_ASSET_CATALOGUE: Dict[str, Dict[str, str]] = {
    # Crypto
    "btc":       {"csv": "Crypto/BTC_cleaned.csv",               "name": "Bitcoin",                  "class": "Crypto",      "symbol": "BTC"},
    "eth":       {"csv": "Crypto/ETH_cleaned.csv",               "name": "Ethereum",                 "class": "Crypto",      "symbol": "ETH"},
    "sol":       {"csv": "Crypto/SOL_cleaned.csv",               "name": "Solana",                   "class": "Crypto",      "symbol": "SOL"},
    "bnb":       {"csv": "Crypto/BNB_cleaned.csv",               "name": "BNB",                      "class": "Crypto",      "symbol": "BNB"},
    "ltc":       {"csv": "Crypto/LTC_cleaned.csv",               "name": "Litecoin",                 "class": "Crypto",      "symbol": "LTC"},
    "trx":       {"csv": "Crypto/TRX_cleaned.csv",               "name": "TRON",                     "class": "Crypto",      "symbol": "TRX"},
    "xmr":       {"csv": "Crypto/XMR_cleaned.csv",               "name": "Monero",                   "class": "Crypto",      "symbol": "XMR"},
    # Commodities
    "gold":      {"csv": "Commodities/Gold_cleaned.csv",         "name": "Gold",                     "class": "Commodities", "symbol": "GOLD"},
    "silver":    {"csv": "Commodities/Silver_cleaned.csv",       "name": "Silver",                   "class": "Commodities", "symbol": "SILVER"},
    "crude":     {"csv": "Commodities/Brent_Crude_Oil_cleaned.csv", "name": "Brent Crude Oil",       "class": "Commodities", "symbol": "CRUDE"},
    "wti":       {"csv": "Commodities/WTI_Crude_Oil_cleaned.csv","name": "WTI Crude Oil",            "class": "Commodities", "symbol": "WTI"},
    "natgas":    {"csv": "Commodities/Natural_Gas_cleaned.csv",  "name": "Natural Gas",              "class": "Commodities", "symbol": "NATGAS"},
    "copper":    {"csv": "Commodities/Copper_cleaned.csv",       "name": "Copper",                   "class": "Commodities", "symbol": "COPPER"},
    "aluminum":  {"csv": "Commodities/Aluminum_cleaned.csv",     "name": "Aluminum",                 "class": "Commodities", "symbol": "ALU"},
    "wheat":     {"csv": "Commodities/Wheat_cleaned.csv",        "name": "Wheat",                    "class": "Commodities", "symbol": "WHEAT"},
    "corn":      {"csv": "Commodities/Corn_cleaned.csv",         "name": "Corn",                     "class": "Commodities", "symbol": "CORN"},
}


def _read_csv_tail(csv_path: Path, rows: int = 30) -> List[Dict]:
    """Read last `rows` rows from a cleaned CSV. Returns list of dicts."""
    try:
        import pandas as pd  # type: ignore
        df = pd.read_csv(csv_path)
        # Only keep clean data
        if "data_quality" in df.columns:
            df = df[df["data_quality"] == 1]
        df = df.dropna(subset=["Close"]).tail(rows)
        return df.to_dict(orient="records")
    except Exception as exc:
        logger.debug("_read_csv_tail failed for %s: %s", csv_path, exc)
        return []


def _compute_trend(rows: List[Dict]) -> str:
    """Classify last-N-row price movement as Bullish / Bearish / Neutral."""
    if len(rows) < 2:
        return "Neutral"
    closes = [float(r.get("Close", r.get("close", 0)) or 0) for r in rows if r.get("Close") or r.get("close")]
    if len(closes) < 2:
        return "Neutral"
    change = (closes[-1] - closes[0]) / closes[0] if closes[0] else 0
    if change > 0.01:
        return "Bullish"
    if change < -0.01:
        return "Bearish"
    return "Neutral"


def _build_price_entry(asset_id: str, meta: Dict, rows: List[Dict]) -> Optional[Dict]:
    """Build a price dict from CSV rows for one asset."""
    if not rows:
        return None
    last  = rows[-1]
    close = float(last.get("Close", last.get("close", 0)) or 0)
    if close <= 0:
        return None

    prev_close = float(rows[-2].get("Close", rows[-2].get("close", close)) or close) if len(rows) > 1 else close
    change_pct = ((close - prev_close) / prev_close * 100) if prev_close else 0.0

    volume_raw = last.get("Volume", last.get("volume", 0)) or 0
    try:
        volume_val = float(volume_raw)
        volume_str = (f"${volume_val / 1e9:.1f}B" if volume_val > 1e9
                      else f"${volume_val / 1e6:.0f}M" if volume_val > 1e6
                      else str(volume_val))
    except (ValueError, TypeError):
        volume_str = str(volume_raw)

    date_raw = last.get("Date", last.get("date", ""))
    try:
        last_updated = str(datetime.strptime(str(date_raw).split(" ")[0], "%Y-%m-%d").date())
    except ValueError:
        last_updated = str(date_raw)

    trend = _compute_trend(rows[-7:])

    return {
        "id":           asset_id,
        "symbol":       meta["symbol"],
        "name":         meta["name"],
        "price":        round(close, 2),
        "change_percent": round(change_pct, 2),
        "volume":       volume_str,
        "last_updated": last_updated,
        "trend":        trend,
        "asset_class":  meta["class"],
    }


@app.get("/market/prices", tags=["Market"])
@_rate_limit("60/minute")
def market_prices(request: Request) -> Dict:
    """
    Return the latest price snapshot for all tracked assets.
    Reads from Data/Cleaned CSVs — no auth required.
    """
    result = []
    for asset_id, meta in _ASSET_CATALOGUE.items():
        csv_path = _DATA_ROOT / meta["csv"]
        rows = _read_csv_tail(csv_path, rows=8)
        entry = _build_price_entry(asset_id, meta, rows)
        if entry:
            result.append(entry)
    return {"prices": result, "count": len(result), "updated_at": datetime.now(timezone.utc).isoformat()}


@app.get("/market/trends", tags=["Market"])
@_rate_limit("60/minute")
def market_trends(
    request: Request,
    timeframe: str = Query("1D", description="1D | 1W | 1M"),
    asset_class: Optional[str] = Query(None, description="Filter by asset class"),
) -> Dict:
    """
    Return trend signals per timeframe for all (or filtered) assets.
    Trend is computed from CSV history over the appropriate lookback window.
    """
    lookback = {"1D": 2, "1W": 7, "1M": 30}.get(timeframe, 2)
    result = []

    for asset_id, meta in _ASSET_CATALOGUE.items():
        if asset_class and asset_class.lower() not in meta["class"].lower():
            continue
        csv_path = _DATA_ROOT / meta["csv"]
        rows_1d  = _read_csv_tail(csv_path, rows=2)
        rows_1w  = _read_csv_tail(csv_path, rows=7)
        rows_1m  = _read_csv_tail(csv_path, rows=30)
        if not rows_1d:
            continue
        result.append({
            "id":         asset_id,
            "symbol":     meta["symbol"],
            "name":       meta["name"],
            "asset_class": meta["class"],
            "trend_1d":   _compute_trend(rows_1d),
            "trend_1w":   _compute_trend(rows_1w),
            "trend_1m":   _compute_trend(rows_1m),
        })

    return {"trends": result, "timeframe": timeframe, "count": len(result)}


# ── News endpoint ──────────────────────────────────────────────────────────────
# Fetches from NewsAPI if NEWSAPI_KEY is configured, otherwise returns curated
# static headlines derived from the RAG news_events collection.

@app.get("/market/news", tags=["Market"])
@_rate_limit("60/minute")
def market_news(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    filter: Optional[str] = Query(None, description="Asset class filter"),
) -> Dict:
    """
    Return market-moving news.
    Uses NewsAPI (if key is set) or falls back to RAG news context.
    No auth required.
    """
    newsapi_key = os.getenv("NEWSAPI_KEY", "").strip()
    news_items: List[Dict] = []

    # ── Live NewsAPI ────────────────────────────────────────────────────────────
    if newsapi_key:
        try:
            import requests as _requests  # type: ignore
            queries = ["stock market", "cryptocurrency", "commodities", "federal reserve", "india nifty"]
            seen_titles: set = set()
            for q in queries:
                if len(news_items) >= limit:
                    break
                resp = _requests.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q":        q,
                        "apiKey":   newsapi_key,
                        "language": "en",
                        "sortBy":   "publishedAt",
                        "pageSize": 5,
                    },
                    timeout=5,
                )
                if resp.status_code != 200:
                    continue
                for article in resp.json().get("articles", []):
                    title = article.get("title", "") or ""
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)
                    # Derive sentiment & impact heuristically
                    lower_title = title.lower()
                    positive_words = {"rise", "surge", "gain", "high", "beat", "record", "rally", "up", "positive", "buy"}
                    negative_words = {"fall", "drop", "loss", "low", "miss", "crash", "sell", "cut", "down", "negative", "warn"}
                    pos_hits = sum(1 for w in positive_words if w in lower_title)
                    neg_hits = sum(1 for w in negative_words if w in lower_title)
                    sentiment = "positive" if pos_hits > neg_hits else "negative" if neg_hits > pos_hits else "neutral"
                    impact = "high" if any(w in lower_title for w in {"federal", "rate", "war", "crash", "ban"}) else "medium"

                    # Determine affected classes
                    affected_classes: List[str] = []
                    if any(w in lower_title for w in {"bitcoin", "crypto", "eth", "btc", "solana"}):
                        affected_classes.append("Crypto")
                    if any(w in lower_title for w in {"stock", "nifty", "sensex", "equity", "share", "nasdaq", "s&p"}):
                        affected_classes.append("Stocks")
                    if any(w in lower_title for w in {"gold", "silver", "oil", "crude", "wheat", "commodity"}):
                        affected_classes.append("Commodities")
                    if any(w in lower_title for w in {"etf", "fund", "index"}):
                        affected_classes.append("ETFs")
                    if not affected_classes:
                        affected_classes = ["Stocks"]

                    published = article.get("publishedAt", datetime.now(timezone.utc).isoformat())

                    news_items.append({
                        "id":              f"news-{len(news_items)}",
                        "title":           title,
                        "summary":         article.get("description") or article.get("content") or title,
                        "source":          (article.get("source") or {}).get("name", "Unknown"),
                        "url":             article.get("url", "#"),
                        "published_at":    published,
                        "sentiment":       sentiment,
                        "affected_assets": [],
                        "affected_classes": affected_classes,
                        "impact":          impact,
                    })
        except Exception as exc:
            logger.warning("NewsAPI fetch failed: %s — using RAG fallback", exc)

    # ── RAG fallback — retrieve top news context chunks ─────────────────────────
    if not news_items:
        try:
            retriever = bot._evaluator.retriever
            ctx = retriever.get_news_context("market moving financial news")
            chunks = ctx.get("results", []) if isinstance(ctx, dict) else []
            for i, chunk in enumerate(chunks[:limit]):
                text = chunk.get("document", "") if isinstance(chunk, dict) else str(chunk)
                if not text:
                    continue
                news_items.append({
                    "id":              f"rag-news-{i}",
                    "title":           text[:100].strip(),
                    "summary":         text[:300].strip(),
                    "source":          "FinNexus RAG",
                    "url":             "#",
                    "published_at":    datetime.now(timezone.utc).isoformat(),
                    "sentiment":       "neutral",
                    "affected_assets": [],
                    "affected_classes": ["Stocks", "Crypto"],
                    "impact":          "medium",
                })
        except Exception as exc:
            logger.warning("RAG news fallback also failed: %s", exc)

    # Apply class filter if requested
    if filter and filter != "All":
        news_items = [n for n in news_items if filter in n.get("affected_classes", [])]

    return {"news": news_items[:limit], "count": len(news_items[:limit])}


# ── User profile endpoint (onboarding) ────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    user_id: int
    name:           Optional[str]  = None
    email:          Optional[str]  = None
    current_level:  Optional[int]  = None
    tracked_assets: Optional[List[str]] = None
    experience:     Optional[str]  = None


@app.post("/user/profile", tags=["User"])
def update_user_profile(
    req: UpdateProfileRequest,
    _user: Dict = Depends(get_current_user),
) -> Dict:
    """Update user profile fields after onboarding."""
    try:
        updates: Dict[str, Any] = {}
        if req.name          is not None: updates["name"]          = req.name
        if req.email         is not None: updates["email"]         = req.email
        if req.current_level is not None: updates["current_level"] = req.current_level
        result = bot.update_user_profile(req.user_id, **updates)
        return result
    except Exception as exc:
        logger.error("update_user_profile error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── Entry point (dev) ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Backend.main:app", host="0.0.0.0", port=8000, reload=True)
