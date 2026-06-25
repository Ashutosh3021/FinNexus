"""
FinNexus Bot — Core Orchestrator  (v3 — RAG + LLM + HITL Features)
====================================================================
The single entry point for all bot logic. Backend/main.py calls only this.

THE CHAIN (executed in order per session):
  1. get_slim_context(user_id, level)   → context_injector  → slim dict
  2. generate_questions(context)        → llm_generator     → 19 questions
  3. evaluate_answers(answers, context) → RAG/evaluator     → scores
  4. extract_features(answers, scores)  → HITL signals      → ML feature dict
  5. update_user(user_id, scores, feats)→ DB + ML update

HITL features extracted (step 4):
  buys_on_bad_news      bool   — chose to buy/add on negative news
  sells_on_volatility   bool   — chose to sell/exit when VIX is elevated
  prefers_defensive     bool   — chose hedging/conservative option majority
  risk_score            float  — 0-1 derived from option choice profile
  decision_speed        float  — avg seconds per question (timing signal)
  accuracy_vs_rag       float  — answer alignment with RAG-suggested action

Async support: all 5 pipeline steps are async-compatible.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from Bot import config as cfg
from Bot.schemas import (
    AnswerRecord, AnswerResponse, BotSession, LevelResult,
    QuestionType, SessionResponse, SessionStatus, UserStats,
)
from Bot.db import BotDB, create_db
from Bot.llm_generator import LLMClient, MarketContext, QuestionGenerator, get_llm_client
from Bot.RAG.retriever import RAGRetriever
from Bot.RAG.evaluator import SAQEvaluator
from Bot.scoring import AnswerScorer, SessionScore
from Bot.model.main import MLModel, extract_features
from Bot.context_injector import ContextInjector

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HITL feature extraction
# ---------------------------------------------------------------------------

# Keywords in question text/options that signal "bad news" context
_BAD_NEWS_SIGNALS = {
    "hack", "miss", "drop", "fall", "decline", "crash", "cut", "downgrade",
    "warning", "weak", "below", "contraction", "recession", "loss", "deficit",
}

# Keywords in option text that indicate a buy/add action
_BUY_OPTION_SIGNALS = {
    "buy more", "add to", "buy the dip", "accumulate", "deploy", "enter",
    "buy immediately",
}

# Keywords in option text that indicate selling on volatility
_SELL_VOL_SIGNALS = {
    "sell", "exit", "close", "cut loss", "reduce", "scale out",
    "sell all", "sell immediately",
}

# Keywords in option text that indicate defensive/hedging preference
_DEFENSIVE_SIGNALS = {
    "hedge", "protect", "stop-loss", "puts", "straddle", "collar",
    "hold and reassess", "wait", "do nothing", "trailing stop",
}


def extract_hitl_features(
    questions: List[Any],
    answers: Dict[str, AnswerRecord],
    session_score: SessionScore,
    question_timings: Dict[str, float],
) -> Dict[str, Any]:
    """
    Extract HITL behavioural signals from a completed session.

    Args:
        questions:       List of Question objects from the session.
        answers:         {question_id: AnswerRecord} from BotSession.
        session_score:   SessionScore aggregate from AnswerScorer.
        question_timings:{question_id: elapsed_seconds} recorded during session.

    Returns slim feature dict suitable for ML model and API responses.
    """
    buys_on_bad_news_count = 0
    bad_news_questions = 0
    sells_on_vol_count = 0
    vol_questions = 0
    defensive_count = 0
    mcq_count = 0
    risk_scores: List[float] = []

    # Build question lookup
    q_map: Dict[str, Any] = {q.id: q for q in questions}

    for q_id, record in answers.items():
        q = q_map.get(q_id)
        if q is None:
            continue

        # Only MCQ questions carry option-based signals
        if q.type != QuestionType.MCQ_SINGLE:
            continue
        mcq_count += 1

        # Resolve chosen option text
        answer_val = record.answer
        chosen_text = ""
        if isinstance(answer_val, int) and q.options and 0 <= answer_val < len(q.options):
            chosen_text = q.options[answer_val].lower()
        elif isinstance(answer_val, str):
            chosen_text = answer_val.lower()

        # Resolve chosen option index (0-4) for risk_score
        option_idx = _resolve_option_index(answer_val, q.options)

        # --- buys_on_bad_news ---
        q_text_lower = (q.question or "").lower()
        has_bad_news = any(w in q_text_lower for w in _BAD_NEWS_SIGNALS)
        if has_bad_news:
            bad_news_questions += 1
            if any(sig in chosen_text for sig in _BUY_OPTION_SIGNALS):
                buys_on_bad_news_count += 1

        # --- sells_on_volatility ---
        vix_context = "vix" in q_text_lower or "volatil" in q_text_lower or "volatile" in q_text_lower
        if vix_context:
            vol_questions += 1
            if any(sig in chosen_text for sig in _SELL_VOL_SIGNALS):
                sells_on_vol_count += 1

        # --- prefers_defensive ---
        if any(sig in chosen_text for sig in _DEFENSIVE_SIGNALS):
            defensive_count += 1

        # --- risk_score per option ---
        # Option A (idx 0) = most aggressive = risk 0.1
        # Option E (idx 4) = most hedged = risk 0.9
        if option_idx >= 0:
            risk_scores.append(option_idx * 0.2 + 0.1)

    # Aggregate booleans
    buys_on_bad_news = (
        buys_on_bad_news_count >= max(1, bad_news_questions // 2)
        if bad_news_questions > 0 else False
    )
    sells_on_volatility = (
        sells_on_vol_count >= max(1, vol_questions // 2)
        if vol_questions > 0 else False
    )
    prefers_defensive = (
        defensive_count >= max(1, mcq_count // 3)
        if mcq_count > 0 else False
    )
    risk_score = float(sum(risk_scores) / len(risk_scores)) if risk_scores else 0.5

    # --- decision_speed ---
    if question_timings:
        speeds = list(question_timings.values())
        avg_speed = sum(speeds) / len(speeds)
        # Normalise: <10s = 1.0 (fast), >120s = 0.0 (slow)
        decision_speed = float(max(0.0, min(1.0, 1.0 - (avg_speed - 10) / 110)))
    else:
        decision_speed = 0.5

    # --- accuracy_vs_rag ---
    # Proxy: SAQEvaluator scores reflect RAG alignment when method != "mcq_selection"
    if session_score.question_results:
        rag_aligned = [
            r.total / 100.0
            for r in session_score.question_results
            if r.question_type in ("strategy_saq", "risk_saq")
        ]
        accuracy_vs_rag = float(sum(rag_aligned) / len(rag_aligned)) if rag_aligned else (
            session_score.overall_score / 100.0
        )
    else:
        accuracy_vs_rag = 0.0

    return {
        "buys_on_bad_news":      buys_on_bad_news,
        "sells_on_volatility":   sells_on_volatility,
        "prefers_defensive":     prefers_defensive,
        "risk_score":            round(risk_score, 4),
        "decision_speed":        round(decision_speed, 4),
        "accuracy_vs_rag":       round(accuracy_vs_rag, 4),
    }


def _resolve_option_index(answer: Any, options: List[str]) -> int:
    """Return 0-based option index from answer value. -1 if unresolvable."""
    if isinstance(answer, int) and 0 <= answer <= 4:
        return answer
    if isinstance(answer, str):
        upper = answer.strip().upper()
        if upper in "ABCDE" and len(upper) == 1:
            return "ABCDE".index(upper)
        # Try matching against option text
        if options:
            for i, opt in enumerate(options):
                if answer.strip().lower() in opt.lower():
                    return i
    return -1


# ---------------------------------------------------------------------------
# Pipeline steps (each a distinct async-compatible function)
# ---------------------------------------------------------------------------

async def get_slim_context(
    injector: ContextInjector,
    user_id: int,
    level: int,
    force_refresh: bool = False,
) -> Dict:
    """
    Step 1 — fetch slim context dict from ContextInjector.
    Runs the blocking I/O in a thread so it's safe in async contexts.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: injector.get_slim_context(
            user_id=user_id, level=level, force_refresh=force_refresh
        ),
    )


