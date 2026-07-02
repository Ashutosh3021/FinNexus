"""
FinNexus Bot — RAG Ingestion Pipeline
======================================
Populates local ChromaDB collections from:
  1. Feature CSVs  → market_data
  2. NewsAPI       → news_events
  3. Built-in finance knowledge → trading_theories (via RAGRetriever seed)

Run:
    python -m Bot.RAG.ingest
    python -m Bot.RAG.ingest --market-only
    python -m Bot.RAG.ingest --news-only
"""

from __future__ import annotations

import argparse
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

from Bot import config as cfg
from Bot.RAG.retriever import RAGRetriever

logger = logging.getLogger(__name__)

_PROJECT_ROOT = cfg.PROJECT_ROOT
_FEATURES_ROOT = _PROJECT_ROOT / "Data" / "Features"

_MARKET_SAMPLES: List[Tuple[str, str, str]] = [
    ("Crypto", "BTC_features.csv", "BTC"),
    ("Crypto", "ETH_features.csv", "ETH"),
    ("Crypto", "SOL_features.csv", "SOL"),
    ("ETFs", "SPY_features.csv", "SPY"),
    ("ETFs", "QQQ_features.csv", "QQQ"),
    ("ETFs", "GLD_features.csv", "GLD"),
    ("Commodities", "Gold_features.csv", "GOLD"),
    ("Commodities", "WTI_Crude_Oil_features.csv", "WTI"),
    ("Futures", "NIFTY_50_Futures_features.csv", "NIFTY"),
    ("Futures", "BANK_NIFTY_Futures_features.csv", "BANKNIFTY"),
    ("Stocks", "N50_RELIANCE_features.csv", "RELIANCE"),
    ("Stocks", "N50_HDFCBANK_features.csv", "HDFCBANK"),
    ("Stocks", "N50_TCS_features.csv", "TCS"),
]

_NEWS_QUERIES: List[Tuple[str, List[str]]] = [
    ("Federal Reserve interest rates stock market", ["SPY", "TLT", "DXY"]),
    ("Bitcoin cryptocurrency ETF institutional", ["BTC", "ETH", "IBIT"]),
    ("India NIFTY Sensex RBI economy", ["NIFTY", "BANKNIFTY", "INR"]),
    ("oil OPEC crude energy prices", ["WTI", "XLE", "USO"]),
    ("gold inflation treasury yields", ["GLD", "TLT", "GOLD"]),
]


def _infer_regime(vix: float, dist_sma_50: float) -> str:
    if vix >= 28:
        return "volatile"
    if dist_sma_50 > 0.02:
        return "bull"
    if dist_sma_50 < -0.02:
        return "bear"
    return "neutral"


def _infer_trend(row: pd.Series) -> str:
    for col, label in [
        ("dist_from_sma_50", "50d MA"),
        ("dist_from_sma_200", "200d MA"),
        ("golden_cross", "golden cross"),
    ]:
        if col not in row.index:
            continue
        val = row[col]
        if pd.isna(val):
            continue
        if col == "golden_cross" and float(val) > 0:
            return "golden cross active"
        if col.startswith("dist_from_sma"):
            if float(val) > 0.01:
                return f"above {label}"
            if float(val) < -0.01:
                return f"below {label}"
    return "near key MAs"


def _latest_feature_row(csv_path: Path) -> Optional[pd.Series]:
    if not csv_path.exists():
        return None
    df = pd.read_csv(csv_path)
    if df.empty:
        return None
    return df.iloc[-1]


def ingest_market_snapshots(
    retriever: RAGRetriever,
    features_root: Path = _FEATURES_ROOT,
) -> int:
    """Embed latest row from each sample feature CSV into market_data."""
    count = 0
    for asset_class, filename, symbol in _MARKET_SAMPLES:
        path = features_root / asset_class / filename
        row = _latest_feature_row(path)
        if row is None:
            logger.warning("ingest_market: skip missing/empty %s", path)
            continue

        close = float(row.get("Close", 0) or 0)
        vix_proxy = float(row.get("return_7d", 0) or 0)
        vix = 18.0 + abs(vix_proxy) * 100
        dist_50 = float(row.get("dist_from_sma_50", 0) or 0)
        regime = _infer_regime(vix, dist_50)
        trend = _infer_trend(row)
        date_str = str(row.get("Date", ""))[:10]

        text = (
            f"{symbol} ({asset_class}) snapshot {date_str}: "
            f"close={close:,.2f}, regime={regime}, trend={trend}, "
            f"7d_return={float(row.get('return_7d', 0) or 0):.4f}, "
            f"RSI={float(row.get('rsi_14', 50) if 'rsi_14' in row.index else 50):.1f}."
        )
        doc_id = f"market_{symbol.lower()}_{date_str}"
        retriever.upsert_market(
            doc_id=doc_id,
            text=text,
            regime=regime,
            asset=symbol,
            price=close,
            trend=trend,
            vix=round(vix, 2),
        )
        count += 1
        logger.info("ingest_market: %s @ %.2f (%s)", symbol, close, regime)

    return count


