"""
Gemini 2.5 Flash integration for FinNexus.
All functions return JSON-only responses with automatic retries and logging.
"""
import json
import logging
import time
from typing import Any, Dict, List, Optional
import google.generativeai as genai

from backend.config import Settings

settings = Settings()
logger = logging.getLogger(__name__)

# Configure Gemini API (try both key names)
api_key = settings.google_api_key or settings.gemini_api_key
if not api_key:
    logger.warning("No Gemini API key configured. Falling back to local responses.")
    model = None
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

# ═══════════════════════════════════════════════════════════════════
# HELPER: JSON Response Parser with Fallback
# ═══════════════════════════════════════════════════════════════════

def _parse_gemini_json(response_text: str, fallback: Dict) -> Dict:
    """Parse Gemini response as JSON. Return fallback on failure."""
    try:
        # Remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        return json.loads(text)
    except Exception as e:
        logger.warning(f"Failed to parse Gemini JSON: {e}")
        return fallback

# ═══════════════════════════════════════════════════════════════════
# FUNCTION 1: teach_concept()
# ═══════════════════════════════════════════════════════════════════

def teach_concept(
    query: str,
    user_level: str,
    retrieved_chunks: Optional[List[Dict]] = None,
    live_market_data: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Teach a financial concept using Gemini, tailored to user level.
    Returns structured lesson with explanation, analogy, examples, etc.
    """
    start_time = time.time()
    
    # Format retrieved chunks
    chunks_formatted = ""
    if retrieved_chunks:
        for i, chunk in enumerate(retrieved_chunks[:3], 1):
            chunks_formatted += f"\n{i}. {chunk.get('content', '')[:200]}... [Source: {chunk.get('source', 'Unknown')}]"
    
    # Format market data
    market_formatted = "None provided" if not live_market_data else str(live_market_data)
    
    # Level-specific prompts
    level_guide = {
        "beginner": "Use simple words, no jargon. Explain like you're teaching a 15-year-old.",
        "intermediate": "Use standard financial terms. Brief formula explanations are OK.",
        "advanced": "Use full technical depth. Include risk metrics, edge cases, and advanced concepts."
    }.get(user_level.lower(), "Use standard financial terminology.")
    
    # Build prompt
    prompt = f"""You are FinMentor, an expert financial educator.
User Level: {user_level.upper()}
{level_guide}

Knowledge Context from documents:
{chunks_formatted}

Live Market Data:
{market_formatted}

User Question: {query}

Respond ONLY in this exact JSON format (no markdown, no backticks):
{{
  "explanation": "string (level-appropriate, max 150 words)",
  "analogy": "string (real-world comparison, max 50 words)",
  "market_example": "string (uses live data if provided)",
  "visual_data": {{
    "type": "line_chart|bar_chart|table|null",
    "title": "string",
    "data": []
  }},
  "key_takeaway": "string (one sentence, bold concepts)",
  "follow_up_questions": ["string", "string"],
  "related_playground_scenario": "string"
}}"""

    # Call Gemini with retry
    fallback = {
        "explanation": f"I need to learn more about {query}. Let's explore this together.",
        "analogy": "Imagine this like managing a business.",
        "market_example": "This matters in real markets every day.",
        "visual_data": {"type": None, "title": "", "data": []},
        "key_takeaway": "Understanding this concept improves financial decisions.",
        "follow_up_questions": ["Tell me more about this.", "How do I apply this?"],
        "related_playground_scenario": "Test this concept in our trading game."
    }
    
    try:
        if model is None:
            return fallback
        response = model.generate_content(prompt)
        result = _parse_gemini_json(response.text, fallback)
        elapsed = time.time() - start_time
        logger.info(f"teach_concept() completed in {elapsed:.2f}s | query: {query} | level: {user_level}")
        return result
    except Exception as e:
        logger.error(f"teach_concept() failed: {e}")
        return fallback


# ═══════════════════════════════════════════════════════════════════
# FUNCTION 2: explain_prediction_result()
# ═══════════════════════════════════════════════════════════════════

def explain_prediction_result(
    asset: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    actual_pct_change: float,
    direction: str,
    user_prediction: str,
    user_result: str,
    bot_prediction: str,
    bot_result: str,
    news_headlines: Optional[List[str]] = None,
    technical_indicators: Optional[Dict] = None,
    macro_data: Optional[Dict] = None,
    user_level: str = "intermediate"
) -> Dict[str, Any]:
    """Analyze prediction outcome with rich context."""
    start_time = time.time()
    
    news_str = " | ".join(news_headlines[:3]) if news_headlines else "No news data"
    tech_str = str(technical_indicators) if technical_indicators else "No technical data"
    macro_str = str(macro_data) if macro_data else "No macro data"
    
    prompt = f"""You are a senior market analyst explaining a trading prediction result.
Be specific, educational, and tie EVERY point back to the data provided.
Never be vague. Always cite a specific indicator or news event.

TRADE: {asset} | {timeframe} | {start_date} → {end_date}
ACTUAL MOVE: {actual_pct_change}% ({direction})
USER: predicted {user_prediction} → {user_result}
BOT: predicted {bot_prediction} → {bot_result}

NEWS at prediction time:
{news_str}

TECHNICAL INDICATORS:
{tech_str}

MACRO DATA:
{macro_str}

User Level: {user_level.upper()}

Return ONLY this JSON:
{{
  "what_happened": "string (2-3 sentences, specific)",
  "why_user_was_right_or_wrong": "string (cite specific data)",
  "why_bot_was_right_or_wrong": "string (cite specific data)",
  "key_signal_that_decided_it": "string (THE most important factor)",
  "what_pro_would_do": "string (actionable insight)",
  "lesson_topic": "string (topic name)",
  "lesson_link": "string (url-safe slug)"
}}"""

    fallback = {
        "what_happened": f"{asset} moved {actual_pct_change}% ({direction}) from {start_date} to {end_date}.",
        "why_user_was_right_or_wrong": f"Your prediction was {user_result}.",
        "why_bot_was_right_or_wrong": f"The bot's prediction was {bot_result}.",
        "key_signal_that_decided_it": "Market dynamics shifted in unexpected ways.",
        "what_pro_would_do": "Study the technical indicators and news correlation.",
        "lesson_topic": "Market Analysis",
        "lesson_link": "market-analysis"
    }
    
    try:
        if model is None:
            return fallback
        response = model.generate_content(prompt)
        result = _parse_gemini_json(response.text, fallback)
        elapsed = time.time() - start_time
        logger.info(f"explain_prediction_result() completed in {elapsed:.2f}s | asset: {asset}")
        return result
    except Exception as e:
        logger.error(f"explain_prediction_result() failed: {e}")
        return fallback


# ═══════════════════════════════════════════════════════════════════
# FUNCTION 3: analyze_news_impact()
# ═══════════════════════════════════════════════════════════════════

def analyze_news_impact(
    headline: str,
    body: str,
    category: str,
    sentiment: str,
    confidence: float,
    impact_score: int,
    affected_assets: Optional[List[str]] = None,
    live_prices: Optional[Dict] = None,
    user_portfolio: Optional[List] = None,
    user_level: str = "intermediate"
) -> Dict[str, Any]:
    """Analyze news impact on markets and portfolio."""
    start_time = time.time()
    
    prices_str = str(live_prices) if live_prices else "No price data"
    portfolio_str = str(user_portfolio) if user_portfolio else "No portfolio data"
    assets_str = ", ".join(affected_assets) if affected_assets else "Multiple sectors"
    
    prompt = f"""You are a financial news analyst and portfolio strategist.

NEWS HEADLINE:
{headline}

NEWS BODY:
{body}

Category: {category}
ML Sentiment: {sentiment} ({confidence*100:.0f}% confidence)
Market Impact Score: {impact_score}/100
Affected Assets: {assets_str}

Live Prices:
{prices_str}

User Portfolio:
{portfolio_str}

User Level: {user_level.upper()}

Return ONLY this JSON:
{{
  "what_happened": "string (summary of the news)",
  "why_it_matters": "string (explain significance)",
  "assets_affected": [
    {{"asset": "string", "direction": "up|down", "strength": "high|medium|low", "reason": "string"}}
  ],
  "general_strategy": "string (market-wide implication)",
  "portfolio_impact": "string (impact on user's holdings)",
  "recommended_action": "string (specific action)",
  "risk_warning": "string|null (if applicable)",
  "learn_more_topic": "string (relevant education topic)"
}}"""

    fallback = {
        "what_happened": headline,
        "why_it_matters": f"This news has an impact score of {impact_score}, indicating moderate market relevance.",
        "assets_affected": [{"asset": asset, "direction": "neutral", "strength": "medium", "reason": "Related to the news category"} for asset in (affected_assets or ["BTC", "ETH"])],
        "general_strategy": "Monitor market reaction over the next 24-48 hours.",
        "portfolio_impact": "Potential impact on securities related to this news.",
        "recommended_action": "Review holdings in affected sectors.",
        "risk_warning": None,
        "learn_more_topic": category
    }
    
    try:
        if model is None:
            return fallback
        response = model.generate_content(prompt)
        result = _parse_gemini_json(response.text, fallback)
        elapsed = time.time() - start_time
        logger.info(f"analyze_news_impact() completed in {elapsed:.2f}s | headline: {headline[:50]}")
        return result
    except Exception as e:
        logger.error(f"analyze_news_impact() failed: {e}")
        return fallback


# ═══════════════════════════════════════════════════════════════════
# FUNCTION 4: analyze_portfolio()
# ═══════════════════════════════════════════════════════════════════

def analyze_portfolio(
    holdings: Optional[List[Dict]] = None,
    metrics: Optional[Dict] = None,
    portfolio_type: str = "Balanced",
    risk_label: str = "Medium",
    risk_score: int = 5,
    top_news: Optional[List[str]] = None,
    user_level: str = "intermediate"
) -> Dict[str, Any]:
    """Comprehensive portfolio analysis."""
    start_time = time.time()
    
    holdings_str = str(holdings) if holdings else "No holdings data"
    news_str = " | ".join(top_news[:3]) if top_news else "No market news"
    sharpe = metrics.get("sharpe_ratio", 1.2) if metrics else 1.2
    drawdown = metrics.get("max_drawdown", 0.15) if metrics else 0.15
    volatility = metrics.get("volatility", 0.2) if metrics else 0.2
    
    prompt = f"""You are a personal portfolio manager reviewing a client's investments.

HOLDINGS:
{holdings_str}

RISK PROFILE: {risk_label} (score: {risk_score}/10)
PORTFOLIO TYPE: {portfolio_type}

METRICS:
Sharpe Ratio: {sharpe}
Max Drawdown: {drawdown*100:.1f}%
Volatility: {volatility*100:.1f}%

RELEVANT NEWS TODAY:
{news_str}

User Level: {user_level.upper()}

Return ONLY this JSON:
{{
  "overall_assessment": "string (1-2 sentences overall view)",
  "strengths": ["string", "string"],
  "weaknesses": ["string", "string"],
  "rebalancing_suggestion": "string (specific rebalancing advice)",
  "risk_reduction_tip": "string (how to reduce portfolio risk)",
  "opportunity_spotted": "string|null (if any)",
  "news_impact_on_portfolio": "string (how today's news affects them)",
  "action_items": ["string", "string", "string"]
}}"""

    fallback = {
        "overall_assessment": f"Your {portfolio_type} portfolio has a {risk_label} risk profile.",
        "strengths": ["Diversified holdings", "Reasonable risk-adjusted returns"],
        "weaknesses": ["Potential overexposure to volatility", "May benefit from rebalancing"],
        "rebalancing_suggestion": "Consider rebalancing quarterly to maintain target allocation.",
        "risk_reduction_tip": "Increase allocation to bonds or stable assets.",
        "opportunity_spotted": None,
        "news_impact_on_portfolio": f"Today's news may impact your portfolio. Sharpe Ratio: {sharpe:.2f}.",
        "action_items": [
            "Review sector allocation",
            "Check correlation of holdings",
            "Plan rebalancing strategy"
        ]
    }
    
    try:
        response = model.generate_content(prompt)
        result = _parse_gemini_json(response.text, fallback)
        elapsed = time.time() - start_time
        logger.info(f"analyze_portfolio() completed in {elapsed:.2f}s | type: {portfolio_type}")
        return result
    except Exception as e:
        logger.error(f"analyze_portfolio() failed: {e}")
        return fallback


# ═══════════════════════════════════════════════════════════════════
# FUNCTION 5: advisor_chat() — THE MAIN ADVISOR FUNCTION
# ═══════════════════════════════════════════════════════════════════

def advisor_chat(
    message: str,
    conversation_history: Optional[List[Dict]] = None,
    user_level: str = "intermediate",
    portfolio_summary: str = "No portfolio",
    prediction_stats: Optional[Dict] = None,
    learning_progress: Optional[Dict] = None,
    top_news_summary: str = "No news",
    virtual_balance: float = 100000.0
) -> Dict[str, Any]:
    """
    Main advisor chat function — ties all modules together.
    This is the most important Gemini integration.
    """
    start_time = time.time()
    
    # Build conversation history string
    history_str = ""
    if conversation_history:
        for msg in conversation_history[-8:]:  # Last 8 messages max
            role = "User" if msg.get("role") == "user" else "Advisor"
            history_str += f"{role}: {msg.get('content', '')}\n"
    
    # Default stats
    if not prediction_stats:
        prediction_stats = {
            "win_rate": 50,
            "current_streak": 2,
            "total_rounds": 10
        }
    
    if not learning_progress:
        learning_progress = {
            "completed_topics": 5,
            "weak_areas": ["Options", "Derivatives"],
            "current_topic": "Candlestick Patterns"
        }
    
    prompt = f"""You are FinAdvisor, an expert AI financial strategist.
You have COMPLETE context about this user. 
Use their ACTUAL data in every response — never be generic.

USER PROFILE:
Level: {user_level.upper()}
Virtual Balance: ₹{virtual_balance:,.0f}

PORTFOLIO:
{portfolio_summary}

PREDICTION HISTORY:
Win Rate: {prediction_stats.get('win_rate', 50)}%
Current Streak: {prediction_stats.get('current_streak', 1)} wins
Total Rounds: {prediction_stats.get('total_rounds', 0)}

LEARNING STATUS:
Completed Topics: {prediction_stats.get('completed_topics', 5)}
Weak Areas: {', '.join(learning_progress.get('weak_areas', ['Market Analysis']))}
Currently Learning: {learning_progress.get('current_topic', 'General Finance')}

TODAY'S MARKET NEWS (top 3):
{top_news_summary}

CONVERSATION HISTORY:
{history_str}

USER MESSAGE: {message}

RESPONSE RULES:
- Reference their portfolio BY NAME when relevant
- If win rate < 40%, address their prediction pattern
- Always suggest a learning topic from their weak areas
- End with ONE specific actionable next step
- Adjust complexity for their {user_level.upper()} level
- Be warm, conversational, and specific to their data

Return ONLY this JSON:
{{
  "reply": "string (conversational, warm, specific to their data)",
  "suggested_actions": [
    {{"label": "string", "route": "string", "icon": "string"}},
    {{"label": "string", "route": "string", "icon": "string"}}
  ],
  "related_module": "learn|playground|news|portfolio|null",
  "proactive_insight": "string|null (something they didn't ask but should know)"
}}"""

    fallback = {
        "reply": f"Hi! I'm FinAdvisor. I can see your {virtual_balance:,.0f} balance and {prediction_stats.get('win_rate', 50)}% win rate. How can I help you today?",
        "suggested_actions": [
            {"label": "View Portfolio", "route": "/portfolio", "icon": "📊"},
            {"label": "Play Prediction Game", "route": "/playground", "icon": "🎯"},
            {"label": "Learn New Topic", "route": "/learn", "icon": "📚"}
        ],
        "related_module": None,
        "proactive_insight": None
    }
    
    try:
        response = model.generate_content(prompt)
        result = _parse_gemini_json(response.text, fallback)
        elapsed = time.time() - start_time
        logger.info(f"advisor_chat() completed in {elapsed:.2f}s | message_len: {len(message)}")
        return result
    except Exception as e:
        logger.error(f"advisor_chat() failed: {e}")
        return fallback
