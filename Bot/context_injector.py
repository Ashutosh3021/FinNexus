"""
FinNexus Bot — Context Injector
=================================
Assembles a slim, LLM-ready context dict from RAG retrievals.

The injector pulls from three RAG collections (market_data, news_events,
trading_theories) and merges live market signals + user profile into one
tight dict that fits under 500 tokens when serialized.

OUTPUT FORMAT (strict):
{
  "market": { "regime": str, "asset": str, "price": float, "trend": str, "vix": float },
  "news":   [ { "headline": str, "impact": str, "affected": list } ],  // max 3 items
  "theory": [ { "name": str, "key_point": str } ],                     // max 3 items
  "user":   { "level": int, "weakness": str }                          // single top weakness
}

Also exposes:
  - ContextInjector class (used by Bot/main.py: self._context_injector.build_context(user_id, level))
  - build_context() module-level function (backwards-compat for direct callers)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_CACHE_TTL_SECONDS = 900  # 15 minutes


@dataclass
class _CachedPayload:
    market: Dict
    news: List[Dict]
    theory: List[Dict]
    fetched_at: float = field(default_factory=time.time)

    def is_fresh(self) -> bool:
        return (time.time() - self.fetched_at) < _CACHE_TTL_SECONDS


_market_cache: Optional[_CachedPayload] = None


# ---------------------------------------------------------------------------
# Live market helpers (yfinance, NewsAPI) — optional
# ---------------------------------------------------------------------------

def _fetch_live_market() -> Optional[Dict]:
    """
    Try to pull a live market snapshot via yfinance.
    Returns a slim market dict or None on failure.
    """
    try:
        import yfinance as yf  # type: ignore

        raw = yf.download(
            ["^VIX", "^GSPC", "BTC-USD", "^NSEI"],
            period="5d", interval="1d",
            progress=False, auto_adjust=True,
        )
        close = raw.get("Close", raw)

        def _last(sym: str) -> float:
            try:
                return round(float(close[sym].dropna().iloc[-1]), 2)
            except Exception:
                return 0.0

        vix = _last("^VIX") or 18.0
        spy = _last("^GSPC")
        btc = _last("BTC-USD")
        nifty = _last("^NSEI")

        # Simple regime logic
        if vix > 30:
            regime = "volatile"
        elif vix < 14 and spy > 0:
            regime = "bull"
        else:
            regime = "neutral"

        # Pick the most query-relevant asset (BTC if crypto context, else SPY)
        asset = "BTC" if btc > 0 else "SPY"
        price = btc if btc > 0 else spy

        return {
            "regime": regime,
            "asset":  asset,
            "price":  price,
            "trend":  "above 50d MA" if regime == "bull" else "near 50d MA",
            "vix":    vix,
        }
    except Exception as exc:
        logger.debug("_fetch_live_market failed: %s", exc)
        return None


def _fetch_live_news(max_items: int = 3) -> List[Dict]:
    """
    Try NewsAPI for recent headlines. Falls back to static stubs.
    Returns max 3 slim news dicts.
    """
    api_key = os.getenv("NEWSAPI_KEY", "")

    if api_key:
        try:
            import requests  # type: ignore

            queries = [
                ("stock market Federal Reserve", ["SPY", "TLT"]),
                ("India NIFTY Sensex economy",   ["NIFTY", "INFY"]),
                ("Bitcoin cryptocurrency ETF",   ["BTC", "ETH"]),
            ]
            items: List[Dict] = []
            for q, affected in queries:
                if len(items) >= max_items:
                    break
                url = (
                    "https://newsapi.org/v2/everything"
                    f"?q={q}&sortBy=publishedAt&pageSize=1"
                    f"&language=en&apiKey={api_key}"
                )
                resp = requests.get(url, timeout=4)
                if resp.status_code == 200:
                    articles = resp.json().get("articles", [])
                    if articles:
                        title = articles[0].get("title", "").strip()[:120]
                        if title:
                            items.append({
                                "headline": title,
                                "impact":   "neutral",
                                "affected": affected,
                            })
            if items:
                return items[:max_items]
        except Exception as exc:
            logger.debug("_fetch_live_news failed: %s", exc)

    # Static fallback — representative, not real-time
    return [
        {
            "headline": "Federal Reserve holds rates; signals data-dependent path for cuts",
            "impact":   "bearish_bonds",
            "affected": ["TLT", "SPY", "DXY"],
        },
        {
            "headline": "OPEC+ extends production cuts — oil supply tightens",
            "impact":   "bullish_oil",
            "affected": ["WTI", "XLE", "USO"],
        },
        {
            "headline": "Bitcoin ETF inflows accelerate; institutional allocation rising",
            "impact":   "bullish_crypto",
            "affected": ["BTC", "ETH", "IBIT"],
        },
    ][:max_items]


# ---------------------------------------------------------------------------
# User weakness helper
# ---------------------------------------------------------------------------

_WEAKNESS_MAP = {
    1: "basic risk management",
    2: "macro awareness",
    3: "options Greeks application",
    4: "portfolio-level hedging",
    5: "cross-asset synthesis",
    20: "global macro regime identification",
}


def _top_weakness(user_id: int, level: int, db=None) -> str:
    """
    Return the single most relevant weakness for this user.
    Uses DB history if available, otherwise falls back to level default.
    """
    if db is not None:
        try:
            history = db.get_user_history(user_id, limit=20)
            if history:
                # Find the answer with the lowest score and use its question type
                worst = min(history, key=lambda h: h.get("score", 1.0))
                score = worst.get("score", 1.0)
                qtype = worst.get("question_type", "")
                if score < 0.4 and qtype:
                    return f"low score on {qtype} questions"
        except Exception:
            pass
    return _WEAKNESS_MAP.get(level, "multi-factor synthesis")


# ---------------------------------------------------------------------------
# Core assembly function
# ---------------------------------------------------------------------------

def _assemble_context(
    user_id: int,
    level: int,
    db=None,
    retriever=None,
    query: str = "market overview",
    force_refresh: bool = False,
) -> Dict:
    """
    Internal: build the slim context dict.
    Uses cache for market/news/theory; user block is always live.
    """
    global _market_cache

    # ── Market block ──────────────────────────────────────────────────────────
    if not force_refresh and _market_cache and _market_cache.is_fresh():
        market_block = _market_cache.market
        news_block   = _market_cache.news
        theory_block = _market_cache.theory
    else:
        # Try live data first
        market_block = _fetch_live_market()
        news_items   = _fetch_live_news(max_items=3)

        # Supplement/override with RAG if available
        if retriever is not None:
            rag_market = retriever.get_market_context(query)
            if market_block is None:
                market_block = rag_market
            else:
                # Merge: keep live price/vix, use RAG regime only as fallback
                if market_block.get("regime") == "neutral":
                    market_block["regime"] = rag_market.get("regime", "neutral")

            rag_news = retriever.get_news_context(query)
            rag_news_items = rag_news.get("items", [])
            # Merge live + RAG news, dedup by headline prefix, cap at 3
            seen: set = set()
            merged: List[Dict] = []
            for item in news_items + rag_news_items:
                key = item.get("headline", "")[:40]
                if key and key not in seen:
                    seen.add(key)
                    merged.append(item)
                if len(merged) >= 3:
                    break
            news_items = merged

            rag_theory = retriever.get_theory_context(query)
            theory_items = [
                {"name": t["name"], "key_point": t["key_point"]}
                for t in rag_theory.get("items", [])[:3]
            ]
        else:
            theory_items = []

        # Final market fallback
        if market_block is None:
            market_block = {
                "regime": "neutral",
                "asset":  "SPY",
                "price":  0.0,
                "trend":  "flat",
                "vix":    18.0,
            }

        # Enforce schema and types
        market_block = {
            "regime": str(market_block.get("regime", "neutral")),
            "asset":  str(market_block.get("asset",  "unknown")),
            "price":  float(market_block.get("price", 0.0)),
            "trend":  str(market_block.get("trend",  "flat")),
            "vix":    float(market_block.get("vix",   18.0)),
        }
        news_block   = news_items[:3]
        theory_block = theory_items[:3]

        _market_cache = _CachedPayload(
            market=market_block,
            news=news_block,
            theory=theory_block,
        )

    # ── User block (always fresh) ──────────────────────────────────────────────
    weakness = _top_weakness(user_id, level, db)
    user_block = {
        "level":    level,
        "weakness": weakness,
    }

    return {
        "market": market_block,
        "news":   news_block,
        "theory": theory_block,
        "user":   user_block,
    }


# ---------------------------------------------------------------------------
# ContextInjector class (used by Bot/main.py)
# ---------------------------------------------------------------------------

class ContextInjector:
    """
    Assembles the slim LLM context dict and converts it to a MarketContext
    for backwards compatibility with QuestionGenerator.

    Bot/main.py usage:
        self._context_injector = ContextInjector(db=db)
        market_context = self._context_injector.build_context(user_id, level)
    """

    def __init__(self, db=None, retriever=None):
        self._db = db
        self._retriever = retriever
        # Lazy-load retriever from RAG module if not provided
        if self._retriever is None:
            try:
                from Bot.RAG.retriever import RAGRetriever
                self._retriever = RAGRetriever()
            except Exception as exc:
                logger.warning("ContextInjector: could not init RAGRetriever: %s", exc)

    def get_slim_context(
        self,
        user_id: int,
        level: int,
        query: str = "market overview",
        force_refresh: bool = False,
    ) -> Dict:
        """
        Return the slim context dict in the canonical output format:
        {
          "market": { "regime", "asset", "price", "trend", "vix" },
          "news":   [ { "headline", "impact", "affected" } ],  // max 3
          "theory": [ { "name", "key_point" } ],               // max 3
          "user":   { "level", "weakness" }
        }
        """
        return _assemble_context(
            user_id=user_id,
            level=level,
            db=self._db,
            retriever=self._retriever,
            query=query,
            force_refresh=force_refresh,
        )

    def build_context(
        self,
        user_id: int,
        level: int,
        force_refresh: bool = False,
    ) -> "MarketContext":
        """
        Build a MarketContext for the QuestionGenerator.
        Adapts the slim dict into the MarketContext dataclass.
        """
        # Import here to avoid circular dependency
        from Bot.llm_generator import MarketContext

        slim = self.get_slim_context(user_id, level, force_refresh=force_refresh)
        mkt = slim["market"]
        news_items = slim["news"]
        user = slim["user"]

        # Convert slim news dicts → flat headline strings for MarketContext.news
        headlines = [
            f"[{n.get('impact', 'neutral').upper()}] {n.get('headline', '')}"
            for n in news_items
        ]

        return MarketContext(
            regime=mkt["regime"],
            vix_level=mkt["vix"],
            dxy_trend="flat",               # not in slim format; use default
            news=headlines,
            prices={mkt["asset"]: mkt["price"]} if mkt["price"] > 0 else {},
            trends={mkt["asset"]: mkt["trend"]} if mkt["trend"] else {},
            user_level=user["level"],
            user_portfolio="",              # not in slim format
            user_history_summary=f"Top weakness: {user['weakness']}",
        )

    def invalidate_cache(self) -> None:
        """Force the next call to re-fetch all data."""
        global _market_cache
        _market_cache = None
        logger.info("ContextInjector: cache invalidated")


# ---------------------------------------------------------------------------
# Module-level backwards-compatible build_context()
# ---------------------------------------------------------------------------

_default_injector: Optional[ContextInjector] = None


def build_context(
    user_level: int = 1,
    user_id: int = 0,
    portfolio_allocation: Optional[str] = None,
    history_summary: Optional[str] = None,
    force_refresh: bool = False,
) -> "MarketContext":
    """
    Backwards-compatible module-level function.
    Returns a MarketContext (same as before) using the new RAG engine.

    Args:
        user_level:           Current user level (1-5, 20).
        user_id:              User ID.
        portfolio_allocation: Ignored (kept for signature compat).
        history_summary:      Ignored (kept for signature compat).
        force_refresh:        Bypass 15-minute cache.
    """
    global _default_injector
    if _default_injector is None:
        _default_injector = ContextInjector()
    return _default_injector.build_context(
        user_id=user_id,
        level=user_level,
        force_refresh=force_refresh,
    )


def invalidate_cache() -> None:
    """Force the next call to build_context to re-fetch data."""
    global _default_injector
    if _default_injector is not None:
        _default_injector.invalidate_cache()
    else:
        global _market_cache
        _market_cache = None
    logger.info("context_injector: cache invalidated")


# ---------------------------------------------------------------------------
# CLI quick-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)

    injector = ContextInjector()
    slim = injector.get_slim_context(user_id=999, level=2)
    print("\n=== SLIM CONTEXT (LLM-ready) ===")
    print(json.dumps(slim, indent=2))

    serialized = json.dumps(slim, separators=(",", ":"))
    print(f"\nSerialized length: {len(serialized)} chars (~{len(serialized)//4} tokens)")

    mc = injector.build_context(user_id=999, level=2)
    print("\n=== MARKET CONTEXT (for QuestionGenerator) ===")
    print(mc.to_prompt_block())
