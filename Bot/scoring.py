"""
FinNexus Bot — Answer Scoring Engine
======================================
Evaluates trader responses for QUALITY OF REASONING, not factual correctness.

Design philosophy:
  - MCQ: choices reveal trader psychology → score each option's dimension
  - SAQ: LLM evaluates open-ended answers across 5 cognitive dimensions
  - Overall score is a multi-dimensional profile, not a single number

Scoring dimensions:
  1. risk_awareness       (0-20): Does the trader consider downside?
  2. market_understanding (0-20): Is the macro/micro context understood?
  3. decision_quality     (0-20): Is the decision specific and actionable?
  4. adaptability         (0-20): Does the plan include conditional logic?
  5. synthesis            (0-20): Are multiple factors integrated?
  Total: 0-100

MCQ Dimension Map:
  For scenario_mcq and impact_mcq, each option A-E maps to known traits.
  The mapping reveals the trader's default style without penalising it.

SAQ Evaluation:
  Uses LLM to score the answer across the 5 dimensions.
  Returns structured JSON with scores + qualitative feedback.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ScoreResult:
    """Result of evaluating one question-answer pair."""

    question_id: str
    question_type: str           # "scenario_mcq" | "impact_mcq" | "strategy_saq" | "risk_saq"
    user_answer: str             # Selected option text or SAQ response

    # Dimension scores (0-20 each)
    risk_awareness: int = 0
    market_understanding: int = 0
    decision_quality: int = 0
    adaptability: int = 0
    synthesis: int = 0

    # Qualitative output
    trader_profile: str = ""     # e.g. "Momentum trader with moderate risk tolerance"
    strengths: List[str] = field(default_factory=list)
    growth_areas: List[str] = field(default_factory=list)
    feedback: str = ""           # 2-3 sentence coaching note

    # Style tags revealed by this answer
    style_tags: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return (self.risk_awareness + self.market_understanding +
                self.decision_quality + self.adaptability + self.synthesis)

    @property
    def pct(self) -> float:
        return self.total / 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "question_type": self.question_type,
            "user_answer": self.user_answer,
            "scores": {
                "risk_awareness": self.risk_awareness,
                "market_understanding": self.market_understanding,
                "decision_quality": self.decision_quality,
                "adaptability": self.adaptability,
                "synthesis": self.synthesis,
                "total": self.total,
            },
            "trader_profile": self.trader_profile,
            "strengths": self.strengths,
            "growth_areas": self.growth_areas,
            "feedback": self.feedback,
            "style_tags": self.style_tags,
        }


# ---------------------------------------------------------------------------
# Session-level aggregate
# ---------------------------------------------------------------------------

@dataclass
class SessionScore:
    """Aggregated score across all questions in a session."""

    user_id: int
    level: int
    question_results: List[ScoreResult] = field(default_factory=list)

    @property
    def avg_risk_awareness(self) -> float:
        return self._avg("risk_awareness")

    @property
    def avg_market_understanding(self) -> float:
        return self._avg("market_understanding")

    @property
    def avg_decision_quality(self) -> float:
        return self._avg("decision_quality")

    @property
    def avg_adaptability(self) -> float:
        return self._avg("adaptability")

    @property
    def avg_synthesis(self) -> float:
        return self._avg("synthesis")

    @property
    def overall_score(self) -> float:
        if not self.question_results:
            return 0.0
        return sum(r.total for r in self.question_results) / len(self.question_results)

    def _avg(self, attr: str) -> float:
        if not self.question_results:
            return 0.0
        return sum(getattr(r, attr) for r in self.question_results) / len(self.question_results)

    @property
    def dominant_style(self) -> str:
        """Most frequently appearing style tag across all answers."""
        from collections import Counter
        all_tags = [t for r in self.question_results for t in r.style_tags]
        if not all_tags:
            return "balanced"
        return Counter(all_tags).most_common(1)[0][0]

    @property
    def trader_archetype(self) -> str:
        """
        Synthesize a trader archetype from dimension averages.
        Examples: "Disciplined Risk Manager", "Aggressive Momentum Trader",
                  "Macro-Aware Conservative", "Systematic Contrarian"
        """
        ra = self.avg_risk_awareness
        mu = self.avg_market_understanding
        dq = self.avg_decision_quality
        ad = self.avg_adaptability
        sy = self.avg_synthesis

        if ra >= 16 and dq >= 16:
            base = "Disciplined Risk Manager"
        elif mu >= 16 and sy >= 16:
            base = "Macro-Aware Analyst"
        elif dq >= 16 and ad >= 16:
            base = "Adaptive Tactical Trader"
        elif ra < 10 and dq >= 14:
            base = "Aggressive Momentum Trader"
        elif ad >= 16 and sy >= 14:
            base = "Systematic Macro Trader"
        else:
            base = "Balanced Multi-Approach Trader"

        # Add qualifier
        if self.overall_score >= 80:
            return f"Elite {base}"
        elif self.overall_score >= 65:
            return base
        elif self.overall_score >= 50:
            return f"Developing {base}"
        else:
            return "Early-Stage Trader (Learning)"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "level": self.level,
            "overall_score": round(self.overall_score, 1),
            "archetype": self.trader_archetype,
            "dominant_style": self.dominant_style,
            "dimension_averages": {
                "risk_awareness": round(self.avg_risk_awareness, 1),
                "market_understanding": round(self.avg_market_understanding, 1),
                "decision_quality": round(self.avg_decision_quality, 1),
                "adaptability": round(self.avg_adaptability, 1),
                "synthesis": round(self.avg_synthesis, 1),
            },
            "question_count": len(self.question_results),
        }


# ---------------------------------------------------------------------------
# MCQ option dimension maps
# ---------------------------------------------------------------------------

# Each MCQ option (index 0-4 = A-E) maps to (style_tag, dimension_boosts)
# dimension_boosts: dict of dimension_name -> points (out of 20)
# Options are not right/wrong — they reveal different strengths.

_SCENARIO_MCQ_MAP = [
    # Option A: Aggressive/decisive action
    {
        "style": "aggressive_momentum",
        "risk_awareness": 8,
        "market_understanding": 14,
        "decision_quality": 16,
        "adaptability": 10,
        "synthesis": 12,
    },
    # Option B: Conservative partial action
    {
        "style": "risk_conscious",
        "risk_awareness": 18,
        "market_understanding": 14,
        "decision_quality": 16,
        "adaptability": 14,
        "synthesis": 14,
    },
    # Option C: Observation / wait-and-see
    {
        "style": "patient_analyst",
        "risk_awareness": 14,
        "market_understanding": 16,
        "decision_quality": 12,
        "adaptability": 16,
        "synthesis": 14,
    },
    # Option D: Adding / contrarian
    {
        "style": "contrarian",
        "risk_awareness": 10,
        "market_understanding": 14,
        "decision_quality": 14,
        "adaptability": 12,
        "synthesis": 16,
    },
    # Option E: Hedging / complex structure
    {
        "style": "sophisticated_hedger",
        "risk_awareness": 16,
        "market_understanding": 16,
        "decision_quality": 14,
        "adaptability": 18,
        "synthesis": 18,
    },
]

_IMPACT_MCQ_MAP = [
    # Strongly bullish
    {
        "style": "bull_conviction",
        "risk_awareness": 8,
        "market_understanding": 14,
        "decision_quality": 14,
        "adaptability": 10,
        "synthesis": 12,
    },
    # Mildly bullish
    {
        "style": "measured_optimist",
        "risk_awareness": 14,
        "market_understanding": 16,
        "decision_quality": 14,
        "adaptability": 14,
        "synthesis": 14,
    },
    # Neutral / already priced in
    {
        "style": "efficient_market_believer",
        "risk_awareness": 16,
        "market_understanding": 18,
        "decision_quality": 12,
        "adaptability": 14,
        "synthesis": 16,
    },
    # Mildly bearish
    {
        "style": "cautious_risk_manager",
        "risk_awareness": 18,
        "market_understanding": 16,
        "decision_quality": 14,
        "adaptability": 14,
        "synthesis": 14,
    },
    # Strongly bearish
    {
        "style": "bear_contrarian",
        "risk_awareness": 12,
        "market_understanding": 14,
        "decision_quality": 14,
        "adaptability": 10,
        "synthesis": 12,
    },
]


def _score_mcq(question_id: str, question_type: str,
               chosen_option_index: int, option_text: str) -> ScoreResult:
    """Score an MCQ answer. chosen_option_index is 0-based (0=A, 4=E)."""
    if question_type == "impact_mcq":
        dim_map = _IMPACT_MCQ_MAP
    else:
        dim_map = _SCENARIO_MCQ_MAP

    idx = max(0, min(4, chosen_option_index))
    dims = dim_map[idx]

    strengths = []
    growth_areas = []

    if dims["risk_awareness"] >= 16:
        strengths.append("Strong risk consciousness")
    elif dims["risk_awareness"] <= 10:
        growth_areas.append("Develop stronger downside awareness before acting")

    if dims["market_understanding"] >= 16:
        strengths.append("Good market context integration")

    if dims["synthesis"] >= 16:
        strengths.append("Multi-factor synthesis in decision-making")
    elif dims["synthesis"] <= 12:
        growth_areas.append("Consider integrating more factors before deciding")

    if dims["adaptability"] >= 16:
        strengths.append("Conditional and adaptive thinking")

    style_to_feedback = {
        "aggressive_momentum": "You tend toward decisive action on signals. Strong execution mindset — ensure you pair it with defined stop-loss levels.",
        "risk_conscious": "You balance conviction with risk management — a hallmark of professional traders. Continue refining your partial position sizing.",
        "patient_analyst": "You prioritise information before action. This discipline protects capital; watch for opportunities missed due to over-analysis.",
        "contrarian": "You look for value where others see risk. Contrarian thinking can generate alpha — ensure your thesis has a clear invalidation point.",
        "sophisticated_hedger": "You structure positions to manage downside while maintaining upside — an advanced approach. Ensure the hedge cost is justified.",
        "bull_conviction": "Strong directional conviction. High-confidence calls can generate strong returns; define your exit before entering.",
        "measured_optimist": "Balanced bullish view that respects uncertainty — a mature framework for impact assessment.",
        "efficient_market_believer": "You discount obvious news, seeking edge in what markets haven't priced. This is a powerful lens at higher levels.",
        "cautious_risk_manager": "Risk-first assessment. Protecting capital is the primary edge — pair it with a clear re-entry framework.",
        "bear_contrarian": "You see bearish scenarios others overlook. Ensure this is data-driven and not anchoring to a prior bear thesis.",
    }

    feedback = style_to_feedback.get(dims["style"], "Decision recorded. Continue developing your trading framework.")

    return ScoreResult(
        question_id=question_id,
        question_type=question_type,
        user_answer=option_text,
        risk_awareness=dims["risk_awareness"],
        market_understanding=dims["market_understanding"],
        decision_quality=dims["decision_quality"],
        adaptability=dims["adaptability"],
        synthesis=dims["synthesis"],
        trader_profile=dims["style"].replace("_", " ").title(),
        strengths=strengths,
        growth_areas=growth_areas,
        feedback=feedback,
        style_tags=[dims["style"]],
    )


# ---------------------------------------------------------------------------
# SAQ scoring prompt
# ---------------------------------------------------------------------------

_SAQ_SCORING_PROMPT = """You are a professional trading coach evaluating a trader's answer.