def _classify_impact(headline: str) -> str:
    lower = headline.lower()
    if any(w in lower for w in ("surge", "rally", "beat", "record high", "inflow", "cut rates")):
        return "bullish"
    if any(w in lower for w in ("crash", "plunge", "miss", "downgrade", "hike", "war", "sanction")):
        return "bearish"
    if any(w in lower for w in ("hold", "unchanged", "flat", "mixed")):
        return "neutral"
    return "neutral"


def ingest_news_from_api(
    retriever: RAGRetriever,
    api_key: str = "",
    max_articles: int = 15,
) -> int:
    """Fetch headlines from newsapi.org and upsert into news_events."""
    key = api_key or cfg.NEWSAPI_KEY
    if not key:
        logger.warning("ingest_news: NEWSAPI_KEY not set — seeding static headlines")
        return _ingest_static_news(retriever)

    count = 0
    seen: set = set()
    for query, affected in _NEWS_QUERIES:
        if count >= max_articles:
            break
        url = (
            "https://newsapi.org/v2/everything"
            f"?q={requests.utils.quote(query)}"
            f"&sortBy=publishedAt&pageSize=3&language=en&apiKey={key}"
        )
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code != 200:
                logger.warning("ingest_news: API %s for query '%s'", resp.status_code, query[:30])
                continue
            for art in resp.json().get("articles", []):
                title = (art.get("title") or "").strip()
                if not title or title in seen:
                    continue
                seen.add(title)
                impact = _classify_impact(title)
                pub = art.get("publishedAt", "")[:10]
                slug = re.sub(r"[^a-z0-9]+", "_", title.lower())[:48]
                doc_id = f"news_{pub}_{slug}"
                retriever.upsert_news(
                    doc_id=doc_id,
                    headline=title[:500],
                    impact=impact,
                    affected=",".join(affected),
                )
                count += 1
                logger.info("ingest_news: [%s] %s", impact, title[:70])
                if count >= max_articles:
                    break
        except Exception as exc:
            logger.warning("ingest_news: request failed: %s", exc)

    if count == 0:
        return _ingest_static_news(retriever)
    return count


def _ingest_static_news(retriever: RAGRetriever) -> int:
    """Fallback headlines when NewsAPI is unavailable."""
    static = [
        ("Fed holds rates steady; dot plot signals one cut this year", "neutral", "SPY,TLT,DXY"),
        ("Bitcoin ETF weekly inflows hit record as institutions accumulate", "bullish", "BTC,ETH,IBIT"),
        ("India RBI keeps repo rate unchanged; growth outlook revised up", "bullish", "NIFTY,INR"),
        ("OPEC+ extends output cuts through Q3; Brent rises on supply tightness", "bullish", "WTI,BRENT,XLE"),
        ("US CPI cools more than expected; bond yields fall, equities rally", "bullish", "SPY,TLT,GLD"),
    ]
    for i, (headline, impact, affected) in enumerate(static):
        retriever.upsert_news(
            doc_id=f"static_news_{i}",
            headline=headline,
            impact=impact,
            affected=affected,
        )
    return len(static)


def run_full_ingestion(
    persist_path: Optional[str] = None,
    skip_news: bool = False,
    skip_market: bool = False,
) -> Dict:
    """
    Run complete RAG ingestion. Returns stats dict.
    """
    path = persist_path or str(cfg.CHROMA_PERSIST_PATH)
    retriever = RAGRetriever(persist_path=path)

    market_n = 0 if skip_market else ingest_market_snapshots(retriever)
    news_n = 0 if skip_news else ingest_news_from_api(retriever)

    stats = retriever.stats()
    stats["ingested_market"] = market_n
    stats["ingested_news"] = news_n
    stats["ingested_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(
        "RAG ingestion complete: market=%d news=%d collections=%s",
        market_n, news_n, stats.get("collection_counts"),
    )
    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(description="FinNexus RAG ingestion")
    parser.add_argument("--market-only", action="store_true")
    parser.add_argument("--news-only", action="store_true")
    parser.add_argument("--persist-path", default="")
    args = parser.parse_args()

    skip_market = args.news_only
    skip_news = args.market_only
    stats = run_full_ingestion(
        persist_path=args.persist_path or None,
        skip_news=skip_news,
        skip_market=skip_market,
    )
    print("\n=== RAG INGESTION RESULT ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
