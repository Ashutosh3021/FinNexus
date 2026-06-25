"""
FinNexus Bot — Data Schemas
Dataclasses and Pydantic models used across the bot, API, and DB layers.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    ABANDONED = "abandoned"


class QuestionType(str, Enum):
    MCQ_SINGLE = "mcq_single"
    MCQ_MULTIPLE = "mcq_multiple"
    SAQ = "saq"


class AssetClass(str, Enum):
    CRYPTO = "Crypto"
    STOCKS = "Stocks"
    ETFS = "ETFs"
    FUTURES = "Futures"
    COMMODITIES = "Commodities"


# ---------------------------------------------------------------------------
# Question schema
# ---------------------------------------------------------------------------

@dataclass
class Question:
    """A single HITL question served to a user."""

    id: str
    level: int
    type: QuestionType
    question: str
    asset_class: str = ""
    asset_symbol: str = ""
    context: str = ""

    # MCQ fields
    options: List[str] = field(default_factory=list)
    correct_answer: Any = None            # str for single, list[str] for multiple
    word_limit: int = 50                  # SAQ only

    # Metadata set by LLM generator
    difficulty: float = 0.5              # 0-1, informational
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "level": self.level,
            "type": self.type.value,
            "question": self.question,
            "asset_class": self.asset_class,
            "asset_symbol": self.asset_symbol,
            "context": self.context,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "word_limit": self.word_limit,
            "difficulty": self.difficulty,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Question":
        return cls(
            id=data["id"],
            level=data["level"],
            type=QuestionType(data["type"]),
            question=data["question"],
            asset_class=data.get("asset_class", ""),
            asset_symbol=data.get("asset_symbol", ""),
            context=data.get("context", ""),
            options=data.get("options", []),
            correct_answer=data.get("correct_answer"),
            word_limit=data.get("word_limit", 50),
            difficulty=data.get("difficulty", 0.5),
            tags=data.get("tags", []),
        )


# ---------------------------------------------------------------------------
# Answer record
# ---------------------------------------------------------------------------

@dataclass
class AnswerRecord:
    """Stores a user's submitted answer and its evaluation."""

    question_id: str
    question_type: QuestionType
    answer: Any                   # str | list[str]
    score: float                  # 0.0 – 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    is_level_20: bool = False
    feedback: str = ""            # LLM-generated feedback for SAQ

    def to_dict(self) -> Dict:
        return {
            "question_id": self.question_id,
            "question_type": self.question_type.value,
            "answer": self.answer,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
            "is_level_20": self.is_level_20,
            "feedback": self.feedback,
        }


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

@dataclass
class BotSession:
    """In-memory representation of an active user session."""

    user_id: int
    level: int
    questions: List[Question]
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_index: int = 0
    answers: Dict[str, AnswerRecord] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    status: SessionStatus = SessionStatus.ACTIVE

    # ── Computed helpers ──────────────────────────────────────────────────

    @property
    def total_questions(self) -> int:
        return len(self.questions)

    @property
    def is_complete(self) -> bool:
        return self.current_index >= self.total_questions

    @property
    def progress_str(self) -> str:
        return f"{self.current_index}/{self.total_questions}"

    @property
    def average_score(self) -> float:
        if not self.answers:
            return 0.0
        return sum(a.score for a in self.answers.values()) / len(self.answers)

    @property
    def current_question(self) -> Optional[Question]:
        if self.current_index < self.total_questions:
            return self.questions[self.current_index]
        return None

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "level": self.level,
            "status": self.status.value,
            "current_index": self.current_index,
            "total_questions": self.total_questions,
            "progress": self.progress_str,
            "average_score": round(self.average_score, 4),
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


# ---------------------------------------------------------------------------
# API response shapes
# ---------------------------------------------------------------------------

@dataclass
class SessionResponse:
    session_id: str
    level: int
    total_questions: int
    progress: str
    first_question: Optional[Dict] = None
    message: str = ""

    def to_dict(self) -> Dict:
        d = {
            "session_id": self.session_id,
            "level": self.level,
            "total_questions": self.total_questions,
            "progress": self.progress,
            "message": self.message,
        }
        if self.first_question:
            d["first_question"] = self.first_question
        return d


@dataclass
class AnswerResponse:
    status: str                   # "in_progress" | "level_complete"
    score: float
    progress: str
    feedback: str = ""
    next_question: Optional[Dict] = None
    level_result: Optional[Dict] = None

    def to_dict(self) -> Dict:
        d = {
            "status": self.status,
            "score": round(self.score, 4),
            "progress": self.progress,
            "feedback": self.feedback,
        }
        if self.next_question:
            d["next_question"] = self.next_question
        if self.level_result:
            d["level_result"] = self.level_result
        return d


@dataclass
class LevelResult:
    level: int
    score: float
    reward: int
    next_level: int
    level_up: bool
    is_level_20: bool = False
    level_20_bonus: int = 0
    message: str = ""

    def to_dict(self) -> Dict:
        return {
            "level": self.level,
            "score": round(self.score, 4),
            "reward": self.reward,
            "next_level": self.next_level,
            "level_up": self.level_up,
            "is_level_20": self.is_level_20,
            "level_20_bonus": self.level_20_bonus,
            "message": self.message,
        }


@dataclass
class UserStats:
    user_id: int
    total_sessions: int
    completed_levels: List[int]
    total_cash_earned: int
    average_score: float
    proficiency: float
    current_level: int
    total_correct: int
    total_answered: int
    accuracy: float
    best_level_score: float
    recent_activity: List[Dict]

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "total_sessions": self.total_sessions,
            "completed_levels": self.completed_levels,
            "total_cash_earned": self.total_cash_earned,
            "average_score": round(self.average_score, 4),
            "proficiency": round(self.proficiency, 4),
            "current_level": self.current_level,
            "total_correct": self.total_correct,
            "total_answered": self.total_answered,
            "accuracy": round(self.accuracy, 4),
            "best_level_score": round(self.best_level_score, 4),
            "recent_activity": self.recent_activity,
        }
