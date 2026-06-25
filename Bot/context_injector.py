"""
FinNexus Bot — Market Context Fetcher
======================================
Pulls real-time market data and news to populate MarketContext before
question generation. Falls back gracefully when APIs are unavailable.

Supported data sources (in priority order):
  1. yfinance  — price snapshots (free, no key)
  2. NewsAPI   — recent headlines (free tier, key required)
  3. Hardcoded fallbacks — always available

Typical usage:
    from context_fetcher import build_context
    from llm_generator import QuestionGenerator, MarketContext

    ctx = build_context(user_level=2, user_id=42)
    gen = QuestionGenerator(llm_client=my_llm)
    questions = gen.generate(level=2, user_id=42, context=ctx)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# yfinance tickers to snapshot
_PRICE_TICKERS: Dict[str, str] = {
    "BTC-USD":   "BTC",
    "ETH-USD":   "ETH",
    "^NSEI":     "NIFTY",
    "^GSPC":     "SPY",
    "GC=F":      "GOLD",
    "CL=F":      "WTI",
    "DX-Y.NYB":  "DXY",
    "^VIX":      "VIX",
}

# Symbols to pull trend context (5d vs 50d MA)
_TREND_TICKERS = ["BTC-USD", "^NSEI", "^GSPC", "GC=F"]

# Maximum age of cached context (seconds)
_CACHE_TTL_SECONDS = 900  # 15 minutes

# ---------------------------------------------------------------------------
# Simple in-process cache
# ---------------------------------------------------------------------------

@dataclass
class _CachedContext:
    context: "MarketContext"
    fetched_at: float = field(default_factory=time.time)

    def is_fresh(self) -> bool:
        return (time.time() - self.fetched_at) < _CACHE_TTL_SECONDS


_cache: Optional[_CachedContext] = None


# ---------------------------------------------------------------------------
# Price and trend fetcher (yfinance)
# ---------------------------------------------------------------------------

def _fetch_prices_and_trends() -> tuple[Dict[str, float], Dict[str, str], str, float, str]:
    """
    Returns: (prices, trends, regime, vix_level, dxy_trend)
    Falls back to empty dicts on failure.
    """
    prices: Dict[str, float] = {}
    trends: Dict[str, str] = {}
    regime = "neutral"
    vix_level = 18.0
    dxy_trend = "flat"

    try:
        import yfinance as yf  # type: ignore

        # ── Price snapshot ────────────────────────────────────────────────
        tickers = list(_PRICE_TICKERS.keys())
        raw = yf.download(tickers, period="5d", interval="1d", progress=False, auto_adjust=True)

        if "Close" in raw.columns:
            close = raw["Close"]
        else:
            close = raw  # single ticker edge case

        for yf_sym, label in _PRICE_TICKERS.items():
            try:
                val = float(close[yf_sym].dropna().iloc[-1])
                prices[label] = round(val, 2)
            except Exception:
                pass

        vix_level = prices.get("VIX", 18.0)
        dxy_val = prices.pop("DXY", None)  # DXY is for trend only, not displayed

        # ── Trend context ─────────────────────────────────────────────────
        for yf_sym in _TREND_TICKERS:
            label = _PRICE_TICKERS.get(yf_sym, yf_sym)
            try:
                hist = yf.download(yf_sym, period="60d", interval="1d",
                                   progress=False, auto_adjust=True)["Close"].dropna()
                price_now = float(hist.iloc[-1])
                ma50 = float(hist.rolling(50).mean().iloc[-1])
                ma20 = float(hist.rolling(20).mean().iloc[-1])
                pct_from_50d = ((price_now / ma50) - 1) * 100

                if price_now > ma50 * 1.05:
                    trend_str = f"above 50d MA (+{pct_from_50d:.1f}%)"
                elif price_now > ma50:
                    trend_str = f"just above 50d MA (+{pct_from_50d:.1f}%)"
                elif price_now > ma50 * 0.95:
                    trend_str = f"just below 50d MA ({pct_from_50d:.1f}%)"
                else:
                    trend_str = f"below 50d MA ({pct_from_50d:.1f}%)"

                # Add overbought/oversold context
                if price_now > ma20 * 1.10:
                    trend_str += ", extended"
                elif price_now < ma20 * 0.90:
                    trend_str += ", oversold"

                trends[label] = trend_str
            except Exception as exc:
                logger.debug("Trend fetch failed for %s: %s", yf_sym, exc)

        # ── Market regime ─────────────────────────────────────────────────
        spy_price = prices.get("SPY", 0)
        nifty_price = prices.get("NIFTY", 0)

        if vix_level > 30:
            regime = "volatile"
        elif vix_level < 14:
            regime = "bull"  # calm markets typically in uptrend
        elif spy_price > 0 and "SPY" in trends and "above" in trends.get("SPY", ""):
            regime = "bull"
        else:
            regime = "neutral"

        # ── DXY trend ─────────────────────────────────────────────────────
        if dxy_val:
            try:
                hist_dxy = yf.download("DX-Y.NYB", period="30d", interval="1d",
                                       progress=False, auto_adjust=True)["Close"].dropna()
                dxy_1m_change = (float(hist_dxy.iloc[-1]) / float(hist_dxy.iloc[0]) - 1) * 100
                if dxy_1m_change > 1.5:
                    dxy_trend = "rising"
                elif dxy_1m_change < -1.5:
                    dxy_trend = "falling"
                else:
                    dxy_trend = "flat"
            except Exception:
                pass

    except ImportError:
        logger.info("yfinance not installed — using fallback prices")
    except Exception as exc:
        logger.warning("Price fetch failed: %s", exc)

    return prices, trends, regime, vix_level, dxy_trend


# ---------------------------------------------------------------------------
# News fetcher (NewsAPI)
# ---------------------------------------------------------------------------

def _fetch_news(max_headlines: int = 8) -> List[str]:
    """
    Pulls recent market-relevant headlines.
    Falls back to curated static headlines if NewsAPI unavailable.
    """
    api_key = os.getenv("NEWSAPI_KEY", "")

    if api_key:
        try:
            import requests  # type: ignore
            queries = [
                "stock market Federal Reserve",
                "India NIFTY Sensex economy",
                "Bitcoin cryptocurrency",
                "oil gold commodities",
            ]
            headlines: List[str] = []
            for q in queries:
                url = (
                    "https://newsapi.org/v2/everything"
                    f"?q={q}&sortBy=publishedAt&pageSize=2"
                    f"&language=en&apiKey={api_key}"
                )
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    for article in resp.json().get("articles", []):
                        title = article.get("title", "").strip()
                        source = article.get("source", {}).get("name", "")
                        if title and len(title) > 20:
                            headlines.append(f"[{source}] {title}")
            return headlines[:max_headlines]
        except Exception as exc:
            logger.warning("NewsAPI fetch failed: %s — using static fallback", exc)

    # ── Static fallback headlines ──────────────────────────────────────────
    # These are representative but NOT real-time. LLM will be instructed
    # to use them as format examples and augment with its own knowledge.
    return [
        "[Fallback] Federal Reserve holds rates; signals data-dependent path for cuts",
        "[Fallback] India Q1 GDP growth at 7.8%; beats consensus estimate of 7.2%",
        "[Fallback] OPEC+ extends production cuts through next quarter",
        "[Fallback] BTC ETF inflows accelerate; institutional allocation rising",
        "[Fallback] US Non-Farm Payrolls: 180k vs 210k expected — mild miss",
        "[Fallback] China manufacturing PMI at 49.8 — near contraction territory",
        "[Fallback] RBI holds repo rate at 6.5%; maintains withdrawal of accommodation",
        "[Fallback] Gold at multi-month high on geopolitical tensions",
    ][:max_headlines]


# ---------------------------------------------------------------------------
# User profile builder
# ---------------------------------------------------------------------------

def _build_user_profile(
    user_level: int,
    portfolio_allocation: Optional[str],
    history_summary: Optional[str],
) -> tuple[str, str]:
    """
    Returns (portfolio_str, history_str) for MarketContext.
    Uses defaults if not provided.
    """
    default_portfolios = {
        1: "60% Large-cap stocks, 30% Cash, 10% Gold",
        2: "45% Stocks (mix large/mid), 25% Crypto, 20% ETFs, 10% Cash",
        3: "35% Stocks, 20% Crypto, 20% Derivatives/Futures, 15% Commodities, 10% Cash",
        4: "40% Long/Short Equity, 20% Derivatives, 20% Fixed Income, 10% Crypto, 10% Cash",
        5: "30% Global Macro, 25% Quant Strategies, 20% Alternatives, 15% Bonds, 10% Cash",
        20: "Multi-asset global: 35% Equities, 20% Bonds, 20% Commodities, 15% Crypto, 10% Cash",
    }

    default_history = {
        1: "New to trading. Strong in basics; needs to develop risk instincts.",
        2: "Intermediate. Comfortable with technical analysis; macro awareness developing.",
        3: "Advanced. Familiar with options and derivatives; event-driven thinking.",
        4: "Expert. Portfolio-level decision maker; systematic approach.",
        5: "Master. Quantitative and macro expertise. Multi-strategy.",
        20: "Senior professional. Global macro. Cross-asset synthesis.",
    }

    portfolio = portfolio_allocation or default_portfolios.get(user_level, default_portfolios[2])
    history = history_summary or default_history.get(user_level, default_history[2])

    return portfolio, history


# ---------------------------------------------------------------------------
# Main public interface
# ---------------------------------------------------------------------------

def build_context(
    user_level: int = 1,
    user_id: int = 0,
    portfolio_allocation: Optional[str] = None,
    history_summary: Optional[str] = None,
    force_refresh: bool = False,
) -> "MarketContext":
    """
    Build a MarketContext populated with live market data.

    Args:
        user_level:           Current user level (1-5, 20).
        user_id:              User ID (for logging).
        portfolio_allocation: Override portfolio string (e.g. "50% BTC, 50% Cash").
        history_summary:      Override user profile string.
        force_refresh:        Bypass the 15-minute cache.

    Returns:
        MarketContext ready for injection into question generation.
    """
    # Import here to avoid circular import (llm_generator imports this module)
    from llm_generator import MarketContext

    global _cache

    if not force_refresh and _cache and _cache.is_fresh():
        logger.debug("build_context: returning cached context (age %.0fs)",
                     time.time() - _cache.fetched_at)
        # Still update user-specific fields
        ctx = _cache.context
        portfolio, history = _build_user_profile(user_level, portfolio_allocation, history_summary)
        ctx.user_level = user_level
        ctx.user_portfolio = portfolio
        ctx.user_history_summary = history
        return ctx

    logger.info("build_context: fetching fresh market data for user %d level %d", user_id, user_level)

    prices, trends, regime, vix_level, dxy_trend = _fetch_prices_and_trends()
    news = _fetch_news()
    portfolio, history = _build_user_profile(user_level, portfolio_allocation, history_summary)

    ctx = MarketContext(
        regime=regime,
        vix_level=vix_level,
        dxy_trend=dxy_trend,
        news=news,
        prices=prices,
        trends=trends,
        user_level=user_level,
        user_portfolio=portfolio,
        user_history_summary=history,
    )

    _cache = _CachedContext(context=ctx)
    logger.info(
        "build_context: regime=%s VIX=%.1f prices=%d news=%d",
        regime, vix_level, len(prices), len(news),
    )
    return ctx


def invalidate_cache() -> None:
    """Force the next call to build_context to re-fetch data."""
    global _cache
    _cache = None
    logger.info("build_context: cache invalidated")


# ---------------------------------------------------------------------------
# CLI quick-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    ctx = build_context(user_level=2, user_id=999)
    print("\n=== MARKET CONTEXT ===")
    print(ctx.to_prompt_block())
    print("\n=== RAW PRICES ===")
    print(json.dumps(ctx.prices, indent=2))
    print("\n=== NEWS HEADLINES ===")
    for h in ctx.news:
        print(" •", h)