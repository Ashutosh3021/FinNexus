"""
News Router - Fetch news and enrich with ML sentiment/impact scores.
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException

from ..schemas import APIResponse, AnalyzeHeadlineRequest
from ..services import news_service, ml_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/", response_model=APIResponse)
async def get_news(category: str = "all", limit: int = 20) -> APIResponse:
    """Fetch news and run sentiment analysis on each headline."""
    try:
        items = news_service.fetch_news_feed(category=category, limit=limit)

        enriched = []
        for it in items:
            headline = it.get("headline", "")
            try:
                sent = ml_service.analyze_news_sentiment(headline)
                it["sentiment"] = sent.get("sentiment", it.get("sentiment", "neutral"))
                it["impact_score"] = sent.get("impact_score", it.get("impact_score", 5))
                it["sentiment_confidence"] = sent.get("confidence", 0.0)
            except Exception as e:
                logger.warning(f"Sentiment analyze failed for headline: {e}")
                it["sentiment"] = it.get("sentiment", "neutral")
                it["impact_score"] = it.get("impact_score", 5)

            enriched.append(it)

        # Sort by impact_score descending
        enriched = sorted(enriched, key=lambda x: x.get("impact_score", 0), reverse=True)

        return APIResponse(success=True, data={"news": enriched, "count": len(enriched)})

    except Exception as e:
        logger.error(f"Failed to fetch news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=APIResponse)
async def analyze_headline(req: AnalyzeHeadlineRequest) -> APIResponse:
    """Analyze a single headline via ML sentiment analyzer."""
    try:
        res = ml_service.analyze_news_sentiment(req.headline)
        return APIResponse(success=True, data=res)
    except Exception as e:
        logger.error(f"Headline analysis failed: {e}")
        return APIResponse(success=False, error=str(e))
