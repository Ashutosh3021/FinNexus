"""
FinNexus Bot — Configuration
Loads settings from environment variables via python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

_bot_env = Path(__file__).parent / ".env"
_root_env = Path(__file__).parent.parent / ".env"

if _bot_env.exists():
    load_dotenv(_bot_env)
elif _root_env.exists():
    load_dotenv(_root_env)

PROJECT_ROOT = Path(__file__).parent.parent

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# ── LLM (OpenAI-compatible) ───────────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")

# ── RAG / Chroma ──────────────────────────────────────────────────────────────
CHROMA_PERSIST_PATH: Path = Path(
    os.getenv("CHROMA_PERSIST_PATH", str(PROJECT_ROOT / "Data" / "chroma_db"))
)
NEWSAPI_KEY: str = os.getenv("NEWSAPI_KEY", "")

# ── ML Model ──────────────────────────────────────────────────────────────────
MODEL_DIR: Path = Path(os.getenv("MODEL_DIR", str(Path(__file__).parent / "model" / "artifacts")))
MODEL_DIR.mkdir(parents=True, exist_ok=True)

SQLITE_PATH: Path = Path(
    os.getenv("SQLITE_PATH", str(Path(__file__).parent / "model" / "finnexus_dev.db"))
)

# ── Session ───────────────────────────────────────────────────────────────────
SESSION_TIMEOUT_SECONDS: int = int(os.getenv("SESSION_TIMEOUT_SECONDS", "3600"))

# ── Level system (1 → 20) ─────────────────────────────────────────────────────
MAX_LEVEL: int = 20
LEVEL_20: int = 20

LEVEL_REWARDS: dict[int, int] = {
    1: 100,
    2: 20,
    3: 20,
    4: 20,
    5: 50,
    6: 25,
    7: 25,
    8: 30,
    9: 30,
    10: 35,
    11: 35,
    12: 40,
    13: 40,
    14: 45,
    15: 45,
    16: 50,
    17: 50,
    18: 55,
    19: 60,
}
LEVEL_20_BASE_REWARD: int = 20
LEVEL_20_MAX_BONUS: int = 200

LEVEL_UP_THRESHOLD: float = 0.60
LEVEL_DOWN_THRESHOLD: float = 0.30

PROFICIENCY_BREAKPOINTS: list[tuple[float, int]] = [
    (0.05, 1),
    (0.10, 2),
    (0.15, 3),
    (0.20, 4),
    (0.25, 5),
    (0.30, 6),
    (0.35, 7),
    (0.40, 8),
    (0.45, 9),
    (0.50, 10),
    (0.55, 11),
    (0.60, 12),
    (0.65, 13),
    (0.70, 14),
    (0.75, 15),
    (0.80, 16),
    (0.85, 17),
    (0.90, 18),
    (0.95, 19),
    (1.01, 20),
]

MCQ_PER_LEVEL: int = 15
SAQ_PER_LEVEL: int = 4
QUESTIONS_PER_LEVEL: int = MCQ_PER_LEVEL + SAQ_PER_LEVEL

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def level_base_reward(level: int) -> int:
    """Paper-cash base reward for completing a level (before score multiplier)."""
    if level == LEVEL_20:
        return LEVEL_20_BASE_REWARD
    if level in LEVEL_REWARDS:
        return LEVEL_REWARDS[level]
    return max(20, 10 + level * 2)
