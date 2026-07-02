"""
Chunk 2 verification — Bot orchestrator + RAG pipeline.
Run: python -m Scripts.verify_chunk2
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Bot import config as cfg
from Bot.main import FinnexusBot
from Bot.schemas import QuestionType


def _auto_answer(bot: FinnexusBot, user_id: int) -> dict:
    """Complete all questions in the active session."""
    last_result = None
    while True:
        q = bot.get_current_question(user_id)
        if q is None:
            break
        qtype = q.get("type", "")
        if qtype == QuestionType.SAQ.value:
            ans = (
                "I would reduce equity exposure by 15%, add gold hedge, "
                "set stop-loss below support because macro risk signals contraction."
            )
        elif qtype == QuestionType.MCQ_MULTIPLE.value:
            opts = q.get("options") or []
            ans = opts[:2] if opts else ["A", "B"]
        else:
            opts = q.get("options") or []
            ans = opts[0] if opts else "Hold and reassess with trailing stop"
        last_result = bot.submit_answer(user_id, ans)
        if last_result.status == "level_complete":
            break

    if last_result is None:
        raise RuntimeError("Session did not produce any answers")
    return last_result.to_dict()


def main() -> None:
    print("=" * 60)
    print("CHUNK 2 VERIFICATION")
    print("=" * 60)

    print("\n--- Pre-flight ---")
    print(f"  Chroma path: {cfg.CHROMA_PERSIST_PATH}")
    print(f"  LLM provider: {cfg.LLM_PROVIDER} (key set: {bool(cfg.LLM_API_KEY and cfg.LLM_API_KEY != 'your_api_key_here')})")

    bot = FinnexusBot.from_env(ensure_rag=True)

    print("\n--- RAG ingestion stats ---")
    rag_stats = bot._retriever.stats()
    print(json.dumps(rag_stats, indent=2))

    print("\n--- RAG retrieval sample ---")
    market_ctx = bot.retrieve_context("Bitcoin price trend volatility", "market_data")
    news_ctx = bot.retrieve_context("Federal Reserve interest rates", "news_events")
    theory_ctx = bot.retrieve_context("risk management stop loss", "trading_theories")
    print("  market:", json.dumps(market_ctx, indent=2))
    print("  news:", json.dumps(news_ctx, indent=2)[:600], "...")
    print("  theory:", json.dumps(theory_ctx, indent=2)[:400], "...")

    user_id = 88001
    bot.update_user_profile(user_id, name="Chunk2 Tester", email="chunk2@test.local")

    levels_to_run = [1, 2, 3]
    for level in levels_to_run:
        profile = bot.get_user_profile(user_id)
        play_level = profile.get("current_level", level)
        if isinstance(play_level, int) and play_level > level:
            play_level = level
        print(f"\n--- Level {play_level} session ---")
        start = bot.start_session(user_id=user_id, level=play_level, force_new=True)
        print(f"  session_id: {start.session_id}")
        print(f"  total_questions: {start.total_questions}")
        result = _auto_answer(bot, user_id)
        print(f"  completed: status={result.get('status')} reward={result.get('level_result', {}).get('reward')}")

    print("\n--- Session state ---")
    state = bot.get_session_state(user_id)
    print(json.dumps(state, indent=2, default=str) if state else "  (no active session — expected)")

    print("\n--- Level progression log ---")
    for entry in bot.get_progression_log():
        print(f"  {entry}")

    print("\n--- Final user profile ---")
    print(json.dumps(bot.get_user_profile(user_id), indent=2, default=str))

    print("\n=== CHUNK 2 VERIFY OK ===")


if __name__ == "__main__":
    main()
