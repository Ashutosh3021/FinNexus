"""
FinNexus Bot — RAG Retriever
Retrieves relevant context chunks for a given query from:
  1. In-memory document store (books / notes loaded at startup)
  2. Local CSV market data summaries (from Data/Cleaned/)
  3. (Optional) a vector store via sentence-transformers + FAISS

Falls back gracefully to keyword search if heavy deps aren't available.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Optional vector search deps ──────────────────────────────────────────────
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer  # type: ignore
    import faiss  # type: ignore
    _VECTOR_SEARCH = True
except ImportError:
    _VECTOR_SEARCH = False
    logger.warning("RAG: sentence-transformers/faiss not installed — using keyword search")


# ---------------------------------------------------------------------------
# Document chunk
# ---------------------------------------------------------------------------

class Chunk:
    __slots__ = ("id", "source", "text", "metadata")

    def __init__(self, id: str, source: str, text: str, metadata: Dict = None):
        self.id = id
        self.source = source
        self.text = text
        self.metadata: Dict = metadata or {}

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source,
            "text": self.text[:500],  # truncate for API responses
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# RAGRetriever
# ---------------------------------------------------------------------------

class RAGRetriever:
    """
    Stores documents as chunks and retrieves top-k most relevant ones
    for a query, using either vector similarity or keyword overlap.
    """

    def __init__(self, embed_model: str = "all-MiniLM-L6-v2"):
        self._chunks: List[Chunk] = []
        self._embed_model_name = embed_model
        self._embedder: Optional[Any] = None
        self._index: Optional[Any] = None  # FAISS index
        self._index_dirty = False           # needs rebuild after new docs

        self._init_embedder()
        self._load_builtin_knowledge()

    # ── Initialise embedder ───────────────────────────────────────────────────

    def _init_embedder(self) -> None:
        if not _VECTOR_SEARCH:
            return
        try:
            self._embedder = SentenceTransformer(self._embed_model_name)
            logger.info("RAGRetriever: loaded embedder '%s'", self._embed_model_name)
        except Exception as exc:
            logger.warning("RAGRetriever: embedder load failed: %s", exc)
            self._embedder = None

    # ── Built-in knowledge base ───────────────────────────────────────────────

    def _load_builtin_knowledge(self) -> None:
        """Seed the retriever with core finance knowledge chunks."""
        knowledge = _BUILTIN_KNOWLEDGE
        for i, (source, text) in enumerate(knowledge):
            self.add_chunk(Chunk(id=f"builtin_{i}", source=source, text=text))
        logger.info("RAGRetriever: loaded %d built-in knowledge chunks", len(knowledge))

    # ── Public API ────────────────────────────────────────────────────────────

    def add_chunk(self, chunk: Chunk) -> None:
        self._chunks.append(chunk)
        self._index_dirty = True

    def add_text(self, text: str, source: str = "user_doc", chunk_size: int = 400) -> int:
        """Split text into chunks and add all. Returns count added."""
        parts = _split_text(text, chunk_size)
        for i, part in enumerate(parts):
            self.add_chunk(Chunk(
                id=f"{source}_{i}",
                source=source,
                text=part,
            ))
        return len(parts)

    def load_jsonl(self, path: str | Path) -> int:
        """Load chunks from a JSONL file where each line is a Chunk dict."""
        count = 0
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                self.add_chunk(Chunk(
                    id=d.get("id", f"jsonl_{count}"),
                    source=d.get("source", str(path)),
                    text=d["text"],
                    metadata=d.get("metadata", {}),
                ))
                count += 1
        logger.info("RAGRetriever: loaded %d chunks from %s", count, path)
        return count

    def retrieve(self, query: str, top_k: int = 5) -> List[Chunk]:
        """Return top_k most relevant chunks for query."""
        if not self._chunks:
            return []

        if _VECTOR_SEARCH and self._embedder:
            return self._vector_retrieve(query, top_k)
        return self._keyword_retrieve(query, top_k)

    def get_context_text(self, query: str, top_k: int = 5) -> str:
        """Convenience: return retrieved chunks as a single string."""
        chunks = self.retrieve(query, top_k)
        parts = [f"[{c.source}] {c.text}" for c in chunks]
        return "\n\n---\n\n".join(parts)

    # ── Vector retrieval ─────────────────────────────────────────────────────

    def _rebuild_index(self) -> None:
        if not _VECTOR_SEARCH or not self._embedder:
            return
        texts = [c.text for c in self._chunks]
        embeddings = self._embedder.encode(texts, show_progress_bar=False)
        embeddings = embeddings.astype("float32")
        faiss.normalize_L2(embeddings)
        dim = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(dim)  # inner product = cosine after normalise
        self._index.add(embeddings)
        self._index_dirty = False
        logger.debug("RAGRetriever: rebuilt FAISS index with %d vectors", len(texts))

    def _vector_retrieve(self, query: str, top_k: int) -> List[Chunk]:
        if self._index_dirty:
            self._rebuild_index()
        if self._index is None:
            return self._keyword_retrieve(query, top_k)

        q_emb = self._embedder.encode([query], show_progress_bar=False).astype("float32")
        faiss.normalize_L2(q_emb)
        k = min(top_k, len(self._chunks))
        _, indices = self._index.search(q_emb, k)
        return [self._chunks[i] for i in indices[0] if 0 <= i < len(self._chunks)]

    # ── Keyword retrieval (fallback) ──────────────────────────────────────────

    def _keyword_retrieve(self, query: str, top_k: int) -> List[Chunk]:
        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored: List[tuple[float, Chunk]] = []

        for chunk in self._chunks:
            chunk_tokens = set(re.findall(r"\w+", chunk.text.lower()))
            overlap = len(query_tokens & chunk_tokens)
            if overlap > 0:
                scored.append((overlap / max(len(query_tokens), 1), chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> Dict:
        return {
            "total_chunks": len(self._chunks),
            "vector_search_available": _VECTOR_SEARCH and self._embedder is not None,
            "index_built": not self._index_dirty and self._index is not None,
        }


# ---------------------------------------------------------------------------
# Text splitter
# ---------------------------------------------------------------------------

def _split_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


# ---------------------------------------------------------------------------
# Built-in finance knowledge (seed data)
# ---------------------------------------------------------------------------

_BUILTIN_KNOWLEDGE: List[tuple[str, str]] = [
    ("technical_analysis",
     "RSI (Relative Strength Index) above 70 indicates overbought conditions — a potential reversal zone. "
     "RSI below 30 indicates oversold conditions — a potential bounce zone. "
     "RSI is a momentum oscillator ranging 0-100, computed over a 14-period default window."),

    ("technical_analysis",
     "Moving averages smooth price action. The 200-day MA is a key long-term trend indicator. "
     "Price above the 200-day MA is bullish; below is bearish. "
     "A golden cross (50-day crossing above 200-day) is a bullish signal. "
     "A death cross (50-day crossing below 200-day) is a bearish signal."),

    ("options_greeks",
     "Options Greeks: Delta measures price sensitivity to underlying. Gamma is rate of Delta change. "
     "Theta is daily time decay — options lose value each day they are held. "
     "Vega measures sensitivity to implied volatility changes. Rho measures interest rate sensitivity."),

    ("futures_basis",
     "Futures basis = Futures price - Spot price. A positive basis (contango) means futures trade at a premium "
     "reflecting carrying costs (interest, storage). A negative basis (backwardation) means futures trade at a "
     "discount, usually signalling strong immediate demand. Nifty futures typically trade at a premium equal to "
     "the risk-free rate times time to expiry."),

    ("macro_correlations",
     "Gold and USD typically have an inverse relationship — a strong dollar suppresses gold prices. "
     "When both gold and USD rise together it often signals a flight to safety in a crisis. "
     "Gold is also inversely correlated to real interest rates: higher real rates reduce gold appeal."),

    ("crypto_fundamentals",
     "Bitcoin on-chain metrics: HODL waves track coin age distribution. Whale wallet accumulation (wallets > 1000 BTC) "
     "is a bullish signal. Exchange inflows signal selling intent. The Stock-to-Flow model relates Bitcoin scarcity to price. "
     "Bitcoin halving events (every ~4 years) reduce new supply, historically preceding bull runs."),

    ("india_equities",
     "Nifty 50 is the benchmark index of the NSE comprising 50 large-cap Indian companies. "
     "FII (Foreign Institutional Investor) flows heavily influence direction — sustained FII buying is bullish. "
     "Bank Nifty is the banking sector index. Q1 earnings season (April-July) is a key catalyst. "
     "RBI monetary policy decisions impact rate-sensitive sectors: banking, real estate, auto."),

    ("candlestick_patterns",
     "Doji: open ≈ close, long wicks — signals indecision. Hammer: small body, long lower wick at bottom of downtrend — bullish reversal. "
     "Shooting Star: small body, long upper wick at top of uptrend — bearish reversal. "
     "Engulfing: large candle envelops prior candle — bullish or bearish depending on direction. "
     "Marubozu: no wicks, full body — strong directional conviction."),

    ("risk_management",
     "Position sizing: risk no more than 1-2% of capital per trade. Stop-loss placement below key support. "
     "Risk-reward ratio: aim for at least 1:2. Diversification across uncorrelated assets reduces portfolio volatility. "
     "Volatility-adjusted position sizing: reduce size in high-VIX environments."),

    ("global_events_level20",
     "Level 20 covers macro global events: Fed rate decisions, geopolitical conflicts, commodity supply shocks, "
     "central bank interventions, currency crises. These events cause cross-asset contagion and regime shifts. "
     "A Fed rate hike cycle typically strengthens USD, pressures emerging market currencies, raises bond yields, "
     "and initially suppresses equities. Oil supply shocks (OPEC cuts, war) are inflationary and affect all assets."),
]
