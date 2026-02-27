"""RAG (retrieval-augmented generation) service for FinNexus.

This module provides a light-weight, well-formed ChromaDB integration used
by the application startup to initialize and seed the educational knowledge
collection. It exposes:

- `initialize_chromadb()` to initialize the client/collection (idempotent)
- `seed_initial_knowledge()` to seed curated lesson documents
- `_collection` global (used elsewhere for quick checks)

The implementation below is intentionally simple and robust for local
development: it uses a SentenceTransformer embedder wrapped for Chroma.
"""
import logging
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from ..config import settings

logger = logging.getLogger(__name__)

# Module-level references required by other modules (main.py checks _collection)
_client = None
_collection = None
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        try:
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer embedder loaded")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _embedder


def initialize_chromadb() -> bool:
    """Initialize ChromaDB persistent client and the knowledge collection.

    Returns True on success. If the collection is empty it will be seeded.
    """
    global _client, _collection
    try:
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False)
        )

        _collection = _client.get_or_create_collection(
            name="finlearn_knowledge",
            embedding_function=ef,
            metadata={"description": "FinNexus educational content"}
        )

        count = _collection.count()
        logger.info(f"ChromaDB initialized at {settings.chroma_persist_dir} with {count} documents")

        if count == 0:
            seed_initial_knowledge()

        return True

    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        return False


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    if not text:
        return []
    words = text.split()
    chunks: List[str] = []
    i = 0
    n = len(words)
    while i < n:
        chunk = words[i:i + chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks


def seed_initial_knowledge() -> bool:
    """Seed the collection with curated educational documents.

    This function is idempotent for common development use-cases.
    """
    global _collection
    if _collection is None:
        logger.error("Cannot seed knowledge: collection is not initialized")
        return False

    try:
        # Minimal curated set used for demos and tests
        docs = [
            {
                "id": "lesson_001",
                "title": "Introduction to Stock Markets",
                "content": (
                    "A stock represents ownership in a company. When you buy shares, you "
                    "become a partial owner. Stock markets are exchanges where buyers and "
                    "sellers trade shares. Key concepts: Bull market, Bear market, Dividends, "
                    "Capital gains. Market indices like the S&P 500 track performance."
                ),
                "topic": "Stocks",
                "level": "BEGINNER",
                "source": "seed"
            },
            {
                "id": "lesson_002",
                "title": "Technical Analysis Basics",
                "content": (
                    "Technical analysis studies price action and volume to forecast short-term "
                    "movements. Tools include moving averages, RSI, MACD, and candlestick patterns."
                ),
                "topic": "Technical Analysis",
                "level": "INTERMEDIATE",
                "source": "seed"
            },
            {
                "id": "lesson_003",
                "title": "Portfolio Diversification",
                "content": (
                    "Diversification reduces idiosyncratic risk by spreading exposure across "
                    "uncorrelated assets. Asset classes include stocks, bonds, commodities, "
                    "and cash. Rebalancing maintains target allocations over time."
                ),
                "topic": "Portfolio",
                "level": "BEGINNER",
                "source": "seed"
            }
        ]

        # Ingest documents as chunked entries so retrieval works via Chroma
        for doc in docs:
            doc_id = doc["id"]
            # Skip if already ingested (simple check by id existence)
            try:
                existing = _collection.get(ids=[f"{doc_id}_chunk_0"])
                if existing and len(existing.get("ids", [])) > 0:
                    logger.info(f"Document {doc_id} already present, skipping")
                    continue
            except Exception:
                # Collection.get may raise if id not present; ignore
                pass

            chunks = chunk_text(doc["content"], chunk_size=200, overlap=50)
            ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "doc_id": doc_id,
                    "title": doc["title"],
                    "topic": doc.get("topic", "general"),
                    "level": doc.get("level", "BEGINNER"),
                    "source": doc.get("source", "seed"),
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]

            _collection.add(ids=ids, documents=chunks, metadatas=metadatas)
            logger.info(f"Seeded document {doc_id} with {len(chunks)} chunks")

        logger.info("ChromaDB seeding complete")
        return True

    except Exception as e:
        logger.error(f"Failed to seed initial knowledge: {e}")
        return False


def retrieve_context(query: str, user_level: str = None, top_k: int = 3) -> List[Dict[str, Any]]:
    """Perform a semantic search and return top_k passages with metadata."""
    global _collection
    if _collection is None:
        logger.warning("retrieve_context called before collection initialization")
        return []

    try:
        where = None
        if user_level:
            where = {"level": user_level.upper()}

        results = _collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        out = []
        for c, m, d in zip(docs, metas, dists):
            out.append({
                "content": c,
                "topic": m.get("topic"),
                "title": m.get("title"),
                "relevance_score": float(1 - d) if d is not None else 0.0
            })

        return out

    except Exception as e:
        logger.error(f"retrieve_context failed: {e}")
        return []

class RAGService:
    def __init__(self, persist_dir: str):
        initialize_chromadb()

    def retrieve_context(self, query: str, user_level: str = None, top_k: int = 3) -> List[Dict[str, Any]]:
        return retrieve_context(query, user_level, top_k)

    def get_collection_stats(self) -> Dict[str, Any]:
        global _collection
        try:
            total = _collection.count() if _collection else 0
            topics = set()
            levels = set()
            if _collection:
                metas = _collection.get(include=["metadatas"]).get("metadatas", [])
                if metas and isinstance(metas, list):
                    flat = metas[0] if isinstance(metas[0], list) else metas
                    for m in flat:
                        t = m.get("topic")
                        l = m.get("level")
                        if t:
                            topics.add(t)
                        if l:
                            levels.add(l)
            return {
                "total_documents": total,
                "topics_covered": list(topics),
                "levels_covered": list(levels),
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"total_documents": 0, "topics_covered": [], "levels_covered": []}


_rag_service = None

def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService(persist_dir=settings.chroma_persist_dir)
    return _rag_service
