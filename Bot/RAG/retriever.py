"""
FinNexus Bot — RAG Retriever (ChromaDB)
========================================
Fetches context from three ChromaDB collections using sentence-transformers
embeddings (all-MiniLM-L6-v2).

Collections:
  - "market_data"       → market regime, price, trend snippets
  - "news_events"       → recent market-relevant news entries
  - "trading_theories"  → finance knowledge (TA, risk, macro theories)

Public API:
  get_market_context(query)  → slim dict (max 5 fields)
  get_news_context(query)    → slim dict (max 5 fields)
  get_theory_context(query)  → slim dict (max 5 fields)
  get_context_text(query)    → plain text (backwards-compat for SAQEvaluator)
  embed(texts)               → np.ndarray of embeddings
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── ChromaDB ────────────────────────────────────────────────────────────────
try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
    _CHROMA_OK = True
except ImportError:
    _CHROMA_OK = False
    logger.warning("RAG: chromadb not installed — retriever will return empty results")

# ── Embedder ─────────────────────────────────────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    _EMBED_OK = True
except ImportError:
    _EMBED_OK = False
    logger.warning("RAG: sentence-transformers not installed — embeddings disabled")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_EMBED_MODEL = "all-MiniLM-L6-v2"
_TOP_K = 3  # hard ceiling — never return more than 3 results per query

# Default ChromaDB persist path (override via CHROMA_PERSIST_PATH env var)
_PERSIST_PATH = os.getenv(
    "CHROMA_PERSIST_PATH",
    str(Path(__file__).parent.parent.parent / "Data" / "chroma_db"),
)

# Collection names
_COL_MARKET = "market_data"
_COL_NEWS = "news_events"
_COL_THEORY = "trading_theories"


# ---------------------------------------------------------------------------
# Embed utility (module-level, reusable by evaluator/injector)
# ---------------------------------------------------------------------------

_embedder: Optional[Any] = None


def _get_embedder() -> Optional[Any]:
    global _embedder
    if _embedder is not None:
        return _embedder
    if not _EMBED_OK:
        return None
    try:
        _embedder = SentenceTransformer(_EMBED_MODEL)
        logger.info("RAGRetriever: loaded embedder '%s'", _EMBED_MODEL)
    except Exception as exc:
        logger.warning("RAGRetriever: embedder load failed: %s", exc)
        _embedder = None
    return _embedder


def embed(texts: List[str]) -> Optional[Any]:
    """
    Embed a list of strings using all-MiniLM-L6-v2.
    Returns numpy array of shape (N, 384) or None if embedder unavailable.
    """
    model = _get_embedder()
    if model is None:
        return None
    return model.encode(texts, show_progress_bar=False)


# ---------------------------------------------------------------------------
# RAGRetriever
# ---------------------------------------------------------------------------

class RAGRetriever:
    """
    ChromaDB-backed retriever with three domain-specific fetch methods.
    Falls back to empty results if ChromaDB/embedder is unavailable.
    """

    def __init__(
        self,
        persist_path: str = _PERSIST_PATH,
        embed_model: str = _EMBED_MODEL,
    ):
        self._persist_path = persist_path
        self._client: Optional[Any] = None
        self._collections: Dict[str, Any] = {}
        self._init_client()
        self._ensure_collections()
        self._seed_builtin_knowledge()

    # ── Initialise ChromaDB client ────────────────────────────────────────────

    def _init_client(self) -> None:
        if not _CHROMA_OK:
            return
        try:
            Path(self._persist_path).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self._persist_path,
                settings=Settings(anonymized_telemetry=False),
            )
            logger.info("RAGRetriever: ChromaDB connected at %s", self._persist_path)
        except Exception as exc:
            logger.warning("RAGRetriever: ChromaDB init failed: %s", exc)
            self._client = None

    # ── Ensure collections exist ──────────────────────────────────────────────

    def _ensure_collections(self) -> None:
        if self._client is None:
            return
        for name in (_COL_MARKET, _COL_NEWS, _COL_THEORY):
            try:
                col = self._client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                )
                self._collections[name] = col
            except Exception as exc:
                logger.warning("RAGRetriever: failed to get/create collection '%s': %s", name, exc)

    # ── Seed built-in finance knowledge ──────────────────────────────────────

    def _seed_builtin_knowledge(self) -> None:
        """Seed trading_theories collection if empty."""
        col = self._collections.get(_COL_THEORY)
        if col is None:
            return
        try:
            if col.count() > 0:
                return  # already seeded
        except Exception:
            return

        ids, docs, metas = [], [], []
        for i, (source, text) in enumerate(_BUILTIN_THEORIES):
            ids.append(f"theory_{i}")
            docs.append(text)
            metas.append({"source": source})

        embs = embed(docs)
        try:
            if embs is not None:
                col.add(
                    ids=ids,
                    documents=docs,
                    embeddings=embs.tolist(),
                    metadatas=metas,
                )
            else:
                col.add(ids=ids, documents=docs, metadatas=metas)
            logger.info("RAGRetriever: seeded %d theory chunks", len(ids))
        except Exception as exc:
            logger.warning("RAGRetriever: seed failed: %s", exc)

    # ── Domain fetch methods ──────────────────────────────────────────────────

    def get_market_context(self, query: str) -> Dict:
        """
        Fetch top-3 market_data chunks for query.
        Returns slim dict with max 5 fields.
        """
        results = self._query_collection(_COL_MARKET, query)
        if not results:
            return {
                "regime": "neutral",
                "asset": "unknown",
                "price": 0.0,
                "trend": "flat",
                "vix": 18.0,
            }

        # Parse first result for structured fields, use rest as trend context
        top = results[0]
        meta = top.get("metadata", {})
        return {
            "regime":  meta.get("regime", "neutral"),
            "asset":   meta.get("asset", top.get("id", "unknown")),
            "price":   float(meta.get("price", 0.0)),
            "trend":   meta.get("trend", top.get("text", "")[:80]),
            "vix":     float(meta.get("vix", 18.0)),
        }

    def get_news_context(self, query: str) -> Dict:
        """
        Fetch top-3 news_events chunks for query.
        Returns slim dict with max 5 fields.
        """
        results = self._query_collection(_COL_NEWS, query)
        items = []
        for r in results[:_TOP_K]:
            meta = r.get("metadata", {})
            affected_raw = meta.get("affected", "")
            affected = (
                affected_raw if isinstance(affected_raw, list)
                else [a.strip() for a in affected_raw.split(",") if a.strip()]
            )
            items.append({
                "headline": r.get("text", "")[:120],
                "impact":   meta.get("impact", "neutral"),
                "affected": affected[:3],  # cap list length
            })
        return {
            "items":  items,
            "count":  len(items),
            "query":  query[:60],
            "source": _COL_NEWS,
            "top_k":  _TOP_K,
        }

    def get_theory_context(self, query: str) -> Dict:
        """
        Fetch top-3 trading_theories chunks for query.
        Returns slim dict with max 5 fields.
        """
        results = self._query_collection(_COL_THEORY, query)
        items = []
        for r in results[:_TOP_K]:
            meta = r.get("metadata", {})
            text = r.get("text", "")
            # Extract first sentence as key_point
            key_point = text.split(".")[0].strip()[:120] if text else ""
            items.append({
                "name":      meta.get("source", r.get("id", "theory")),
                "key_point": key_point,
            })
        return {
            "items":  items,
            "count":  len(items),
            "query":  query[:60],
            "source": _COL_THEORY,
            "top_k":  _TOP_K,
        }

    # ── Backwards-compatible method for SAQEvaluator ─────────────────────────

    def get_context_text(self, query: str, top_k: int = _TOP_K) -> str:
        """
        Return retrieved theory + news chunks as plain text.
        Kept for SAQEvaluator compatibility.
        top_k is accepted but internally capped at _TOP_K=3.
        """
        effective_k = min(top_k, _TOP_K)
        theory = self._query_collection(_COL_THEORY, query)
        news = self._query_collection(_COL_NEWS, query)

        combined = (theory + news)[:effective_k]
        if not combined:
            return ""
        return "\n\n---\n\n".join(
            f"[{r.get('metadata', {}).get('source', 'doc')}] {r.get('text', '')}"
            for r in combined
        )

    # ── Upsert helpers (for loading fresh market/news data) ───────────────────

    def upsert_market(
        self,
        doc_id: str,
        text: str,
        regime: str = "neutral",
        asset: str = "",
        price: float = 0.0,
        trend: str = "",
        vix: float = 18.0,
    ) -> None:
        """Add or update a document in the market_data collection."""
        self._upsert(_COL_MARKET, doc_id, text, {
            "regime": regime,
            "asset":  asset,
            "price":  price,
            "trend":  trend,
            "vix":    vix,
        })

    def upsert_news(
        self,
        doc_id: str,
        headline: str,
        impact: str = "neutral",
        affected: str = "",
    ) -> None:
        """Add or update a document in the news_events collection."""
        self._upsert(_COL_NEWS, doc_id, headline, {
            "impact":   impact,
            "affected": affected,
        })

    def upsert_theory(
        self,
        doc_id: str,
        text: str,
        source: str = "theory",
    ) -> None:
        """Add or update a document in the trading_theories collection."""
        self._upsert(_COL_THEORY, doc_id, text, {"source": source})

    # ── Internal query helper ─────────────────────────────────────────────────

    def _query_collection(self, collection_name: str, query: str) -> List[Dict]:
        col = self._collections.get(collection_name)
        if col is None:
            return []
        try:
            n_results = min(_TOP_K, max(col.count(), 1))
            emb = embed([query])
            if emb is not None:
                result = col.query(
                    query_embeddings=emb.tolist(),
                    n_results=n_results,
                    include=["documents", "metadatas", "distances"],
                )
            else:
                result = col.query(
                    query_texts=[query],
                    n_results=n_results,
                    include=["documents", "metadatas", "distances"],
                )

            ids    = result.get("ids", [[]])[0]
            docs   = result.get("documents", [[]])[0]
            metas  = result.get("metadatas", [[]])[0]

            return [
                {"id": ids[i], "text": docs[i], "metadata": metas[i]}
                for i in range(len(ids))
            ]
        except Exception as exc:
            logger.warning("RAGRetriever: query '%s' failed on '%s': %s",
                           query[:40], collection_name, exc)
            return []

    def _upsert(self, collection_name: str, doc_id: str, text: str, meta: Dict) -> None:
        col = self._collections.get(collection_name)
        if col is None:
            logger.warning("RAGRetriever: collection '%s' not available", collection_name)
            return
        try:
            emb = embed([text])
            if emb is not None:
                col.upsert(
                    ids=[doc_id],
                    documents=[text],
                    embeddings=emb.tolist(),
                    metadatas=[meta],
                )
            else:
                col.upsert(ids=[doc_id], documents=[text], metadatas=[meta])
        except Exception as exc:
            logger.warning("RAGRetriever: upsert failed for '%s': %s", doc_id, exc)

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> Dict:
        counts = {}
        for name, col in self._collections.items():
            try:
                counts[name] = col.count()
            except Exception:
                counts[name] = -1
        return {
            "chroma_available":  _CHROMA_OK,
            "embedder_available": _EMBED_OK,
            "persist_path":      self._persist_path,
            "collection_counts": counts,
        }


# ---------------------------------------------------------------------------
# Built-in finance knowledge (seed for trading_theories collection)
# ---------------------------------------------------------------------------

_BUILTIN_THEORIES: List[tuple[str, str]] = [
    ("technical_analysis",
     "RSI above 70 indicates overbought conditions — potential reversal zone. "
     "RSI below 30 indicates oversold — potential bounce zone. "
     "Computed over a 14-period default window, range 0-100."),

    ("moving_averages",
     "The 200-day MA is the key long-term trend indicator. Price above = bullish. "
     "Golden cross (50d over 200d) is bullish. Death cross (50d under 200d) is bearish."),

    ("options_greeks",
     "Delta = price sensitivity to underlying. Gamma = rate of Delta change. "
     "Theta = daily time decay. Vega = sensitivity to implied volatility. "
     "Rho = interest rate sensitivity."),

    ("futures_basis",
     "Futures basis = Futures price - Spot price. Positive basis = contango (futures premium). "
     "Negative basis = backwardation (futures discount, strong immediate demand). "
     "Nifty futures trade at premium equal to risk-free rate × time to expiry."),

    ("macro_correlations",
     "Gold and USD are inversely correlated. Strong dollar suppresses gold. "
     "Gold rises with real interest rate declines. Both gold and USD rising signals crisis."),

    ("crypto_fundamentals",
     "Bitcoin halving (every ~4 years) reduces new supply. Exchange inflows signal selling. "
     "Whale wallet accumulation (>1000 BTC) is bullish. Stock-to-Flow models scarcity."),

    ("india_equities",
     "Nifty 50 = 50 large-cap NSE stocks. FII sustained buying is bullish. "
     "Bank Nifty is the banking index. RBI policy impacts banking, real estate, auto."),

    ("candlestick_patterns",
     "Doji = indecision. Hammer at downtrend bottom = bullish reversal. "
     "Shooting star at uptrend top = bearish reversal. "
     "Engulfing candle signals directional shift. Marubozu = strong conviction."),

    ("risk_management",
     "Risk 1-2% of capital per trade. Stop-loss below key support. "
     "Aim for 1:2 risk-reward minimum. Reduce position size in high-VIX environments."),

    ("global_macro",
     "Fed rate hike cycle strengthens USD, pressures EM currencies, raises bond yields, "
     "suppresses equities initially. OPEC supply cuts are inflationary across all assets. "
     "Geopolitical risk spikes gold and oil simultaneously."),
]
