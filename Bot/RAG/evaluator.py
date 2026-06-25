"""
FinNexus Bot — SAQ Evaluator
=============================
Scores SHORT-ANSWER and MCQ responses for TRADING DECISION QUALITY.

Scoring philosophy:
  MCQ answers reveal trading style — not right/wrong.
  SAQ answers scored on: Decision clarity, Risk awareness, Synthesis depth.

Uses retrieved context from RAGRetriever (trading_theories + news_events).
Does NOT handle context assembly — that belongs to context_injector.py.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from Bot.RAG.retriever import RAGRetriever

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword sets for heuristic scoring
# ---------------------------------------------------------------------------

_DECISION_WORDS = {
    "buy", "sell", "hold", "short", "long", "enter", "exit", "close",
    "reduce", "add", "hedge", "cover", "roll", "rotate", "deploy",
    "take profit", "cut loss", "scale", "position",
}

_RISK_WORDS = {
    "stop", "stop-loss", "stoploss", "risk", "drawdown", "loss",
    "hedge", "protect", "limit", "max loss", "exposure", "size",
    "percent", "%", "capital", "allocation", "downside", "upside",
    "support", "resistance", "level",
}

_SYNTHESIS_WORDS = {
    "because", "therefore", "signals", "implies", "given",
    "macro", "rate", "fed", "rbi", "inflation", "earnings",
    "volume", "trend", "breakout", "momentum", "sector",
    "correlation", "vix", "volatility", "news", "catalyst",
    "flow", "fii", "dii", "sentiment", "technical", "fundamental",
}

_VAGUE_PHRASES = [
    "i would wait", "hard to say", "depends on", "it could go either way",
    "not sure", "maybe", "might", "perhaps", "i think", "i guess",
]


# ---------------------------------------------------------------------------
# SAQEvaluator
# ---------------------------------------------------------------------------

class SAQEvaluator:
    """
    Evaluates SAQ and MCQ responses for trading decision quality.

    Context is retrieved from RAGRetriever (top_k=3 max).
    LLM fallback evaluates Decision Quality, Risk Awareness, Synthesis.
    Heuristic fallback uses keyword density + specificity signals.
    """

    def __init__(self, retriever: "RAGRetriever", llm_client=None):
        self.retriever = retriever
        self.llm = llm_client

    # ── Main entry point ─────────────────────────────────────────────────────

    def evaluate(
        self,
        question: str,
        answer: str,
        word_limit: int = 80,
        context_hint: str = "",
        question_subtype: str = "",
    ) -> Dict:
        """
        Returns:
          {
            "score": float 0-1,
            "feedback": str,
            "decision_quality": float,
            "risk_awareness": float,
            "synthesis": float,
            "method": "llm" | "heuristic"
          }
        """
        # MCQ with no justification → base engagement score
        if question_subtype in ("scenario_mcq", "impact_mcq") and len(answer.strip().split()) < 5:
            return _mcq_selection_score(answer)

        # Retrieve scored context (top_k capped at 3 in retriever)
        query = f"{question} {context_hint}".strip()
        context_text = self.retriever.get_context_text(query, top_k=3)

        if self.llm is not None:
            try:
                return self._llm_evaluate(question, answer, context_text, word_limit)
            except Exception as exc:
                logger.warning("SAQEvaluator LLM failed: %s — using heuristic", exc)

        return self._heuristic_evaluate(question, answer, word_limit)

    # ── LLM evaluation ────────────────────────────────────────────────────────

    def _llm_evaluate(self, question: str, answer: str, context: str, word_limit: int) -> Dict:
        prompt = _build_eval_prompt(question, answer, context, word_limit)
        raw = self.llm.complete(prompt)
        return _parse_llm_response(raw)

    # ── Heuristic evaluation ──────────────────────────────────────────────────

    def _heuristic_evaluate(self, question: str, answer: str, word_limit: int) -> Dict:
        answer_lower  = answer.lower()
        answer_words  = answer_lower.split()
        word_count    = len(answer_words)
        answer_tokens = set(re.findall(r"\b\w{3,}\b", answer_lower))

        # Decision quality
        decision_hits = len(answer_tokens & _DECISION_WORDS)
        vague_count   = sum(1 for p in _VAGUE_PHRASES if p in answer_lower)
        decision_raw  = min(decision_hits / 3.0, 1.0) - (vague_count * 0.15)
        decision_quality = float(max(decision_raw, 0.0))

        # Risk awareness
        risk_hits     = len(answer_tokens & _RISK_WORDS)
        numeric_count = len(re.findall(r"\d+", answer))
        risk_raw      = min(risk_hits / 3.0, 1.0) + (min(numeric_count, 3) * 0.08)
        risk_awareness = float(min(risk_raw, 1.0))

        # Synthesis depth
        synth_hits  = len(answer_tokens & _SYNTHESIS_WORDS)
        length_ratio = min(word_count / max(word_limit * 0.5, 20), 1.0)
        synth_raw   = (min(synth_hits / 4.0, 1.0) * 0.6) + (length_ratio * 0.4)
        synthesis   = float(synth_raw)

        score = round(decision_quality * 0.4 + risk_awareness * 0.35 + synthesis * 0.25, 4)
        feedback = _build_heuristic_feedback(score, decision_quality, risk_awareness, synthesis, word_count)

        return {
            "score"           : score,
            "feedback"        : feedback,
            "decision_quality": round(decision_quality, 4),
            "risk_awareness"  : round(risk_awareness, 4),
            "synthesis"       : round(synthesis, 4),
            "method"          : "heuristic",
        }


# ---------------------------------------------------------------------------
# MCQ selection scorer
# ---------------------------------------------------------------------------

def _mcq_selection_score(answer: str) -> Dict:
    """Base score for MCQ option selection without justification."""
    return {
        "score"           : 0.7,
        "feedback"        : (
            "Choice noted. All options represent valid trading philosophies. "
            "Add your reasoning to improve your score."
        ),
        "decision_quality": 0.7,
        "risk_awareness"  : 0.7,
        "synthesis"       : 0.7,
        "method"          : "mcq_selection",
    }


# ---------------------------------------------------------------------------
# LLM prompt builder
# ---------------------------------------------------------------------------

def _build_eval_prompt(question: str, answer: str, context: str, word_limit: int) -> str:
    return f"""You are evaluating a TRADER'S DECISION QUALITY for the FinNexus HITL platform.

