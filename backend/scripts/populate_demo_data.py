"""Populate demo data for local development.

This script will:
- Initialize ChromaDB and seed the knowledge collection (if empty)
- Warm the news cache by fetching mock news
- Write a sample `demo_user_context.json` file with portfolio and prediction history

Run: python backend/scripts/populate_demo_data.py
"""
import json
import os
import logging

from backend.services import rag_service, news_service

logger = logging.getLogger(__name__)

DEMO_OUTPUT = os.path.join(os.path.dirname(__file__), "..", "demo_user_context.json")


def main():
    print("Initializing ChromaDB and seeding knowledge (if needed)...")
    ok = rag_service.initialize_chromadb()
    print("Chroma init:", ok)

    print("Warming news cache...")
    news = news_service.fetch_news_feed(limit=6)
    print(f"Fetched {len(news)} news items")

    demo_context = {
        "level": "intermediate",
        "virtual_balance": 100000.0,
        "portfolio": [
            {"symbol": "AAPL", "quantity": 10, "current_price": 150.0, "pnl": 5.2},
            {"symbol": "BTC", "quantity": 0.1, "current_price": 45000.0, "pnl": -1.5}
        ],
        "prediction_history": [
            {"result": "win"}, {"result": "loss"}, {"result": "win"}
        ],
        "learning_progress": {"completed_topics": 5, "total_topics": 20}
    }

    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo_user_context.json"))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(demo_context, f, indent=2)

    print("Wrote demo user context to:", out_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
