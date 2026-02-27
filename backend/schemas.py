"""
Pydantic schemas for request/response validation.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== GENERIC RESPONSE ====================

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ==================== AUTH SCHEMAS ====================

class LoginRequest(BaseModel):
    """Login request payload."""
    email: str
    password: str


class RegisterRequest(BaseModel):
    """Registration request payload."""
    name: str
    email: str
    password: str
    level: str = "BEGINNER"


class UpdateLevelRequest(BaseModel):
    """Update user level request."""
    level: str = Field(..., pattern="^(BEGINNER|INTERMEDIATE|ADVANCED)$")


class UserResponse(BaseModel):
    """User data response."""
    id: str
    name: str
    email: str
    level: str
    virtual_balance: float
    xp: int
    avatar: Optional[str] = None
    join_date: Optional[str] = None


# ==================== EDUCATION SCHEMAS ====================

class AskQuestionRequest(BaseModel):
    """Ask educational question."""
    question: str
    user_level: str = "BEGINNER"


class LessonSearchRequest(BaseModel):
    """Search lessons."""
    query: str
    level: Optional[str] = None


# ==================== PLAYGROUND SCHEMAS ====================

class OHLCVData(BaseModel):
    """OHLCV candle data."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class PredictRequest(BaseModel):
    """Prediction request."""
    symbol: str
    ohlcv_data: List[OHLCVData]


class BattleRequest(BaseModel):
    """Battle prediction request."""
    symbol: str
    user_prediction: str = Field(..., pattern="^(up|down)$")
    ohlcv_data: List[OHLCVData]


class PredictionResponse(BaseModel):
    """Prediction result."""
    direction: str
    confidence: float
    prob_up: float
    prob_down: float


class BattleResponse(BaseModel):
    """Battle result."""
    result: str
    actual_direction: str
    pnl: float
    ml_prediction: str
    explanation: str


# ==================== NEWS SCHEMAS ====================

class AnalyzeHeadlineRequest(BaseModel):
    """Analyze news headline."""
    headline: str


class NewsItemResponse(BaseModel):
    """News item."""
    id: str
    headline: str
    category: str
    sentiment: str
    impact_score: int
    affected_assets: List[str]
    summary: str
    gemini_analysis: str
    date: str
    source: str


class SentimentResponse(BaseModel):
    """Sentiment analysis result."""
    sentiment: str
    confidence: float
    impact_score: int
    gemini_analysis: Optional[str] = None


# ==================== PORTFOLIO SCHEMAS ====================

class HoldingInput(BaseModel):
    """Portfolio holding input."""
    asset: str
    symbol: str
    qty: float
    buy_price: float
    current_price: float


class PortfolioAnalyzeRequest(BaseModel):
    """Analyze portfolio request."""
    holdings: List[HoldingInput]


class RebalanceRequest(BaseModel):
    """Rebalance request."""
    current_allocations: Dict[str, float]


class RiskResponse(BaseModel):
    """Risk analysis result."""
    risk_label: str
    score: int
    volatility: float
    expected_return: float
    sharpe_ratio: float


class PortfolioTypeResponse(BaseModel):
    """Portfolio type classification."""
    portfolio_type: str
    suggestions: List[str]


# ==================== ADVISOR SCHEMAS ====================

class ChatMessage(BaseModel):
    """Chat message."""
    role: str
    content: str


class AdvisorChatRequest(BaseModel):
    """Advisor chat request."""
    message: str
    conversation_history: List[ChatMessage] = []
    user_portfolio: Optional[Dict[str, float]] = None
    user_level: str = "BEGINNER"


class AdvisorAction(BaseModel):
    """Action suggested by advisor."""
    type: str
    payload: Any


class AdvisorResponse(BaseModel):
    """Advisor chat response."""
    response: str
    suggestions: List[str]
    actions: List[AdvisorAction] = []
    followup_questions: List[str] = []


# ==================== MACRO SCHEMAS ====================

class MacroDataResponse(BaseModel):
    """Macro economic data."""
    inflation: float
    inflation_trend: str
    gdp: float
    gdp_trend: str
    interest_rate: float
    interest_rate_trend: str
    unemployment: float
    unemployment_trend: str
    last_updated: str
