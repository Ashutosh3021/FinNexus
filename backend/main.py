"""
Main FastAPI application for FinNexus backend.
Startup sequence performs model loading, optional RAG seeding, and prints health.
"""
import logging
from fastapi import FastAPI

from backend.routers.playground import router as playground_router
from backend.routers.portfolio import router as portfolio_router
from backend.routers.news import router as news_router
from backend.routers.education import router as education_router
from backend.routers.advisor import router as advisor_router

logger = logging.getLogger(__name__)

app = FastAPI(title="FinNexus API")


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
