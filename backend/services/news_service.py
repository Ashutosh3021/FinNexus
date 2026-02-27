"""
News service for fetching and analyzing financial news.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from ..config import settings
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

# News categories
CATEGORIES = ["all", "macro", "crypto", "earnings", "commodities", "tech", "global"]


def fetch_news_feed(
    category: str = "all",
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Fetch financial news from NewsAPI.
    
    Args:
        category: News category filter
        limit: Maximum number of news items
        
    Returns:
        List of news items
    """
    cache_key = f"news_{category}_{limit}"
    cached = cache_service.get(cache_key)
    if cached:
        return cached
    
    news_items = []
    
    # Try NewsAPI first
    if settings.newsapi_key:
        try:
            news_items = _fetch_from_newsapi(category, limit)
        except Exception as e:
            logger.warning(f"NewsAPI failed: {e}")
    
    # Fallback to mock data if NewsAPI fails
    if not news_items:
        news_items = _get_mock_news(category, limit)
    
    # Filter by category if needed
    if category != "all":
        news_items = [n for n in news_items if n.get("category") == category]
    
    # Limit results
    news_items = news_items[:limit]
    
    cache_service.set(cache_key, news_items, ttl=300)
    return news_items


def _fetch_from_newsapi(category: str, limit: int) -> List[Dict[str, Any]]:
    """Fetch news from NewsAPI."""
    # Map categories to search queries
    queries = {
        "all": "finance OR stock OR market OR economy",
        "macro": "Federal Reserve OR interest rate OR inflation OR GDP",
        "crypto": "Bitcoin OR cryptocurrency OR blockchain OR Ethereum",
        "earnings": "earnings OR revenue OR quarterly results",
        "commodities": "oil OR gold OR commodity prices",
        "tech": "technology stocks OR tech earnings OR AI",
        "global": "global markets OR international OR world economy"
    }
    
    query = queries.get(category, queries["all"])
    
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": limit,
        "apiKey": settings.newsapi_key
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    news_items = []
    for article in data.get("articles", []):
        news_items.append({
            "id": f"news_{len(news_items)}",
            "headline": article.get("title", ""),
            "category": category,
            "sentiment": "neutral",
            "impact_score": 5,
            "affected_assets": _extract_mentioned_assets(article.get("title", "")),
            "summary": article.get("description", "")[:200],
            "gemini_analysis": "",
            "date": article.get("publishedAt", "")[:10],
            "source": article.get("source", {}).get("name", "Unknown")
        })
    
    return news_items


def _extract_mentioned_assets(text: str) -> List[str]:
    """Extract stock/crypto symbols from text."""
    assets = []
    text_upper = text.upper()
    
    # Common stocks
    stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "SPY"]
    for stock in stocks:
        if stock in text_upper:
            assets.append(stock)
    
    # Crypto
    cryptos = ["BITCOIN", "BTC", "ETHEREUM", "ETH", "SOLANA", "SOL"]
    for crypto in cryptos:
        if crypto in text_upper:
            if crypto == "BITCOIN":
                assets.append("BTC-USD")
            elif crypto == "ETHEREUM":
                assets.append("ETH-USD")
            elif crypto == "SOLANA":
                assets.append("SOL-USD")
    
    return assets[:5]


def _get_mock_news(category: str, limit: int) -> List[Dict[str, Any]]:
    """Return mock news data as fallback."""
    mock_news = [
        {
            "id": "news_001",
            "headline": "Fed Signals Stable Interest Rates Through 2024",
            "category": "macro",
            "sentiment": "neutral",
            "impact_score": 7,
            "affected_assets": ["SPY", "MSFT", "AAPL"],
            "summary": "Federal Reserve officials indicate no immediate changes to monetary policy.",
            "gemini_analysis": "This signals economic stability but may limit growth expectations for the broader market.",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": "Reuters"
        },
        {
            "id": "news_002",
            "headline": "Bitcoin Surges Amid Institutional Adoption",
            "category": "crypto",
            "sentiment": "positive",
            "impact_score": 9,
            "affected_assets": ["BTC-USD", "ETH-USD"],
            "summary": "Bitcoin gains momentum as institutional investors increase allocations.",
            "gemini_analysis": "Strong institutional buying pressure signals sustained demand for crypto assets.",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": "CoinDesk"
        },
        {
            "id": "news_003",
            "headline": "Tech Giants Report Strong Quarterly Earnings",
            "category": "earnings",
            "sentiment": "positive",
            "impact_score": 8,
            "affected_assets": ["AAPL", "MSFT", "GOOGL"],
            "summary": "Major tech companies exceed profit expectations, raising market optimism.",
            "gemini_analysis": "Strong earnings and positive guidance suggest continued momentum in technology sector.",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": "CNBC"
        },
        {
            "id": "news_004",
            "headline": "Oil Prices Decline Amid Demand Concerns",
            "category": "commodities",
            "sentiment": "negative",
            "impact_score": 6,
            "affected_assets": ["CL=F"],
            "summary": "Global oil prices drop as economic slowdown concerns emerge.",
            "gemini_analysis": "Energy sector pressure may persist if recession indicators continue deteriorating.",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": "Bloomberg"
        },
        {
            "id": "news_005",
            "headline": "Gold Rises as Safe-Haven Asset",
            "category": "commodities",
            "sentiment": "positive",
            "impact_score": 5,
            "affected_assets": ["GOLD"],
            "summary": "Gold prices rise amid geopolitical tensions and inflation concerns.",
            "gemini_analysis": "Precious metals remain attractive as inflation hedges in uncertain environment.",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": "MarketWatch"
        },
        {
            "id": "news_006",
            "headline": "AI Investments Continue to Drive Tech Sector",
            "category": "tech",
            "sentiment": "positive",
            "impact_score": 8,
            "affected_assets": ["NVDA", "MSFT", "GOOGL"],
            "summary": "Artificial intelligence investments continue to fuel tech sector growth.",
            "gemini_analysis": "AI adoption is accelerating across industries, benefiting leading technology companies.",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": "Financial Times"
        }
    ]
    
    return mock_news[:limit]


def get_news_by_id(news_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific news item by ID.
    
    Args:
        news_id: News item ID
        
    Returns:
        News item or None if not found
    """
    news = fetch_news_feed(limit=50)
    for item in news:
        if item.get("id") == news_id:
            return item
    return None


def get_latest_headlines(limit: int = 5) -> List[str]:
    """
    Get latest news headlines for advisor context.
    
    Args:
        limit: Number of headlines to return
        
    Returns:
        List of headline strings
    """
    news = fetch_news_feed(limit=limit)
    return [item.get("headline", "") for item in news if item.get("headline")]
