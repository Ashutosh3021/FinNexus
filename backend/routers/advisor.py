"""
AI Advisor router for FinNexus.
Provides conversational AI assistance with full market/portfolio/learning context.
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import gemini_service, market_service, news_service
from backend.schemas import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/advisor", tags=["advisor"])

# ═══════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════

class AdvisorChatRequest(BaseModel):
    """Request for advisor chat endpoint."""
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    user_context: Dict[str, Any] = {
        "level": "intermediate",
        "virtual_balance": 100000.0,
        "portfolio": [],
        "prediction_history": [],
        "learning_progress": {}
    }

class ContextSummaryResponse(BaseModel):
    """Context summary for advisor sidebar."""
    portfolio_summary: Dict[str, Any]
    prediction_stats: Dict[str, Any]
    news_headlines: List[Dict[str, Any]]
    learning_progress: Dict[str, Any]

# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _build_portfolio_summary(portfolio: List) -> Dict[str, Any]:
    """Build human-readable portfolio summary for Gemini."""
    # Normalize input to list of holdings
    if not portfolio or isinstance(portfolio, dict):
        return {"summary": "No portfolio data", "holdings_count": 0}
    
    summary_text = f"You hold {len(portfolio)} positions:\n"
    total_value = 0
    
    for holding in portfolio[:10]:  # Max 10 for context
        symbol = holding.get("symbol", "UNKNOWN")
        quantity = holding.get("quantity", 0)
        price = holding.get("current_price", 0)
        pnl = holding.get("pnl", 0)
        value = quantity * price if price else 0
        total_value += value
        
        pnl_indicator = "📈" if pnl >= 0 else "📉"
        summary_text += f"• {symbol}: {quantity} units @ ₹{price:.2f} | {pnl_indicator} {pnl:+.1f}%\n"
    
    return {
        "summary": summary_text,
        "holdings_count": len(portfolio),
        "total_value": total_value,
        "currency": "INR"
    }

def _build_prediction_stats(history: List) -> Dict[str, Any]:
    """Calculate prediction stats from history."""
    if not history:
        return {
            "win_rate": 0,
            "current_streak": 0,
            "total_rounds": 0,
            "recent_results": []
        }
    # Accept list of dicts or list of strings
    normalized = []
    for h in history:
        if isinstance(h, dict):
            normalized.append(h.get("result", "unknown"))
        elif isinstance(h, str):
            normalized.append(h)
    if not normalized:
        normalized = []
    wins = sum(1 for r in normalized if r == "win")
    total = len(history)
    win_rate = (wins / total * 100) if total > 0 else 0
    
    # Calculate streak (consecutive wins/losses)
    streak = 0
    streak_type = None
    for r in reversed(normalized[-10:]):
        result = r
        if streak_type is None:
            streak_type = result
            streak = 1
        elif result == streak_type:
            streak += 1
        else:
            break
    
    return {
        "win_rate": round(win_rate, 1),
        "current_streak": streak,
        "total_rounds": total,
        "recent_results": normalized[-5:],
        "trend": "improving" if (normalized and normalized[-1] == "win") else "declining"
    }

def _fetch_top_news() -> List[Dict[str, Any]]:
    """Fetch top 3 news headlines with sentiment."""
    try:
        items = news_service.fetch_news_feed(limit=3)
        if items and isinstance(items, list):
            out = []
            for item in items[:3]:
                out.append({
                    "headline": item.get("headline", ""),
                    "sentiment": item.get("sentiment", "neutral"),
                    "category": item.get("category", "general")
                })
            return out
    except Exception as e:
        logger.warning(f"Failed to fetch news for advisor: {e}")
    
    return [{"headline": "Market updates coming soon", "sentiment": "neutral", "category": "general"}]

# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.post("/chat")
async def advisor_chat(request: AdvisorChatRequest) -> APIResponse:
    """
    Main advisor chat endpoint.
    
    Flow:
    1. Build portfolio summary from context
    2. Calculate prediction stats
    3. Fetch top news with sentiment
    4. Call gemini_service.advisor_chat()
    5. Return response with suggested actions
    """
    try:
        user_context = request.user_context
        # Defensive normalization to avoid client-side shape mismatches
        portfolio_in = user_context.get("portfolio", [])
        if isinstance(portfolio_in, dict):
            portfolio_in = []
        prediction_hist_in = user_context.get("prediction_history", [])
        if prediction_hist_in and isinstance(prediction_hist_in, list) and isinstance(prediction_hist_in[0], str):
            prediction_hist_in = [{"result": r} for r in prediction_hist_in]
        user_context["portfolio"] = portfolio_in
        user_context["prediction_history"] = prediction_hist_in
        
        # Build summaries for Gemini
        portfolio_summary_dict = _build_portfolio_summary(user_context.get("portfolio", []))
        portfolio_text = portfolio_summary_dict.get("summary", "No portfolio")
        
        prediction_stats = _build_prediction_stats(user_context.get("prediction_history", []))
        
        # Fetch current news (cached)
        news_items = _fetch_top_news()
        news_summary = "\n".join([
            f"• {item['headline']} [{item['sentiment'].upper()}]"
            for item in news_items
        ])
        
        # Extract learning progress
        learning_progress = user_context.get("learning_progress", {})
        
        # Call Gemini advisor
        advisor_response = gemini_service.advisor_chat(
            message=request.message,
            conversation_history=request.conversation_history,
            user_level=user_context.get("level", "intermediate"),
            portfolio_summary=portfolio_text,
            prediction_stats=prediction_stats,
            learning_progress=learning_progress,
            top_news_summary=news_summary,
            virtual_balance=user_context.get("virtual_balance", 100000.0)
        )
        
        logger.info(f"advisor_chat completed: message_len={len(request.message)}")
        
        return APIResponse(
            success=True,
            data=advisor_response,
            message="Advisor response generated"
        )
    
    except Exception as e:
        logger.error(f"advisor_chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Advisor error: {str(e)}")


@router.get("/context-summary")
async def context_summary() -> APIResponse:
    """
    Return pre-built context for advisor sidebar.
    
    Includes:
    - Portfolio mini view (allocation, total value, P&L)
    - Prediction stats (win rate, streak)
    - Top 3 news with sentiment
    - Learning progress (completed topics, weak areas)
    """
    try:
        # For now, return mock data structure. In production, would fetch from user session.
        portfolio = [
            {"symbol": "AAPL", "quantity": 10, "current_price": 150.0, "pnl": 5.2},
            {"symbol": "BTC", "quantity": 0.5, "current_price": 45000.0, "pnl": -2.1},
        ]
        
        prediction_history = [
            {"result": "win"}, {"result": "win"}, {"result": "loss"},
            {"result": "win"}, {"result": "loss"}, {"result": "win"}
        ]
        
        learning_progress = {
            "completed_topics": 8,
            "total_topics": 20,
            "weak_areas": ["Options", "Futures"],
            "current_topic": "Technical Analysis"
        }
        
        # Build summaries
        portfolio_summary = _build_portfolio_summary(portfolio)
        prediction_stats = _build_prediction_stats(prediction_history)
        news_items = _fetch_top_news()
        
        result = {
            "portfolio_summary": portfolio_summary,
            "prediction_stats": prediction_stats,
            "news_headlines": news_items,
            "learning_progress": learning_progress
        }
        
        return APIResponse(
            success=True,
            data=result,
            message="Context summary loaded"
        )
    
    except Exception as e:
        logger.error(f"context_summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load context: {str(e)}")
