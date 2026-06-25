"""
FinNexus Bot — Core Orchestrator
FinnexusBot drives the full HITL session lifecycle:
  start_session → serve_question → submit_answer → finish_level
Wires together: DB, QuestionGenerator, SAQEvaluator, MLModel.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from Bot import config as cfg
from Bot.schemas import (
    AnswerRecord, AnswerResponse, BotSession, LevelResult,
    QuestionType, SessionResponse, SessionStatus, UserStats,
)
from Bot.db import BotDB, create_db
from Bot.llm_generator import LLMClient, MarketContext, QuestionGenerator
from Bot.RAG.retriever import RAGRetriever
from Bot.RAG.evaluator import SAQEvaluator
from Bot.model.main import MLModel
from Bot.context_injector import ContextInjector

logger = logging.getLogger(__name__)


class FinnexusBot:
    """
    Central orchestrator for FinNexus HITL bot sessions.

    Usage::
        bot = FinnexusBot.from_env()
        resp = bot.start_session(user_id=1, level=1)
        resp = bot.submit_answer(user_id=1, answer="RSI")
        stats = bot.get_user_stats(user_id=1)
    """

    def __init__(
        self,
        db: BotDB,
        question_generator: QuestionGenerator,
        saq_evaluator: SAQEvaluator,
        ml_model: MLModel,
    ):
        self._db = db
        self._qgen = question_generator
        self._evaluator = saq_evaluator
        self._ml = ml_model
        self._context_injector = ContextInjector(db=db)
        # In-memory session cache  {user_id: BotSession}
        self._sessions: Dict[int, BotSession] = {}

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "FinnexusBot":
        """Build a fully wired FinnexusBot from environment / config defaults."""
        db = create_db(
            url=cfg.SUPABASE_URL,
            key=cfg.SUPABASE_KEY,
            sqlite_path=str(cfg.MODEL_DIR.parent / "finnexus_dev.db"),
        )
        llm = LLMClient(
            provider=cfg.LLM_PROVIDER,
            api_key=cfg.LLM_API_KEY,
            model=cfg.LLM_MODEL,
            base_url=cfg.LLM_BASE_URL,
        )
        qgen = QuestionGenerator(llm_client=llm)
        retriever = RAGRetriever()
        evaluator = SAQEvaluator(retriever=retriever, llm_client=llm if llm.available else None)
        ml = MLModel(model_dir=cfg.MODEL_DIR)
        return cls(db=db, question_generator=qgen, saq_evaluator=evaluator, ml_model=ml)

    # ── Session management ────────────────────────────────────────────────────

    def start_session(
        self,
        user_id: int,
        level: int,
        asset_context: str = "",
        force_new: bool = False,
        market_context: Optional[MarketContext] = None,
    ) -> SessionResponse:
        """
        Start (or resume) a HITL session for user_id at the given level.
        Returns a SessionResponse with the first question.
        """
        # Expire stale in-memory session
        existing = self._sessions.get(user_id)
        if existing and not force_new:
            age = (datetime.now() - existing.last_activity).total_seconds()
            if age > cfg.SESSION_TIMEOUT_SECONDS:
                self._close_session(user_id, SessionStatus.TIMED_OUT)
                existing = None

        if existing and not force_new:
            session = existing
            logger.info("FinnexusBot: resuming session %s for user %d", session.session_id, user_id)
        else:
            # Build market context if not provided
            if market_context is None:
                market_context = self._context_injector.build_context(user_id, level)

            questions = self._qgen.generate(
                level=level,
                user_id=user_id,
                context=market_context,
                asset_context=asset_context,
            )
            session = BotSession(user_id=user_id, level=level, questions=questions)
            self._sessions[user_id] = session
            self._db.create_session(session.session_id, user_id, level)
            logger.info(
                "FinnexusBot: new session %s for user %d level %d (%d questions)",
                session.session_id, user_id, level, len(questions),
            )

        first_q = session.current_question
        return SessionResponse(
            session_id=session.session_id,
            level=session.level,
            total_questions=session.total_questions,
            progress=session.progress_str,
            first_question=first_q.to_dict() if first_q else None,
            message=f"Level {level} session started. {session.total_questions} questions.",
        )

    def get_current_question(self, user_id: int) -> Optional[Dict]:
        """Return the current question dict for an active session."""
        session = self._get_session(user_id)
        if session is None:
            return None
        q = session.current_question
        return q.to_dict() if q else None

    # ── Answer submission ─────────────────────────────────────────────────────

    def submit_answer(self, user_id: int, answer: Any) -> AnswerResponse:
        """
        Score the current question's answer, advance the session pointer,
        persist the record, and return an AnswerResponse.
        If the level is complete, triggers finish_level internally.
        """
        session = self._get_session(user_id)
        if session is None:
            raise ValueError(f"No active session for user {user_id}. Call start_session first.")

        if session.is_complete:
            raise ValueError("Session already complete. Start a new session.")

        question = session.current_question
        is_level_20 = (session.level == 20)

        # ── Score ─────────────────────────────────────────────────────────────
        score, feedback = self._score_answer(question, answer)

        record = AnswerRecord(
            question_id=question.id,
            question_type=question.type,
            answer=answer,
            score=score,
            is_level_20=is_level_20,
            feedback=feedback,
        )
        session.answers[question.id] = record
        session.current_index += 1
        session.last_activity = datetime.now()

        # ── Persist ───────────────────────────────────────────────────────────
        self._db.save_answer(
            user_id=user_id,
            session_id=session.session_id,
            question_id=question.id,
            question_type=question.type.value,
            answer=answer,
            score=score,
            is_level_20=is_level_20,
            feedback=feedback,
        )
        self._db.update_session(session.session_id, current_question=session.current_index)

        # ── Check completion ──────────────────────────────────────────────────
        if session.is_complete:
            level_result = self._finish_level(user_id, session)
            return AnswerResponse(
                status="level_complete",
                score=score,
                progress=session.progress_str,
                feedback=feedback,
                level_result=level_result.to_dict(),
            )

        next_q = session.current_question
        return AnswerResponse(
            status="in_progress",
            score=score,
            progress=session.progress_str,
            feedback=feedback,
            next_question=next_q.to_dict() if next_q else None,
        )

    # ── Level completion ──────────────────────────────────────────────────────

    def _finish_level(self, user_id: int, session: BotSession) -> LevelResult:
        """Compute reward, update DB, trigger ML training, close session."""
        avg_score = session.average_score
        level = session.level
        is_level_20 = (level == 20)

        # Reward calculation
        base_reward = cfg.LEVEL_REWARDS.get(level, cfg.LEVEL_20_BASE_REWARD)
        level_20_bonus = 0
        if is_level_20:
            level_20_bonus = int(avg_score * cfg.LEVEL_20_MAX_BONUS)
            reward = base_reward + level_20_bonus
        else:
            reward = int(base_reward * avg_score)  # scale reward by performance

        # Level progression
        level_up = avg_score >= cfg.LEVEL_UP_THRESHOLD
        level_down = avg_score < cfg.LEVEL_DOWN_THRESHOLD and level > 1

        if level_up and not is_level_20:
            next_level = min(level + 1, 5)
        elif level_down:
            next_level = max(level - 1, 1)
        else:
            next_level = level

        # Build message
        if level_up:
            msg = f"Great work! Score {avg_score:.0%} — advancing to Level {next_level}."
        elif level_down:
            msg = f"Score {avg_score:.0%} — dropping to Level {next_level} for more practice."
        else:
            msg = f"Score {avg_score:.0%} — stay at Level {level}. Keep practising!"
        if is_level_20:
            msg += f" Bonus earned: ${level_20_bonus}."

        # Persist progress and paper cash
        self._db.save_level_progress(
            user_id=user_id, level=level, score=avg_score,
            reward=reward, next_level_unlocked=level_up,
        )
        self._db.add_paper_cash(user_id, reward)

        # ML online update (non-blocking)
        try:
            self._ml.train_on_answers(
                user_id=user_id,
                answers=session.answers,
                market_outcome=avg_score,
                level=level,
            )
        except Exception as exc:
            logger.warning("FinnexusBot: ML train_on_answers failed: %s", exc)

        # Close session
        session.status = SessionStatus.COMPLETED
        self._db.close_session(session.session_id, status="completed")
        del self._sessions[user_id]

        logger.info(
            "FinnexusBot: user %d finished level %d | score=%.3f | reward=%d | next=%d",
            user_id, level, avg_score, reward, next_level,
        )
        return LevelResult(
            level=level, score=avg_score, reward=reward,
            next_level=next_level, level_up=level_up,
            is_level_20=is_level_20, level_20_bonus=level_20_bonus,
            message=msg,
        )

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _score_answer(self, question, answer: Any) -> tuple[float, str]:
        """Return (score 0-1, feedback str) for the given question + answer."""
        qtype = question.type
        subtype = question.tags[0] if question.tags else ""

        if qtype == QuestionType.SAQ:
            result = self._evaluator.evaluate(
                question=question.question,
                answer=str(answer),
                word_limit=question.word_limit,
                context_hint=question.context,
                question_subtype=subtype,
            )
            return result["score"], result.get("feedback", "")

        if qtype == QuestionType.MCQ_SINGLE:
            # Scenario/Impact MCQs have no "correct" answer (correct_answer = None)
            # All options are valid trading philosophies
            if question.correct_answer is None:
                # Award base engagement score — all choices are legitimate
                return 0.7, (
                    "Choice noted. All options represent valid trading styles. "
                    "No single 'correct' answer. Consider adding reasoning in future."
                )
            # Traditional MCQ with a correct answer (legacy/trivia — should be rare now)
            correct = question.correct_answer
            is_correct = str(answer).strip().lower() == str(correct).strip().lower()
            score = 1.0 if is_correct else 0.0
            fb = "Correct!" if is_correct else f"Incorrect. The answer is: {correct}"
            return score, fb

        if qtype == QuestionType.MCQ_MULTIPLE:
            correct_set = {str(c).strip().lower() for c in (question.correct_answer or [])}
            if not correct_set:
                return 0.5, "No correct answers defined."
            ans_set = {str(a).strip().lower() for a in (answer if isinstance(answer, list) else [answer])}
            if not ans_set:
                return 0.0, "No answer provided."
            precision = len(ans_set & correct_set) / len(ans_set)
            recall = len(ans_set & correct_set) / len(correct_set)
            score = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
            fb = f"F1 score: {score:.0%}. Correct answers: {', '.join(question.correct_answer)}"
            return round(score, 4), fb

        return 0.0, "Unknown question type."

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_user_stats(self, user_id: int) -> UserStats:
        """Aggregate DB history into a UserStats object."""
        history = self._db.get_user_history(user_id, limit=500)
        progress = self._db.get_user_progress(user_id)
        cash = self._db.get_paper_cash(user_id)

        total = len(history)
        correct = sum(1 for h in history if h.get("score", 0) >= 0.5)
        avg_score = sum(h.get("score", 0) for h in history) / total if total else 0.0
        accuracy = correct / total if total else 0.0

        completed_levels = sorted({p["level_completed"] for p in progress})
        total_sessions = len({p.get("session_id", i) for i, p in enumerate(progress)})
        best_score = max((p.get("score", 0) for p in progress), default=0.0)
        current_level = max(completed_levels, default=1)

        # Simple proficiency: normalised avg score
        proficiency = min(avg_score * (1 + current_level / 5), 1.0)

        return UserStats(
            user_id=user_id,
            total_sessions=total_sessions,
            completed_levels=completed_levels,
            total_cash_earned=cash,
            average_score=avg_score,
            proficiency=proficiency,
            current_level=current_level,
            total_correct=correct,
            total_answered=total,
            accuracy=accuracy,
            best_level_score=best_score,
            recent_activity=history[:10],
        )

    def get_ml_stats(self) -> Dict:
        return self._ml.get_stats()

    def predict_improvement(self, user_id: int) -> float:
        session = self._sessions.get(user_id)
        if session is None:
            return 0.0
        return self._ml.predict_improvement(session.answers, session.level)

    # ── Proficiency assessment (onboarding) ───────────────────────────────────

    def assess_starting_level(self, proficiency_score: float) -> int:
        """Map a proficiency score (0-1) to a recommended starting level."""
        for threshold, level in cfg.PROFICIENCY_BREAKPOINTS:
            if proficiency_score < threshold:
                return level
        return 5

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_session(self, user_id: int) -> Optional[BotSession]:
        session = self._sessions.get(user_id)
        if session is None:
            return None
        age = (datetime.now() - session.last_activity).total_seconds()
        if age > cfg.SESSION_TIMEOUT_SECONDS:
            self._close_session(user_id, SessionStatus.TIMED_OUT)
            return None
        return session

    def _close_session(self, user_id: int, status: SessionStatus) -> None:
        session = self._sessions.pop(user_id, None)
        if session:
            self._db.close_session(session.session_id, status=status.value)
            logger.info("FinnexusBot: closed session %s with status %s", session.session_id, status.value)
