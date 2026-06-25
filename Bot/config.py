"""
FinNexus Bot — Configuration
Loads settings from environment variables via python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from Bot/ directory or project root, whichever exists first
_bot_env = Path(__file__).parent / ".env"
_root_env = Path(__file__).parent.parent / ".env"

if _bot_env.exists():
    load_dotenv(_bot_env)
elif _root_env.exists():
    load_dotenv(_root_env)


# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# ── LLM (OpenAI-compatible) ────────────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")        # "openai" | "groq" | "ollama"
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")              # For Ollama / Groq

# ── ML Model ─────────────────────────────────────────────────────────────────
MODEL_DIR: Path = Path(os.getenv("MODEL_DIR", str(Path(__file__).parent / "model" / "artifacts")))
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ── Session ───────────────────────────────────────────────────────────────────
SESSION_TIMEOUT_SECONDS: int = int(os.getenv("SESSION_TIMEOUT_SECONDS", "3600"))  # 1 hour

# ── Reward Table ─────────────────────────────────────────────────────────────
LEVEL_REWARDS: dict[int, int] = {
    1: 100,
    2: 20,
    3: 20,
    4: 20,
    5: 50,
}
LEVEL_20_BASE_REWARD: int = 20
LEVEL_20_MAX_BONUS: int = 200

# ── Score Thresholds ──────────────────────────────────────────────────────────
LEVEL_UP_THRESHOLD: float = 0.60    # avg score needed to advance
LEVEL_DOWN_THRESHOLD: float = 0.30  # avg score below which user drops a level

# Proficiency → starting level breakpoints
PROFICIENCY_BREAKPOINTS: list[tuple[float, int]] = [
    (0.30, 1),
    (0.50, 2),
    (0.65, 3),
    (0.80, 4),
    (1.01, 5),   # catch-all upper bound
]

# ── Questions per level ───────────────────────────────────────────────────────
MCQ_PER_LEVEL: int = 15
SAQ_PER_LEVEL: int = 4
QUESTIONS_PER_LEVEL: int = MCQ_PER_LEVEL + SAQ_PER_LEVEL  # 19

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
