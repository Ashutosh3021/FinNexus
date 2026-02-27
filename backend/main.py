"""
Main FastAPI application for FinNexus backend.
Startup sequence performs model loading, optional RAG seeding, and prints health.
"""
import logging
from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_cors_origins

from backend.routers.playground import router as playground_router
from backend.routers.portfolio import router as portfolio_router
from backend.routers.news import router as news_router
from backend.routers.education import router as education_router
from backend.routers.advisor import router as advisor_router
from backend.routers import education as education_handlers

logger = logging.getLogger(__name__)

app = FastAPI(title="FinNexus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
  return {"name": "FinNexus API", "version": "1.0.0"}

@app.get("/health")
def health():
  return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    """
    Startup sequence (EXACT order required):
      1. load_all_models()
      2. seed_initial_knowledge() via initialize_chromadb() (only if empty)
      3. print startup health check
    """
    # 1. Load ML models directly from models.ml_loader
    try:
        import models.ml_loader as ml_loader
        ml_loader.load_all_models()
        models_loaded = getattr(ml_loader, "models_loaded", False)
    except Exception as e:
        logger.error(f"Failed to load ML models on startup: {e}")
        models_loaded = False

    # 2. Initialize ChromaDB and seed initial knowledge if empty
    try:
        from backend.services import rag_service
        chroma_ok = rag_service.initialize_chromadb()
        docs_count = 0
        try:
            if getattr(rag_service, "_collection", None) is not None:
                docs_count = rag_service._collection.count()
        except Exception:
            docs_count = -1
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {e}")
        chroma_ok = False
        docs_count = -1

    # 3. Print startup health check
    logger.info("=== Startup Health Check ===")
    logger.info(f"ML models loaded: {models_loaded}")
    logger.info(f"ChromaDB initialized: {chroma_ok}, docs_count={docs_count}")
    logger.info("=============================")


# Include routers
app.include_router(playground_router)
app.include_router(portfolio_router)
app.include_router(news_router)
app.include_router(education_router)
app.include_router(advisor_router)

@app.get("/education/topics")
async def education_topics_alias():
    return await education_handlers.get_topics()

@app.post("/education/ask")
async def education_ask_alias(payload: dict = Body(...)):
    return await education_handlers.ask_concept(payload)

@app.get("/education/lesson/{topic_slug}")
async def education_lesson_alias(topic_slug: str, level: str = Query("BEGINNER")):
    return await education_handlers.get_lesson(topic_slug, level)

@app.post("/education/quiz/submit")
async def education_quiz_submit_alias(payload: dict = Body(...)):
    return await education_handlers.submit_quiz(payload)

@app.get("/education/search")
async def education_search_alias(q: str = Query(...), level: str = Query(None)):
    return await education_handlers.search(q, level)

@app.get("/education/stats")
async def education_stats_alias():
    return await education_handlers.stats()


if __name__ == "__main__":
    import uvicorn