async def generate_questions(
    qgen: QuestionGenerator,
    context: MarketContext,
    level: int,
    user_id: int,
) -> List[Any]:
    """
    Step 2 — generate 19 questions via LLM or template fallback.
    LLM calls are blocking; run in executor to stay non-blocking.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: qgen.generate(level=level, user_id=user_id, context=context),
    )


async def evaluate_answers(
    evaluator: SAQEvaluator,
    scorer: AnswerScorer,
    questions: List[Any],
    answers: Dict[str, AnswerRecord],
    user_id: int,
    level: int,
) -> SessionScore:
    """
    Step 3 — evaluate all answers using RAG evaluator + AnswerScorer.
    Returns a SessionScore with dimension breakdowns.
    """
    loop = asyncio.get_event_loop()

    def _run() -> SessionScore:
        scorer.reset()
        q_map = {q.id: q for q in questions}
        for q_id, record in answers.items():
            q = q_map.get(q_id)
            if q is None:
                continue
            scorer.score_answer(q, record.answer)
        return scorer.session_summary(user_id=user_id, level=level)

    return await loop.run_in_executor(None, _run)


async def extract_features_step(
    questions: List[Any],
    answers: Dict[str, AnswerRecord],
    session_score: SessionScore,
    question_timings: Dict[str, float],
) -> Dict[str, Any]:
    """
    Step 4 — extract HITL behavioural features from the completed session.
    Pure CPU work; run in executor for async compatibility.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: extract_hitl_features(questions, answers, session_score, question_timings),
    )