QUESTION TYPE: {question_type}
QUESTION: {question}
CONTEXT: {context}

TRADER'S ANSWER:
{answer}

Evaluate this answer across FIVE dimensions (each scored 0-20):

1. risk_awareness (0-20): Does the answer identify and quantify downside risks?
   - 0-5: No risk mention
   - 6-10: Risks mentioned but vague
   - 11-15: Specific risks identified with mitigation
   - 16-20: Quantified risks with clear stop-losses or hedges

2. market_understanding (0-20): Is the macro/micro market context correctly interpreted?
   - 0-5: Factually incorrect or irrelevant analysis
   - 6-10: Partial understanding of context
   - 11-15: Sound analysis with minor gaps
   - 16-20: Expert-level context integration

3. decision_quality (0-20): Is the decision specific, actionable, and internally consistent?
   - 0-5: Vague or contradictory
   - 6-10: General direction without specifics
   - 11-15: Specific entries/exits mentioned
   - 16-20: Complete plan with asset, sizing, entry, exit, and logic

4. adaptability (0-20): Does the answer include conditional logic ("if X then Y")?
   - 0-5: Single rigid outcome assumed
   - 6-10: One alternative scenario considered
   - 11-15: Multiple scenarios with responses
   - 16-20: Dynamic framework with trigger conditions

