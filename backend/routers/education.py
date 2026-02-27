"""
Education Router - endpoints for RAG-powered lessons and quizzes.
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query

from ..schemas import APIResponse
from ..services.rag_service import get_rag_service
from ..services import market_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/education", tags=["education"])

# Try to import gemini_service; fallback to simple stub
try:
    from ..services import gemini_service
    _gemini = gemini_service
except Exception:
    _gemini = None


@router.post("/ask", response_model=APIResponse)
async def ask_concept(payload: Dict[str, Any]) -> APIResponse:
    """Ask a question and receive RAG + Gemini lesson content.

    Expects: { query: str, user_level: str, include_market_data: bool }
    """
    try:
        query = payload.get("query", "")
        user_level = payload.get("user_level", "BEGINNER")
        include_market = bool(payload.get("include_market_data", False))

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        rag = get_rag_service()
        chunks = rag.retrieve_context(query, user_level, top_k=3)

        market_data = None
        sources = []
        if include_market:
            # attempt to extract an asset symbol from query (simple heuristic)
            tokens = query.split()
            symbol = None
            for t in tokens:
                if t.upper() in ["AAPL", "BTC-USD", "BTC", "ETH", "SPY"]:
                    symbol = t.upper()
                    break
            if symbol:
                # fetch latest price
                prices = market_service.get_current_prices([symbol if "-" in symbol else symbol])
                market_data = {"symbol": symbol, "price": prices.get(symbol)}

        for c in chunks:
            if c.get("source"):
                sources.append(c.get("source"))

        # Call Gemini teach_concept if available
        if _gemini and hasattr(_gemini, "teach_concept"):
            lesson = _gemini.teach_concept(query=query, user_level=user_level, chunks=chunks, market_data=market_data)
        else:
            # Fallback simple synthesis
            explanation = "\n\n".join([c.get("content", "") for c in chunks]) or "An overview of the topic."
            lesson = {
                "explanation": explanation,
                "analogy": "Think of investing like planting a garden — diversify seeds across beds.",
                "market_example": f"Latest price for {market_data['symbol']}: {market_data['price']}" if market_data else "",
                "visual_data": None,
                "key_takeaway": "Diversify, manage risk, and align with time horizon.",
                "follow_up_questions": ["Would you like a quiz?", "Show me an example trade?"],
                "related_playground_scenario": "Use the playground to test this concept.",
                "sources": list(dict.fromkeys(sources))
            }

        return APIResponse(success=True, data=lesson)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ask concept failed: {e}")
        return APIResponse(success=False, error=str(e))


@router.get("/topics", response_model=APIResponse)
async def get_topics():
    """Get all available topics grouped by level."""
    try:
        rag = get_rag_service()
        stats = rag.get_collection_stats()
        # Return topics grouped by level
        topics = {}
        for lvl in stats.get("levels_covered", []):
            topics[lvl] = []

        # iterate over metadatas to build topic lists
        metas = rag._collection.get(include=["metadatas"]).get("metadatas", [])
        if metas and isinstance(metas, list):
            flat = metas[0] if isinstance(metas[0], list) else metas
            seen = set()
            for m in flat:
                lvl = m.get("level", "BEGINNER")
                title = m.get("title", "")
                if title and title not in seen:
                    topics.setdefault(lvl, []).append({"title": title, "topic": m.get("topic")})
                    seen.add(title)

        return APIResponse(success=True, data={"topics": topics})
    except Exception as e:
        logger.error(f"Get topics failed: {e}")
        return APIResponse(success=False, error=str(e))


@router.get("/lesson/{topic_slug}", response_model=APIResponse)
async def get_lesson(topic_slug: str, level: str = Query("BEGINNER")):
    """Fetch lesson for specific topic at a given level."""
    try:
        rag = get_rag_service()
        # retrieve by topic across levels, prefer requested level
        chunks = rag.retrieve_context(topic_slug, level, top_k=5)
        content = "\n\n".join([c.get("content", "") for c in chunks])
        return APIResponse(success=True, data={"topic": topic_slug, "level": level, "content": content, "sources": [c.get("source") for c in chunks]})
    except Exception as e:
        logger.error(f"Get lesson failed: {e}")
        return APIResponse(success=False, error=str(e))


@router.post("/quiz/submit", response_model=APIResponse)
async def submit_quiz(payload: Dict[str, Any]):
    """Submit a quiz answer and get feedback."""
    try:
        topic = payload.get("topic")
        question = payload.get("question")
        user_answer = payload.get("user_answer")
        correct_answer = payload.get("correct_answer")

        is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()

        if _gemini and hasattr(_gemini, "explain_quiz_answer"):
            explanation = _gemini.explain_quiz_answer(question=question, user_answer=user_answer, correct_answer=correct_answer)
        else:
            explanation = "Correct." if is_correct else f"Incorrect. The correct answer is: {correct_answer}."

        xp = 10 if is_correct else 2
        return APIResponse(success=True, data={"is_correct": is_correct, "explanation": explanation, "xp_earned": xp})
    except Exception as e:
        logger.error(f"Quiz submit failed: {e}")
        return APIResponse(success=False, error=str(e))


@router.get("/search", response_model=APIResponse)
async def search(q: str = Query(...), level: str = Query(None)):
    """Semantic search across all topics."""
    try:
        rag = get_rag_service()
        results = rag.retrieve_context(q, level, top_k=5)
        # Return previews
        out = []
        for r in results:
            preview = r.get("content", "")[:200]
            out.append({"title": r.get("topic"), "preview": preview, "score": r.get("relevance_score")})
        return APIResponse(success=True, data={"results": out})
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return APIResponse(success=False, error=str(e))


@router.get("/stats", response_model=APIResponse)
async def stats():
    """Get ChromaDB collection stats (admin/debug)."""
    try:
        rag = get_rag_service()
        s = rag.get_collection_stats()
        return APIResponse(success=True, data=s)
    except Exception as e:
        logger.error(f"Stats failed: {e}")
        return APIResponse(success=False, error=str(e))