TRADING SCENARIO / QUESTION:
{question}

TRADER'S ANSWER ({word_limit}-word limit):
{answer}

MARKET CONTEXT:
{context}

EVALUATION FRAMEWORK — score each dimension 0.0 to 1.0 (two decimal places):

DECISION_QUALITY: Is the answer specific and actionable?
  1.0 = Clear, specific action with exact levels (buy X at Y, stop at Z)
  0.7 = Reasonable action stated but lacks specifics
  0.4 = Vague or uncommitted ("wait and see", "depends")
  0.1 = No meaningful decision given

RISK_AWARENESS: Does the answer acknowledge downside / position sizing / risk management?
  1.0 = Explicit stop-loss, position size, max loss, or hedge mentioned
  0.7 = Some risk acknowledgement (e.g. "reduce exposure")
  0.4 = Indirect risk awareness
  0.1 = No risk consideration at all

SYNTHESIS: Does the answer integrate multiple factors (price + news + macro)?
  1.0 = Synthesises at least 3 factors from the scenario
  0.7 = Uses 2 factors
  0.4 = References only one factor
  0.1 = Generic answer disconnected from the scenario

Respond ONLY in this exact format — no other text:
DECISION_QUALITY: <score>
RISK_AWARENESS: <score>
SYNTHESIS: <score>
FEEDBACK: <one specific sentence of constructive feedback for a trader>"""


# ---------------------------------------------------------------------------
# LLM response parser
# ---------------------------------------------------------------------------

def _parse_llm_response(raw: str) -> Dict:
    dq = ra = sy = None
    feedback = ""
    for line in raw.strip().splitlines():
        ln = line.strip()
        if ln.upper().startswith("DECISION_QUALITY:"):
            dq = _extract_float(ln)
        elif ln.upper().startswith("RISK_AWARENESS:"):
            ra = _extract_float(ln)
        elif ln.upper().startswith("SYNTHESIS:"):
            sy = _extract_float(ln)
        elif ln.upper().startswith("FEEDBACK:"):
            feedback = ln.split(":", 1)[-1].strip()

    if any(v is None for v in (dq, ra, sy)):
        nums = re.findall(r"0\.\d+|1\.0", raw)
        fallback = float(nums[0]) if nums else 0.5
        return {
            "score"           : round(fallback, 4),
            "feedback"        : feedback or "Answer evaluated.",
            "decision_quality": fallback,
            "risk_awareness"  : fallback,
            "synthesis"       : fallback,
            "method"          : "llm_partial",
        }

    dq = float(min(max(dq, 0.0), 1.0))
    ra = float(min(max(ra, 0.0), 1.0))
    sy = float(min(max(sy, 0.0), 1.0))
    score = round(dq * 0.40 + ra * 0.35 + sy * 0.25, 4)

    return {
        "score"           : score,
        "feedback"        : feedback,
        "decision_quality": dq,
        "risk_awareness"  : ra,
        "synthesis"       : sy,
        "method"          : "llm",
    }


def _extract_float(line: str) -> Optional[float]:
    m = re.search(r"(\d+\.?\d*)", line)
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Heuristic feedback builder
# ---------------------------------------------------------------------------

def _build_heuristic_feedback(
    score: float,
    dq: float,
    ra: float,
    sy: float,
    word_count: int,
) -> str:
    if word_count < 8:
        return "Too brief. State a specific action with at least one level and one reason."
    if dq < 0.3:
        return "Be more decisive. State exactly what you would do (buy/sell/hedge) and at what level."
    if ra < 0.3:
        return "Your answer lacks risk management. Add a stop-loss level or position size."
    if sy < 0.3:
        return "Try to connect multiple factors: price action, news, and macro context."
    if score >= 0.80:
        return "Strong answer — clear decision, risk-aware, and well-grounded in the scenario."
    if score >= 0.60:
        return "Solid answer. Adding specific levels (entry/stop/target) would push this higher."
    return "Reasonable thinking. Try to be more specific: exact levels, exact sizing, exact reasons."