5. synthesis (0-20): Are multiple factors (news + price + risk + timing) integrated?
   - 0-5: Single factor only
   - 6-10: Two factors mentioned
   - 11-15: Three or more factors coherently integrated
   - 16-20: Complete multi-factor synthesis with cross-asset awareness

Also provide:
- trader_profile: One-line description of what this answer reveals about the trader
- strengths: 1-3 specific strengths demonstrated (be precise, not generic)
- growth_areas: 1-3 specific areas to develop (constructive, not critical)
- feedback: 2-3 sentence coaching note that would help this trader improve
- style_tags: 1-3 tags from: [momentum, contrarian, risk_first, macro_aware, systematic,
  fundamental, technical, event_driven, hedger, aggressive, conservative, patient]

Return ONLY a valid JSON object (no other text):
{{
  "risk_awareness": <int 0-20>,
  "market_understanding": <int 0-20>,
  "decision_quality": <int 0-20>,
  "adaptability": <int 0-20>,
  "synthesis": <int 0-20>,
  "trader_profile": "<string>",
  "strengths": ["<string>", ...],
  "growth_areas": ["<string>", ...],
  "feedback": "<string>",
  "style_tags": ["<string>", ...]
}}"""


def _score_saq_with_llm(
    question_id: str,
    question_type: str,
    question_text: str,
    context: str,
    answer: str,
    llm_client: Any,
) -> ScoreResult:
    """Use LLM to score an SAQ response."""
    prompt = _SAQ_SCORING_PROMPT.format(
        question_type=question_type,
        question=question_text,
        context=context,
        answer=answer,
    )

    try:
        raw = llm_client.complete(prompt, temperature=0.3, max_tokens=600)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in LLM scoring response")
        data = json.loads(match.group(0))

        return ScoreResult(
            question_id=question_id,
            question_type=question_type,
            user_answer=answer,
            risk_awareness=int(data.get("risk_awareness", 10)),
            market_understanding=int(data.get("market_understanding", 10)),
            decision_quality=int(data.get("decision_quality", 10)),
            adaptability=int(data.get("adaptability", 10)),
            synthesis=int(data.get("synthesis", 10)),
            trader_profile=data.get("trader_profile", ""),
            strengths=data.get("strengths", []),
            growth_areas=data.get("growth_areas", []),
            feedback=data.get("feedback", ""),
            style_tags=data.get("style_tags", []),
        )
    except Exception as exc:
        logger.warning("SAQ LLM scoring failed (%s) — falling back to heuristic", exc)
        return _score_saq_heuristic(question_id, question_type, answer)


def _score_saq_heuristic(question_id: str, question_type: str, answer: str) -> ScoreResult:
    """
    Heuristic SAQ scorer used when LLM is unavailable.
    Scores based on answer length and presence of key trading vocabulary.
    This is a rough proxy — LLM scoring is strongly preferred.
    """
    answer_lower = answer.lower()
    word_count = len(answer.split())

    # Base score from word count (more words → likely more detail, up to a point)
    base = min(12, max(4, word_count // 10))

    # Vocabulary signals
    risk_words = ["stop loss", "stop-loss", "downside", "risk", "hedge", "drawdown", "protect"]
    market_words = ["macro", "interest rate", "fed", "rbi", "inflation", "gdp", "volume",
                    "moving average", "support", "resistance", "vix"]
    decision_words = ["buy", "sell", "hold", "enter", "exit", "position", "sizing", "allocation"]
    adaptability_words = ["if", "when", "unless", "scenario", "alternatively", "in case", "trigger"]
    synthesis_words = ["because", "therefore", "given that", "combined with", "alongside"]

    def _count_matches(words: List[str]) -> int:
        return sum(1 for w in words if w in answer_lower)

    ra = min(20, base + _count_matches(risk_words) * 2)
    mu = min(20, base + _count_matches(market_words) * 2)
    dq = min(20, base + _count_matches(decision_words) * 2)
    ad = min(20, base + _count_matches(adaptability_words) * 2)
    sy = min(20, base + _count_matches(synthesis_words) * 2)

    feedback = (
        "Answer recorded. For best results, include specific entry/exit levels, "
        "position sizing rationale, and conditional logic ('if price breaks X, then Y')."
    )

    return ScoreResult(
        question_id=question_id,
        question_type=question_type,
        user_answer=answer,
        risk_awareness=ra,
        market_understanding=mu,
        decision_quality=dq,
        adaptability=ad,
        synthesis=sy,
        trader_profile="Heuristic evaluation — LLM unavailable",
        strengths=["Answer submitted"],
        growth_areas=["Enable LLM evaluation for detailed feedback"],
        feedback=feedback,
        style_tags=[],
    )


# ---------------------------------------------------------------------------
# Public scoring API
# ---------------------------------------------------------------------------

class AnswerScorer:
    """
    Scores individual question answers and aggregates session results.

    Usage:
        scorer = AnswerScorer(llm_client=my_llm)  # llm optional but recommended

        # Score an MCQ answer
        result = scorer.score_mcq(question, chosen_index=1)

        # Score an SAQ answer
        result = scorer.score_saq(question, answer_text)

        # Get session summary after all questions scored
        session = scorer.session_summary(user_id=42, level=2)
    """

    def __init__(self, llm_client: Optional[Any] = None):
        self.llm = llm_client
        self._results: List[ScoreResult] = []

    def score_mcq(self, question: Any, chosen_option_index: int) -> ScoreResult:
        """
        Score an MCQ answer.

        Args:
            question:             A Question object (from llm_generator).
            chosen_option_index:  0-based index of selected option (0=A, 4=E).
        """
        option_text = ""
        if question.options and 0 <= chosen_option_index < len(question.options):
            option_text = question.options[chosen_option_index]

        # Determine sub-type from tags
        q_type = question.tags[0] if question.tags else "scenario_mcq"

        result = _score_mcq(
            question_id=question.id,
            question_type=q_type,
            chosen_option_index=chosen_option_index,
            option_text=option_text,
        )
        self._results.append(result)
        return result

    def score_saq(self, question: Any, answer_text: str) -> ScoreResult:
        """
        Score an SAQ answer.

        Args:
            question:     A Question object (from llm_generator).
            answer_text:  The trader's written response.
        """
        q_type = question.tags[0] if question.tags else "strategy_saq"

        if self.llm and self.llm.available:
            result = _score_saq_with_llm(
                question_id=question.id,
                question_type=q_type,
                question_text=question.question,
                context=question.context,
                answer=answer_text,
                llm_client=self.llm,
            )
        else:
            result = _score_saq_heuristic(question.id, q_type, answer_text)

        self._results.append(result)
        return result

    def score_answer(self, question: Any, answer: Any) -> ScoreResult:
        """
        Convenience dispatcher: detects MCQ vs SAQ and routes accordingly.

        Args:
            question: Question object.
            answer:   int (MCQ option index) or str (SAQ text).
        """
        from Bot.schemas import QuestionType  # type: ignore

        if question.type == QuestionType.SAQ:
            return self.score_saq(question, str(answer))
        else:
            # MCQ: answer can be int (index) or str (option letter)
            if isinstance(answer, str) and answer.upper() in "ABCDE":
                idx = "ABCDE".index(answer.upper())
            elif isinstance(answer, int):
                idx = answer
            else:
                idx = 0
            return self.score_mcq(question, idx)

    def session_summary(self, user_id: int, level: int) -> SessionScore:
        """Aggregate all scored results into a session-level report."""
        session = SessionScore(user_id=user_id, level=level, question_results=list(self._results))
        return session

    def reset(self) -> None:
        """Clear stored results for a new session."""
        self._results = []

    @property
    def result_count(self) -> int:
        return len(self._results)


# ---------------------------------------------------------------------------
# Score interpreter helpers
# ---------------------------------------------------------------------------

def interpret_dimension(name: str, score: float) -> str:
    """Return a human-readable label for a dimension score."""
    thresholds = [
        (18, "Exceptional"),
        (15, "Strong"),
        (12, "Developing"),
        (9, "Early"),
        (0, "Needs Focus"),
    ]
    for threshold, label in thresholds:
        if score >= threshold:
            return label
    return "Needs Focus"


def level_up_recommendation(session: SessionScore) -> str:
    """
    Based on session scores, recommend whether the user should advance,
    stay, or revisit their current level.
    """
    score = session.overall_score
    if score >= 75:
        return f"Ready to advance to Level {session.level + 1}"
    elif score >= 60:
        return f"Solidifying Level {session.level} — one more session recommended"
    elif score >= 45:
        return f"Continue at Level {session.level} — focus on risk awareness and decision quality"
    else:
        return f"Consider revisiting Level {max(1, session.level - 1)} fundamentals"


# ---------------------------------------------------------------------------
# CLI quick-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Simulate an MCQ score
    from dataclasses import dataclass as dc

    @dc
    class MockQuestion:
        id = "test_q1"
        type = "MCQ_SINGLE"
        question = "Mock question text"
        context = "Mock context"
        options = ["🟢 Option A", "🟡 Option B", "🔵 Option C", "🟣 Option D", "🔴 Option E"]
        tags = ["scenario_mcq", "risk_tolerance"]

    scorer = AnswerScorer()
    q = MockQuestion()
    result = scorer.score_mcq(q, chosen_option_index=1)

    print("\n=== MCQ SCORE RESULT ===")
    import json as _json
    print(_json.dumps(result.to_dict(), indent=2))

    session = scorer.session_summary(user_id=1, level=1)
    print("\n=== SESSION SUMMARY ===")
    print(_json.dumps(session.to_dict(), indent=2))
    print("Level recommendation:", level_up_recommendation(session))