async def update_user(
    db: BotDB,
    ml: MLModel,
    user_id: int,
    level: int,
    avg_score: float,
    reward: int,
    level_up: bool,
    answers: Dict[str, AnswerRecord],
    hitl_features: Dict[str, Any],
) -> None:
    """
    Step 5 — persist progress to DB and trigger async ML update.
    DB writes run in executor; ML training is fire-and-forget.
    """
    loop = asyncio.get_event_loop()

    await loop.run_in_executor(
        None,
        lambda: db.save_level_progress(
            user_id=user_id,
            level=level,
            score=avg_score,
            reward=reward,
            next_level_unlocked=level_up,
        ),
    )
    await loop.run_in_executor(
        None,
        lambda: db.add_paper_cash(user_id, reward),
    )

    # ML update is non-critical — fire and forget in background thread
    def _ml_update() -> None:
        try:
            ml.train_on_answers(
                user_id=user_id,
                answers=answers,
                market_outcome=avg_score,
                level=level,
            )
        except Exception as exc:
            logger.warning("update_user: ML train failed: %s", exc)

    loop.run_in_executor(None, _ml_update)


# ---------------------------------------------------------------------------
# FinnexusBot orchestrator
# ---------------------------------------------------------------------------

class FinnexusBot:
    """
    Central orchestrator for FinNexus HITL bot sessions.

    Backend/main.py is the only caller. All LLM, RAG, DB, and ML
    interactions go through this class — never directly from Backend.

    Sync API (for FastAPI compatibility):
        resp  = bot.start_session(user_id, level)
        resp  = bot.submit_answer(user_id, answer)
        stats = bot.get_user_stats(user_id)

    Async pipeline (exposed for async callers or internal use):
        session_id, questions = await bot.async_start_session(user_id, level)
        result = await bot.async_submit_answers(session_id, answers)
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
        self._scorer = AnswerScorer(llm_client=question_generator.llm)

        # In-memory session cache  {user_id: BotSession}
        self._sessions: Dict[int, BotSession] = {}
        # Question timing tracker {session_id: {question_id: start_time}}
        self._q_start_times: Dict[str, Dict[str, float]] = {}
        # Timing results per session {session_id: {question_id: elapsed_secs}}
        self._q_timings: Dict[str, Dict[str, float]] = {}

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_env(cls) -> "FinnexusBot":
        """Build a fully wired FinnexusBot from environment / config defaults."""
        db = create_db(
            url=cfg.SUPABASE_URL,
            key=cfg.SUPABASE_KEY,
            sqlite_path=str(cfg.MODEL_DIR.parent / "finnexus_dev.db"),
        )
        llm = get_llm_client()
        qgen = QuestionGenerator(llm_client=llm)
        retriever = RAGRetriever()
        evaluator = SAQEvaluator(retriever=retriever, llm_client=llm if llm.available else None)
        ml = MLModel(model_dir=cfg.MODEL_DIR)
        return cls(db=db, question_generator=qgen, saq_evaluator=evaluator, ml_model=ml)


    # =========================================================================
    # Async pipeline API  (Backend calls these directly for async endpoints)
    # =========================================================================

    async def async_start_session(
        self,
        user_id: int,
        level: int = 1,
        force_new: bool = False,
    ) -> Tuple[str, List[Dict]]:
        """
        Async entry point: Step 1 + Step 2.

        Returns (session_id, list_of_question_dicts).
        Exposed to Backend as POST /v2/session/start.
        """
        # Expire stale session
        existing = self._sessions.get(user_id)
        if existing and not force_new:
            age = (datetime.now() - existing.last_activity).total_seconds()
            if age > cfg.SESSION_TIMEOUT_SECONDS:
                self._close_session(user_id, SessionStatus.TIMED_OUT)
                existing = None

        if existing and not force_new:
            session = existing
            logger.info("async_start_session: resuming %s for user %d", session.session_id, user_id)
        else:
            # Step 1: get slim context
            slim = await get_slim_context(self._context_injector, user_id, level)
            market_ctx = self._context_injector.build_context(user_id, level)

            # Step 2: generate questions
            questions = await generate_questions(self._qgen, market_ctx, level, user_id)

            session = BotSession(user_id=user_id, level=level, questions=questions)
            self._sessions[user_id] = session
            self._q_start_times[session.session_id] = {}
            self._q_timings[session.session_id] = {}

            self._db.create_session(session.session_id, user_id, level)
            logger.info(
                "async_start_session: new %s for user %d level %d (%d questions)",
                session.session_id, user_id, level, len(questions),
            )

        # Record start time for first question
        if session.current_question:
            self._q_start_times.setdefault(session.session_id, {})[
                session.current_question.id
            ] = time.monotonic()

        return session.session_id, [q.to_dict() for q in session.questions]

    async def async_submit_answers(
        self,
        session_id: str,
        answers: Dict[str, Any],
    ) -> Dict:
        """
        Async entry point: Step 3 + Step 4 + Step 5.

        Args:
            session_id: returned from async_start_session.
            answers:    {question_id: answer_value} for all (or partial) questions.

        Returns result dict with score, reward, level_result, hitl_features.
        Exposed to Backend as POST /v2/session/answers.
        """
        # Find session by session_id
        session = self._find_session_by_id(session_id)
        if session is None:
            raise ValueError(f"Session '{session_id}' not found or expired.")

        user_id = session.user_id
        level = session.level
        is_level_20 = (level == 20)

        # Score each submitted answer and record into session
        for q_id, raw_answer in answers.items():
            q = next((q for q in session.questions if q.id == q_id), None)
            if q is None:
                continue
            if q_id in session.answers:
                continue  # already answered — skip

            # Record timing
            sid_timings = self._q_start_times.get(session.session_id, {})
            start_t = sid_timings.pop(q_id, None)
            if start_t is not None:
                elapsed = time.monotonic() - start_t
                self._q_timings.setdefault(session.session_id, {})[q_id] = elapsed

            score, feedback = self._score_answer(q, raw_answer)
            record = AnswerRecord(
                question_id=q_id,
                question_type=q.type,
                answer=raw_answer,
                score=score,
                is_level_20=is_level_20,
                feedback=feedback,
            )
            session.answers[q_id] = record
            session.current_index += 1
            session.last_activity = datetime.now()

            self._db.save_answer(
                user_id=user_id,
                session_id=session.session_id,
                question_id=q_id,
                question_type=q.type.value,
                answer=raw_answer,
                score=score,
                is_level_20=is_level_20,
                feedback=feedback,
            )

        self._db.update_session(session.session_id, current_question=session.current_index)

        # Only finalise if all questions answered
        if not session.is_complete:
            return {
                "status":   "in_progress",
                "answered": len(session.answers),
                "total":    session.total_questions,
            }

        # Step 3: evaluate answers via RAG scoring
        session_score = await evaluate_answers(
            evaluator=self._evaluator,
            scorer=self._scorer,
            questions=session.questions,
            answers=session.answers,
            user_id=user_id,
            level=level,
        )

        # Step 4: extract HITL features
        timings = self._q_timings.pop(session.session_id, {})
        hitl_feats = await extract_features_step(
            questions=session.questions,
            answers=session.answers,
            session_score=session_score,
            question_timings=timings,
        )

        # Compute reward
        avg_score = session.average_score
        level_result = self._compute_level_result(user_id, session, avg_score)

        # Step 5: update DB + ML
        await update_user(
            db=self._db,
            ml=self._ml,
            user_id=user_id,
            level=level,
            avg_score=avg_score,
            reward=level_result.reward,
            level_up=level_result.level_up,
            answers=session.answers,
            hitl_features=hitl_feats,
        )

        # Clean up session
        session.status = SessionStatus.COMPLETED
        self._db.close_session(session.session_id, status="completed")
        self._q_start_times.pop(session.session_id, None)
        del self._sessions[user_id]

        logger.info(
            "async_submit_answers: user %d | level %d | score=%.3f | reward=%d",
            user_id, level, avg_score, level_result.reward,
        )

        return {
            "status":        "complete",
            "score":         round(avg_score, 4),
            "reward":        level_result.reward,
            "level_result":  level_result.to_dict(),
            "session_score": session_score.to_dict(),
            "hitl_features": hitl_feats,
        }


    # =========================================================================
    # Sync API — preserved for backwards compat with existing Backend endpoints
    # =========================================================================

    def start_session(
        self,
        user_id: int,
        level: int = 1,
        asset_context: str = "",
        force_new: bool = False,
        market_context: Optional[MarketContext] = None,
    ) -> SessionResponse:
        """
        Sync version of session start. Used by existing Backend /session/start.
        Runs the async pipeline synchronously via asyncio.
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
            # Step 1: context (sync path — use build_context directly)
            if market_context is None:
                market_context = self._context_injector.build_context(user_id, level)

            # Step 2: generate questions (sync)
            questions = self._qgen.generate(
                level=level,
                user_id=user_id,
                context=market_context,
                asset_context=asset_context,
            )

            session = BotSession(user_id=user_id, level=level, questions=questions)
            self._sessions[user_id] = session
            self._q_start_times[session.session_id] = {}
            self._q_timings[session.session_id] = {}

            self._db.create_session(session.session_id, user_id, level)
            logger.info(
                "FinnexusBot: new session %s for user %d level %d (%d questions)",
                session.session_id, user_id, level, len(questions),
            )

        # Record start time for first question
        if session.current_question:
            self._q_start_times.setdefault(session.session_id, {})[
                session.current_question.id
            ] = time.monotonic()

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

        # Record start time for this question
        if q is not None:
            self._q_start_times.setdefault(session.session_id, {}).setdefault(
                q.id, time.monotonic()
            )

        return q.to_dict() if q else None

    def submit_answer(self, user_id: int, answer: Any) -> AnswerResponse:
        """
        Sync one-answer-at-a-time submission. Preserved for existing Backend endpoints.
        """
        session = self._get_session(user_id)
        if session is None:
            raise ValueError(f"No active session for user {user_id}. Call start_session first.")

        if session.is_complete:
            raise ValueError("Session already complete. Start a new session.")

        question = session.current_question
        is_level_20 = (session.level == 20)

        # Record timing
        sid_timings = self._q_start_times.get(session.session_id, {})
        start_t = sid_timings.pop(question.id, None)
        if start_t is not None:
            elapsed = time.monotonic() - start_t
            self._q_timings.setdefault(session.session_id, {})[question.id] = elapsed

        # Score via existing scoring logic
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

        # Start timer for next question
        next_q = session.current_question
        if next_q is not None:
            self._q_start_times.setdefault(session.session_id, {})[next_q.id] = time.monotonic()

        if session.is_complete:
            level_result = self._finish_level(user_id, session)
            return AnswerResponse(
                status="level_complete",
                score=score,
                progress=session.progress_str,
                feedback=feedback,
                level_result=level_result.to_dict(),
            )

        return AnswerResponse(
            status="in_progress",
            score=score,
            progress=session.progress_str,
            feedback=feedback,
            next_question=next_q.to_dict() if next_q else None,
        )


    # =========================================================================
    # Internal helpers
    # =========================================================================

    def _finish_level(self, user_id: int, session: BotSession) -> LevelResult:
        """Compute reward, run Steps 3-5 synchronously, close session."""
        avg_score = session.average_score
        level_result = self._compute_level_result(user_id, session, avg_score)
        level = session.level

        # Step 3+4 sync path: AnswerScorer + HITL features
        self._scorer.reset()
        q_map = {q.id: q for q in session.questions}
        for q_id, record in session.answers.items():
            q = q_map.get(q_id)
            if q:
                self._scorer.score_answer(q, record.answer)
        session_score = self._scorer.session_summary(user_id=user_id, level=level)

        timings = self._q_timings.pop(session.session_id, {})
        hitl_feats = extract_hitl_features(
            questions=session.questions,
            answers=session.answers,
            session_score=session_score,
            question_timings=timings,
        )
        logger.info(
            "FinnexusBot: HITL features for user %d: %s", user_id, hitl_feats
        )

        # Step 5: DB + ML
        self._db.save_level_progress(
            user_id=user_id, level=level, score=avg_score,
            reward=level_result.reward, next_level_unlocked=level_result.level_up,
        )
        self._db.add_paper_cash(user_id, level_result.reward)

        try:
            self._ml.train_on_answers(
                user_id=user_id,
                answers=session.answers,
                market_outcome=avg_score,
                level=level,
            )
        except Exception as exc:
            logger.warning("FinnexusBot: ML train_on_answers failed: %s", exc)

        # Close
        session.status = SessionStatus.COMPLETED
        self._db.close_session(session.session_id, status="completed")
        self._q_start_times.pop(session.session_id, None)
        del self._sessions[user_id]

        logger.info(
            "FinnexusBot: user %d finished level %d | score=%.3f | reward=%d | next=%d",
            user_id, level, avg_score, level_result.reward, level_result.next_level,
        )
        return level_result

    def _compute_level_result(
        self, user_id: int, session: BotSession, avg_score: float
    ) -> LevelResult:
        """Pure computation of reward + level progression. No side effects."""
        level = session.level
        is_level_20 = (level == 20)

        base_reward = cfg.LEVEL_REWARDS.get(level, cfg.LEVEL_20_BASE_REWARD)
        level_20_bonus = 0
        if is_level_20:
            level_20_bonus = int(avg_score * cfg.LEVEL_20_MAX_BONUS)
            reward = base_reward + level_20_bonus
        else:
            reward = int(base_reward * avg_score)

        level_up = avg_score >= cfg.LEVEL_UP_THRESHOLD
        level_down = avg_score < cfg.LEVEL_DOWN_THRESHOLD and level > 1

        if level_up and not is_level_20:
            next_level = min(level + 1, 5)
        elif level_down:
            next_level = max(level - 1, 1)
        else:
            next_level = level

        if level_up:
            msg = f"Great work! Score {avg_score:.0%} — advancing to Level {next_level}."
        elif level_down:
            msg = f"Score {avg_score:.0%} — dropping to Level {next_level} for more practice."
        else:
            msg = f"Score {avg_score:.0%} — stay at Level {level}. Keep practising!"
        if is_level_20:
            msg += f" Bonus earned: ${level_20_bonus}."

        return LevelResult(
            level=level, score=avg_score, reward=reward,
            next_level=next_level, level_up=level_up,
            is_level_20=is_level_20, level_20_bonus=level_20_bonus,
            message=msg,
        )

    def _score_answer(self, question: Any, answer: Any) -> Tuple[float, str]:
        """Return (score 0-1, feedback str). No side effects."""
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
            if question.correct_answer is None:
                return 0.7, (
                    "Choice noted. All options represent valid trading styles. "
                    "No single 'correct' answer."
                )
            correct = question.correct_answer
            is_correct = str(answer).strip().lower() == str(correct).strip().lower()
            score = 1.0 if is_correct else 0.0
            fb = "Correct!" if is_correct else f"Incorrect. The answer is: {correct}"
            return score, fb

        if qtype == QuestionType.MCQ_MULTIPLE:
            correct_set = {str(c).strip().lower() for c in (question.correct_answer or [])}
            if not correct_set:
                return 0.5, "No correct answers defined."
            ans_set = {
                str(a).strip().lower()
                for a in (answer if isinstance(answer, list) else [answer])
            }
            if not ans_set:
                return 0.0, "No answer provided."
            precision = len(ans_set & correct_set) / len(ans_set)
            recall = len(ans_set & correct_set) / len(correct_set)
            score = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
            fb = f"F1 score: {score:.0%}. Correct answers: {', '.join(question.correct_answer)}"
            return round(score, 4), fb

        return 0.0, "Unknown question type."

    def _find_session_by_id(self, session_id: str) -> Optional[BotSession]:
        """Look up a session by session_id across all in-memory sessions."""
        for session in self._sessions.values():
            if session.session_id == session_id:
                age = (datetime.now() - session.last_activity).total_seconds()
                if age > cfg.SESSION_TIMEOUT_SECONDS:
                    self._close_session(session.user_id, SessionStatus.TIMED_OUT)
                    return None
                return session
        return None

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
            self._q_start_times.pop(session.session_id, None)
            self._q_timings.pop(session.session_id, None)
            logger.info(
                "FinnexusBot: closed session %s with status %s",
                session.session_id, status.value,
            )


    # =========================================================================
    # Stats / utility (unchanged logic, preserved exactly)
    # =========================================================================

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

    def assess_starting_level(self, proficiency_score: float) -> int:
        """Map a proficiency score (0-1) to a recommended starting level."""
        for threshold, level in cfg.PROFICIENCY_BREAKPOINTS:
            if proficiency_score < threshold:
                return level
        return 5

