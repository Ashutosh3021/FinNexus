"""
FinNexus Bot — HITL Question Generator  (v2 — Decision Intelligence)
=====================================================================
Generates 19 questions per session that extract HUMAN TRADING INTELLECT:
  - 10 Scenario MCQ  : "You hold X, news Y breaks. What do you DO?"
  - 5  Impact MCQ    : "News Z hits Asset A. What's your assessment?"
  - 2  Strategy SAQ  : Open-ended trading plan questions
  - 2  Risk SAQ      : Portfolio risk / repositioning questions
  - (+1 Level-20 special: global macro synthesis)

NO trivia. NO definitions. Every question demands a decision under uncertainty.

Question lifecycle:
  MarketContext → LLMClient → QuestionGenerator → List[Question]
  If LLM unavailable → _TEMPLATE_QUESTIONS (scenario bank) used as fallback.
"""

from __future__ import annotations

import json
import logging
import random
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from Bot.schemas import Question, QuestionType
from Bot import config as cfg

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Question sub-types (stored in Question.tags[0])
# ---------------------------------------------------------------------------

SCENARIO_MCQ = "scenario_mcq"   # you hold X, news Y → what do you do?
IMPACT_MCQ   = "impact_mcq"     # news Y hits asset X → impact?
STRATEGY_SAQ = "strategy_saq"   # open-ended trade plan
RISK_SAQ     = "risk_saq"       # portfolio repositioning / risk mgmt

# Per-session question counts
_N_SCENARIO_MCQ = 10
_N_IMPACT_MCQ   = 5
_N_STRATEGY_SAQ = 2
_N_RISK_SAQ     = 2
# Total = 19  (Level-20 replaces the last question with a global synthesis SAQ)


# ---------------------------------------------------------------------------
# Market context dataclass
# ---------------------------------------------------------------------------

@dataclass
class MarketContext:
    """
    Snapshot of current market conditions injected into every prompt.
    All fields are optional — the generator degrades gracefully if absent.
    """
    # Macro regime
    regime: str = "neutral"          # "bull" | "bear" | "volatile" | "neutral"
    vix_level: float = 18.0
    dxy_trend: str = "flat"          # "rising" | "falling" | "flat"

    # Recent news headlines (list of strings)
    news: List[str] = field(default_factory=list)

    # Key price snapshots  {"BTC": 65000, "NIFTY": 24500, ...}
    prices: Dict[str, float] = field(default_factory=dict)

    # Trend context per symbol  {"BTC": "above 50d MA", "NIFTY": "near ATH", ...}
    trends: Dict[str, str] = field(default_factory=dict)

    # User context
    user_level: int = 1
    user_portfolio: str = ""         # e.g. "40% Tech, 30% Crypto, 20% Gold, 10% Cash"
    user_history_summary: str = ""   # e.g. "avg score 0.72, strong in crypto, weak in macro"

    def to_prompt_block(self) -> str:
        """Render context as a compact string for LLM injection."""
        lines = [
            f"MARKET REGIME : {self.regime.upper()}  |  VIX={self.vix_level}  |  DXY={self.dxy_trend}",
        ]
        if self.prices:
            price_str = "  ".join(f"{k}={v:,.0f}" for k, v in self.prices.items())
            lines.append(f"KEY PRICES    : {price_str}")
        if self.trends:
            trend_str = "  |  ".join(f"{k}: {v}" for k, v in self.trends.items())
            lines.append(f"TRENDS        : {trend_str}")
        if self.news:
            lines.append("RECENT NEWS   :")
            for n in self.news[:6]:
                lines.append(f"  • {n}")
        if self.user_portfolio:
            lines.append(f"USER PORTFOLIO: {self.user_portfolio}")
        if self.user_history_summary:
            lines.append(f"USER PROFILE  : {self.user_history_summary}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM Client (unchanged — OpenAI-compatible wrapper)
# ---------------------------------------------------------------------------

class LLMClient:
    """Thin wrapper supporting OpenAI, Groq, and Ollama."""

    def __init__(self, provider="openai", api_key="", model="gpt-4o-mini", base_url=""):
        self.provider  = provider
        self.api_key   = api_key
        self.model     = model
        self.base_url  = base_url
        self._client   = None
        self._init_client()

    def _init_client(self):
        if not self.api_key and self.provider != "ollama":
            logger.warning("LLMClient: no API key — will use template fallback")
            return
        try:
            from openai import OpenAI
            kwargs: Dict[str, Any] = {"api_key": self.api_key or "ollama"}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            elif self.provider == "groq":
                kwargs["base_url"] = "https://api.groq.com/openai/v1"
            elif self.provider == "ollama":
                kwargs["base_url"] = self.base_url or "http://localhost:11434/v1"
            self._client = OpenAI(**kwargs)
            logger.info("LLMClient: %s / %s ready", self.provider, self.model)
        except ImportError:
            logger.warning("LLMClient: openai package not installed")

    def complete(self, prompt: str, temperature: float = 0.85, max_tokens: int = 4000) -> str:
        if self._client is None:
            raise RuntimeError("LLM client not initialised")
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""

    @property
    def available(self) -> bool:
        return self._client is not None


# ---------------------------------------------------------------------------
# System prompt for the LLM
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are FINNEXUS HITL Question Generator.
Your purpose is to extract HUMAN TRADING INTELLECT through scenario-based questions.

CORE RULES — NEVER VIOLATE:
1. NEVER ask definition or trivia questions ("What does RSI stand for?" is FORBIDDEN).
2. EVERY question must present a real decision under uncertainty.
3. MCQ options must represent different trading philosophies — there is NO single correct answer.
4. SAQs must require synthesis of multiple factors (news + price action + risk).
5. Questions must feel like they could happen TODAY in a live trading session.
6. Use the MARKET CONTEXT provided — reference actual prices, news, and trends.
7. Separate aggressive/momentum traders from conservative/risk-first traders through option design.

OPTION DESIGN GUIDE for MCQ:
  Option A — Aggressive momentum (ride the move)
  Option B — Conservative scale-out (take partial profits / cut partial loss)
  Option C — Hedging / risk management (protect the position)
  Option D — Wait and observe (more data needed)
  Option E — Contrarian / macro override

SCORING PHILOSOPHY: Answers are not right/wrong. They reveal trading psychology.
The question should expose: risk tolerance, conviction level, time horizon, macro awareness.

OUTPUT FORMAT — return ONLY a valid JSON array, zero other text:
[
  {
    "type": "scenario_mcq",
    "scenario": "📊 You hold [position]. 📰 NEWS: [specific event]. [Price action context].",
    "options": ["🟢 Option A", "🟡 Option B", "🔵 Option C", "🟣 Option D", "🔴 Option E"],
    "context": "Reveals: [what each choice says about the trader]",
    "asset_class": "Stocks|Crypto|ETFs|Futures|Commodities",
    "asset_symbol": "SYMBOL",
    "reveals": "risk_tolerance|conviction|macro_awareness|discipline|time_horizon"
  },
  {
    "type": "impact_mcq",
    "scenario": "📰 NEWS: [specific event]. 🏭 ASSET: [asset + current price]. Key levels: [support/resistance].",
    "options": [
      "🟢 Strongly bullish — [specific target]",
      "🟡 Mildly bullish — [specific target]",
      "⚪ Neutral — already priced in",
      "🟠 Mildly bearish — [specific target]",
      "🔴 Strongly bearish — [specific target]"
    ],
    "context": "Reveals: [what choice says about trader's macro model]",
    "asset_class": "...",
    "asset_symbol": "..."
  },
  {
    "type": "strategy_saq",
    "question": "📊 [Market state with specific numbers]. 📰 NEWS: [events]. You have [capital] to deploy over [timeframe]. Outline your specific trading plan: asset selection, position sizing, entry/exit levels, and reasoning.",
    "context": "Portfolio context: [relevant background]",
    "word_limit": 80
  },
  {
    "type": "risk_saq",
    "question": "⚠️ RISK SIGNAL: [specific scenario]. Your current portfolio: [allocation]. How do you reposition and what is your risk framework?",
    "context": "Key risk factors: [list]",
    "word_limit": 80
  }
]"""


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_generation_prompt(level: int, context: MarketContext) -> str:
    level_profiles = {
        1: "Level 1 (Beginner): Use simple scenarios — single asset, one news event. "
           "Prices and positions should be small. Test basic risk instincts.",
        2: "Level 2 (Intermediate): Multi-factor scenarios. Include sector context. "
           "Test MACD/BB decision points embedded in real situations.",
        3: "Level 3 (Advanced): Options, futures, cross-asset. Include Greeks context in scenarios. "
           "Test hedging decisions and volatility regime awareness.",
        4: "Level 4 (Expert): Portfolio-level decisions. Stat arb, basis trades, factor exposures. "
           "Test risk-adjusted thinking and multi-leg strategy reasoning.",
        5: "Level 5 (Master): Macro regime, systemic risk, ML signal interpretation. "
           "Test synthesis of global macro + quantitative signal + portfolio risk.",
        20: "Level 20 (Global Events): Major macro shocks only — Fed decisions, geopolitical crises, "
            "currency contagion, commodity supply shocks. Test cross-asset contagion reasoning.",
    }
    profile = level_profiles.get(level, level_profiles[2])

    counts = (
        f"Generate EXACTLY: {_N_SCENARIO_MCQ} scenario_mcq, "
        f"{_N_IMPACT_MCQ} impact_mcq, "
        f"{_N_STRATEGY_SAQ} strategy_saq, "
        f"{_N_RISK_SAQ} risk_saq"
    )
    if level == 20:
        counts = (
            "Generate EXACTLY: 8 scenario_mcq, 5 impact_mcq, 2 strategy_saq, "
            "2 risk_saq, 1 strategy_saq (global macro synthesis spanning 5+ assets and 3+ news events)"
        )

    return f"""{_SYSTEM_PROMPT}

--- MARKET CONTEXT ---
{context.to_prompt_block()}

--- TASK ---
{profile}

{counts} = 19 total questions.
Use the market context above. Reference real prices, real news, real trends.
Do NOT invent contradictory prices. Keep asset_symbol realistic.
Return ONLY the JSON array."""


# ---------------------------------------------------------------------------
# LLM response parser
# ---------------------------------------------------------------------------

def _parse_llm_questions(raw: str, level: int) -> List[Question]:
    questions: List[Question] = []
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        logger.warning("_parse_llm_questions: no JSON array found in LLM output")
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        logger.warning("_parse_llm_questions: JSON parse error: %s", exc)
        return []

    type_map = {
        "scenario_mcq" : QuestionType.MCQ_SINGLE,
        "impact_mcq"   : QuestionType.MCQ_SINGLE,
        "strategy_saq" : QuestionType.SAQ,
        "risk_saq"     : QuestionType.SAQ,
    }

    for i, item in enumerate(data):
        try:
            raw_type  = item.get("type", "scenario_mcq")
            qtype     = type_map.get(raw_type, QuestionType.MCQ_SINGLE)
            question_text = item.get("scenario") or item.get("question") or ""
            q = Question(
                id=f"llm_{level}_{i}",
                level=level,
                type=qtype,
                question=question_text,
                asset_class=item.get("asset_class", ""),
                asset_symbol=item.get("asset_symbol", ""),
                context=item.get("context", ""),
                options=item.get("options", []),
                # No single "correct" answer for scenario/impact MCQs
                correct_answer=None,
                word_limit=item.get("word_limit", 80),
                tags=[raw_type, item.get("reveals", "")],
            )
            questions.append(q)
        except (KeyError, TypeError) as exc:
            logger.debug("_parse_llm_questions: skipping item %d: %s", i, exc)

    return questions


# ---------------------------------------------------------------------------
# QuestionGenerator
# ---------------------------------------------------------------------------

class QuestionGenerator:
    """
    Generates 19 decision-intelligence questions per session.

    Strategy:
      1. LLM generates context-aware, news-driven scenarios if available.
      2. Template bank fills remaining slots (also scenario-based — no trivia).
      3. Questions are shuffled and re-indexed for the session.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client

    def generate(
        self,
        level: int,
        user_id: int,
        context: Optional[MarketContext] = None,
        # Legacy arg kept for backwards compat with Bot/main.py
        asset_context: str = "",
    ) -> List[Question]:
        """Return exactly 19 Question objects for the given level."""
        if context is None:
            context = MarketContext(user_level=level)

        questions: List[Question] = []

        # ── LLM attempt ─────────────────────────────────────────────────────
        if self.llm and self.llm.available:
            try:
                prompt  = _build_generation_prompt(level, context)
                raw     = self.llm.complete(prompt, temperature=0.85, max_tokens=4000)
                llm_qs  = _parse_llm_questions(raw, level)
                questions.extend(llm_qs)
                logger.info(
                    "QuestionGenerator: LLM produced %d questions for level %d",
                    len(llm_qs), level,
                )
            except Exception as exc:
                logger.warning("QuestionGenerator: LLM failed: %s — falling back to templates", exc)

        # ── Template fill ────────────────────────────────────────────────────
        needed = cfg.QUESTIONS_PER_LEVEL - len(questions)
        if needed > 0:
            used_ids = {q.id for q in questions}
            templates = _get_templates(level, needed, exclude_ids=used_ids)
            questions.extend(templates)

        # ── Finalise ─────────────────────────────────────────────────────────
        questions = questions[:cfg.QUESTIONS_PER_LEVEL]
        random.shuffle(questions)

        prefix = f"u{user_id}_l{level}_{uuid.uuid4().hex[:6]}"
        for i, q in enumerate(questions):
            q.id = f"{prefix}_q{i+1:02d}"

        logger.info(
            "QuestionGenerator: serving %d questions for user %d level %d",
            len(questions), user_id, level,
        )
        return questions

    def _from_templates(self, level: int, count: int, exclude_ids: set) -> List[Question]:
        """Legacy internal helper — kept for any external callers."""
        return _get_templates(level, count, exclude_ids)


def _get_templates(level: int, count: int, exclude_ids: set) -> List[Question]:
    pool = [q for q in _TEMPLATE_QUESTIONS if q.level == level and q.id not in exclude_ids]
    if len(pool) < count:
        # Borrow from adjacent levels
        extra = [q for q in _TEMPLATE_QUESTIONS if q.id not in exclude_ids and q not in pool]
        random.shuffle(extra)
        pool.extend(extra)
    random.shuffle(pool)
    return pool[:count]


# ---------------------------------------------------------------------------
# Template Question Bank  — SCENARIO-BASED ONLY (no trivia/definitions)
# ---------------------------------------------------------------------------
# Tags format: [sub_type, reveals_dimension]
# correct_answer = None for all scenario/impact MCQs (no single right answer)
# ---------------------------------------------------------------------------

def _smcq(id_, level, question, options, asset_class, symbol, context="", reveals=""):
    """Convenience builder for scenario_mcq."""
    return Question(
        id=id_, level=level, type=QuestionType.MCQ_SINGLE,
        question=question, options=options,
        correct_answer=None,
        asset_class=asset_class, asset_symbol=symbol,
        context=context, word_limit=0,
        tags=[SCENARIO_MCQ, reveals],
    )

def _imcq(id_, level, question, options, asset_class, symbol, context=""):
    """Convenience builder for impact_mcq."""
    return Question(
        id=id_, level=level, type=QuestionType.MCQ_SINGLE,
        question=question, options=options,
        correct_answer=None,
        asset_class=asset_class, asset_symbol=symbol,
        context=context, word_limit=0,
        tags=[IMPACT_MCQ, "macro_awareness"],
    )

def _ssaq(id_, level, question, asset_class, symbol, context="", word_limit=80):
    """Convenience builder for strategy_saq."""
    return Question(
        id=id_, level=level, type=QuestionType.SAQ,
        question=question, options=[],
        correct_answer=None,
        asset_class=asset_class, asset_symbol=symbol,
        context=context, word_limit=word_limit,
        tags=[STRATEGY_SAQ, "synthesis"],
    )

def _rsaq(id_, level, question, asset_class, symbol, context="", word_limit=80):
    """Convenience builder for risk_saq."""
    return Question(
        id=id_, level=level, type=QuestionType.SAQ,
        question=question, options=[],
        correct_answer=None,
        asset_class=asset_class, asset_symbol=symbol,
        context=context, word_limit=word_limit,
        tags=[RISK_SAQ, "risk_management"],
    )


_OPT_SCENARIO = [
    "🟢 Sell immediately — lock in gains / cut losses",
    "🟡 Scale out 50% — secure partial profit / reduce risk",
    "🔵 Hold and reassess — wait for next candle / confirmation",
    "🟣 Add to position — conviction unchanged, better price",
    "🔴 Hedge with options — buy puts / sell calls to protect",
]

_OPT_IMPACT = [
    "🟢 Strongly bullish — significant upside move expected",
    "🟡 Mildly bullish — small positive drift",
    "⚪ Neutral — already priced in by the market",
    "🟠 Mildly bearish — mild selloff likely",
    "🔴 Strongly bearish — sharp downside move expected",
]

_TEMPLATE_QUESTIONS: List[Question] = [

    # ══════════════════════════════════════════════════════════════════════════
    # LEVEL 1 — Beginner scenarios (single-asset, one clear news event)
    # ══════════════════════════════════════════════════════════════════════════

    # ── Scenario MCQs (10) ────────────────────────────────────────────────────
    _smcq("t1_s01", 1,
        "📊 You bought 10 shares of Infosys at ₹1,400. It's now ₹1,350 (-3.5%).\n"
        "📰 NEWS: Q4 earnings miss — revenue growth 6% vs 12% expected.\n"
        "The stock is below its 50-day moving average. What is your PRIMARY action?",
        ["🟢 Sell all — earnings miss is a fundamental deterioration",
         "🟡 Sell half — reduce risk but keep some exposure",
         "🔵 Hold — one quarter doesn't change the long-term story",
         "🟣 Buy more — price dip is an opportunity if you believe in the company",
         "🔴 Set a stop-loss at ₹1,320 — let price decide"],
        "Stocks", "INFY",
        "Reveals: How you handle fundamental bad news vs. price action signals.",
        "loss_response"),

    _smcq("t1_s02", 1,
        "📊 You hold 5 units of NIFTY ETF at ₹220. It rises to ₹240 (+9%) in 3 weeks.\n"
        "📰 NEWS: RBI holds rates steady. FII inflows at 3-month high.\n"
        "RSI just crossed 72 (overbought zone). What do you do?",
        ["🟢 Sell all — RSI overbought, take profits now",
         "🟡 Sell half — bank profits on 50%, hold rest for more upside",
         "🔵 Hold — FII flow momentum can push RSI higher",
         "🟣 Buy more — FII buying is strong confirmation",
         "🔴 Set trailing stop at ₹230 — let winners run with protection"],
        "ETFs", "NIFTYBEES",
        "Reveals: Technical vs. momentum trading style. Profit-taking discipline.",
        "profit_taking"),

    _smcq("t1_s03", 1,
        "📊 You hold 0.1 BTC at $62,000. BTC drops to $56,000 (-9%) in 24 hours.\n"
        "📰 NEWS: Major crypto exchange reports $500M hack. Market-wide panic selling.\n"
        "Your unrealised loss is $600. What is your PRIMARY action?",
        ["🟢 Sell — exchange hack signals systemic risk, exit the sector",
         "🟡 Sell half — reduce exposure during uncertainty",
         "🔵 Hold — exchange-specific risk, BTC network itself is unaffected",
         "🟣 Buy more — panic selloff is overreaction, accumulate at discount",
         "🔴 Wait for a daily close above $58,000 before deciding"],
        "Crypto", "BTC",
        "Reveals: Ability to distinguish systemic vs. idiosyncratic risk.",
        "risk_differentiation"),

    _smcq("t1_s04", 1,
        "📊 You have ₹50,000 in cash, watching Reliance Industries at ₹2,800.\n"
        "📰 NEWS: Reliance announces ₹75,000 crore new energy investment over 3 years.\n"
        "Stock jumps 4% at market open. What do you do?",
        ["🟢 Buy immediately — big strategic investment is bullish long term",
         "🟡 Wait for the gap to partially fill before buying",
         "🔵 Watch for 2-3 days — let the news settle before entering",
         "🟣 Skip this trade — 4% gap already prices in the news",
         "🔴 Short it — 'buy the rumor, sell the news' pattern"],
        "Stocks", "RELIANCE",
        "Reveals: Entry timing style — momentum chaser vs. patient buyer.",
        "entry_timing"),

    _smcq("t1_s05", 1,
        "📊 You hold Gold ETF (GLD) worth $2,000. Gold is at $1,950/oz.\n"
        "📰 NEWS: US CPI comes in at 4.2% — higher than 3.8% expected.\n"
        "Gold spikes 1.5% immediately. What is your PRIMARY action?",
        ["🟢 Sell — gold already ran, take profit before it reverses",
         "🟡 Hold — inflation data confirms gold's safe-haven thesis",
         "🔵 Buy more — high inflation environment is structurally bullish for gold",
         "🟣 Wait — CPI data alone is not enough, watch Fed response",
         "🔴 Sell and rotate into TIPS (inflation-linked bonds) instead"],
        "ETFs", "GLD",
        "Reveals: Inflation macro understanding. Gold allocation conviction.",
        "macro_response"),

    _smcq("t1_s06", 1,
        "📊 You shorted 10 shares of a midcap IT company at ₹500. It's now ₹480.\n"
        "📰 NEWS: Unexpected deal win announced — stock jumps 8% to ₹518.\n"
        "Your short is now underwater by ₹180. What do you do?",
        ["🟢 Cover immediately — the thesis is broken, take the loss",
         "🟡 Cover half — manage risk but keep some short if you still believe",
         "🔵 Hold — one deal doesn't change the fundamental weakness",
         "🟣 Add to the short — stock is now even more overvalued",
         "🔴 Set a stop at ₹530 — give it room but cap maximum loss"],
        "Stocks", "MIDCAPIT",
        "Reveals: Ability to accept being wrong. Stop-loss discipline.",
        "loss_acceptance"),

    _smcq("t1_s07", 1,
        "📊 You hold Wheat commodity ETF. Wheat is at $650/bushel.\n"
        "📰 NEWS: Major drought warning in US Midwest — crop yield forecast cut 15%.\n"
        "Wheat futures already up 6% this week. Do you:",
        ["🟢 Buy more — supply shock thesis is strengthening",
         "🟡 Hold existing position — already well positioned",
         "🔵 Take profit — 6% weekly gain, consolidation likely",
         "🟣 Sell — drought fears may be overstated, weather can change",
         "🔴 Wait for weekly close to confirm the breakout before adding"],
        "Commodities", "WHEAT",
        "Reveals: Commodity supply-shock response. Momentum vs. mean-reversion.",
        "supply_shock"),

    _smcq("t1_s08", 1,
        "📊 You hold 100 units of SPY at $475. SPY drops to $458 (-3.6%) on Monday open.\n"
        "📰 NEWS: US non-farm payrolls miss by 150k — weakest in 18 months.\n"
        "Your portfolio is down $1,700. Markets are highly volatile. What do you do?",
        ["🟢 Sell SPY — weak jobs data signals economic slowdown, reduce risk",
         "🟡 Hold — one month's data doesn't change the trend",
         "🔵 Buy more — weak jobs could mean the Fed cuts rates, which is bullish for equities",
         "🟣 Hedge with TLT (long bonds) — rotation into safety",
         "🔴 Do nothing — you're a long-term investor, ignore short-term noise"],
        "ETFs", "SPY",
        "Reveals: Economic data interpretation. Bull vs. bear signal reading.",
        "data_interpretation"),

    _smcq("t1_s09", 1,
        "📊 You're watching Tata Motors at ₹900. You haven't bought yet.\n"
        "📰 NEWS: Jaguar Land Rover reports record UK sales. Tata Motors up 7% yesterday.\n"
        "Today it opens flat. Volume is 50% below average. Do you:",
        ["🟢 Buy today — JLR news is strong, any dip is an opportunity",
         "🟡 Wait for a pullback to ₹850-860 before entering",
         "🔵 Skip — you missed the move, next entry needs a new catalyst",
         "🟣 Buy a small starter position, add more on confirmation",
         "🔴 Short it — the move is exhausted, gap-fill to ₹850 likely"],
        "Stocks", "TATAMOTORS",
        "Reveals: FOMO management. Entry discipline after a big move.",
        "fomo_discipline"),

    _smcq("t1_s10", 1,
        "📊 You hold ETH at $3,200. ETH is up 45% in the past month.\n"
        "📰 NEWS: Ethereum network upgrade delayed by 6 weeks due to bugs.\n"
        "ETH drops 8% in 4 hours on the news. What is your PRIMARY action?",
        ["🟢 Sell — technical delay signals execution risk, take profits",
         "🟡 Sell 30% — reduce exposure but stay invested for the upgrade",
         "🔵 Hold — delay is temporary, fundamentals unchanged",
         "🟣 Buy the dip — network upgrade will happen, this is a gift",
         "🔴 Set alerts at $2,900 and $3,000 support; decide then"],
        "Crypto", "ETH",
        "Reveals: How you handle negative news against an existing profitable position.",
        "profit_protection"),

    # ── Impact MCQs (5) ───────────────────────────────────────────────────────
    _imcq("t1_i01", 1,
        "📰 NEWS: RBI surprises market with a 25bps rate CUT.\n"
        "🏭 ASSET: HDFC Bank (HDFCBANK) — currently at ₹1,680.\n"
        "Key levels: Support ₹1,620 | Resistance ₹1,750.\n"
        "What is your impact assessment for HDFC Bank over the next 5 trading days?",
        ["🟢 Strongly bullish — rate cuts expand NIM and boost credit demand",
         "🟡 Mildly bullish — positive but NIM compression offsets loan growth",
         "⚪ Neutral — rate cut already anticipated, priced in",
         "🟠 Mildly bearish — rate cuts signal economic weakness",
         "🔴 Strongly bearish — bank stocks rally then sharply reverse"],
        "Stocks", "HDFCBANK",
        "Reveals: Understanding of bank economics vs. macro signals."),

    _imcq("t1_i02", 1,
        "📰 NEWS: OPEC+ agrees to extend production cuts of 500k bbl/day for another quarter.\n"
        "🏭 ASSET: WTI Crude Oil Futures — currently at $76/bbl.\n"
        "Key levels: Support $72 | Resistance $82 | 52W high $89.\n"
        "What is your impact assessment for WTI over the next 2 weeks?",
        _OPT_IMPACT,
        "Commodities", "WTI",
        "Reveals: Supply-demand intuition. OPEC policy understanding."),

    _imcq("t1_i03", 1,
        "📰 NEWS: US Fed Chair says 'no rate cuts planned until inflation is sustainably at 2%'.\n"
        "🏭 ASSET: SPY (S&P 500 ETF) — currently at $480.\n"
        "Key levels: 50-day MA $472 | 200-day MA $455.\n"
        "What is your impact assessment for SPY over the next week?",
        _OPT_IMPACT,
        "ETFs", "SPY",
        "Reveals: Fed policy → equity market transmission understanding."),

    _imcq("t1_i04", 1,
        "📰 NEWS: China factory PMI drops to 48.2 (below 50 = contraction) for 3rd straight month.\n"
        "🏭 ASSET: Copper Futures (HG1!) — currently at $3.85/lb.\n"
        "Key levels: Support $3.70 | Resistance $4.00. China imports 55% of global copper.\n"
        "What is your impact assessment for Copper over the next month?",
        _OPT_IMPACT,
        "Commodities", "COPPER",
        "Reveals: China-commodity linkage awareness."),

    _imcq("t1_i05", 1,
        "📰 NEWS: Bitcoin ETF daily inflows hit $1.2B — highest since launch.\n"
        "🏭 ASSET: BTC — currently at $68,000.\n"
        "Key levels: Resistance $72,000 (ATH) | Support $63,000.\n"
        "What is your impact assessment for BTC over the next 72 hours?",
        _OPT_IMPACT,
        "Crypto", "BTC",
        "Reveals: ETF flow → spot price understanding. Crypto market microstructure."),

    # ── Strategy SAQs (2) ─────────────────────────────────────────────────────
    _ssaq("t1_saq01", 1,
        "📊 MARKET: NIFTY 50 at 22,800 (+2% this week). VIX at 14 (low).\n"
        "📰 NEWS: IT sector Q4 results beat expectations. Pharma sector weak on US FDA concerns.\n"
        "You have ₹1,00,000 to invest for 3 months.\n"
        "Which 2 sectors would you allocate to and why? What is your entry plan?",
        "Stocks", "NIFTY",
        "Context: You are a retail investor with basic market access.",
        word_limit=80),

    _ssaq("t1_saq02", 1,
        "📊 MARKET: BTC at $65,000. ETH at $3,400. Crypto market cap up 35% YTD.\n"
        "📰 NEWS: US SEC approves spot ETH ETF application. Institutional buying accelerating.\n"
        "You have $5,000 to allocate in crypto for 1 month.\n"
        "What is your specific plan? Include which assets, how much to each, and your exit strategy.",
        "Crypto", "ETH",
        "Context: Moderate risk tolerance. Can handle 20% drawdown.",
        word_limit=80),

    # ── Risk SAQs (2) ─────────────────────────────────────────────────────────
    _rsaq("t1_raq01", 1,
        "⚠️ RISK SIGNAL: You bought Tata Steel at ₹150. It's now ₹108 (-28%).\n"
        "📰 NEWS: Global steel prices down 20% due to China oversupply. No recovery signal visible.\n"
        "Your portfolio: 60% Tata Steel, 40% Cash.\n"
        "How do you handle this position going forward? What is your decision framework?",
        "Stocks", "TATASTEEL",
        "Context: You originally bought on India infrastructure story.",
        word_limit=80),

    _rsaq("t1_raq02", 1,
        "⚠️ RISK SIGNAL: Your portfolio dropped 15% in 2 weeks.\n"
        "Allocation: 50% midcap stocks, 30% crypto, 20% cash.\n"
        "📰 NEWS: Global recession fears. FII outflows from India 8 days in a row. VIX at 28.\n"
        "What specific actions do you take to protect your remaining capital?",
        "ETFs", "NIFTY",
        "Context: You have a 6-month investment horizon.",
        word_limit=80),


    # ══════════════════════════════════════════════════════════════════════════
    # LEVEL 2 — Intermediate (multi-factor, options basics, sector rotation)
    # ══════════════════════════════════════════════════════════════════════════

    _smcq("t2_s01", 2,
        "📊 You hold a long NIFTY Bank call option (strike 48,000, expiry 3 weeks).\n"
        "Bank Nifty is at 47,600. Your option is worth ₹120 (paid ₹90).\n"
        "📰 NEWS: RBI policy meet tomorrow — rate decision uncertain. IV spikes to 22%.\n"
        "What do you do with your option position before the event?",
        ["🟢 Hold through the event — you expect a bullish surprise",
         "🟡 Book 50% profit now — reduce risk before binary event",
         "🔵 Buy an equal put as a straddle — profit from any big move",
         "🟣 Sell and re-enter after the announcement",
         "🔴 Add more calls — high IV makes them expensive but conviction is high"],
        "Futures", "BANKNIFTY",
        "Reveals: Binary event risk management. Options vs. equity discipline.",
        "event_risk"),

    _smcq("t2_s02", 2,
        "📊 You hold 500 shares of HDFC Bank at ₹1,600 (current ₹1,720, +7.5%).\n"
        "📰 NEWS: MACD shows bearish crossover. Bollinger Band upper reached. Volume declining.\n"
        "Macro: FII net sellers last 3 sessions. Q1 earnings next week.\n"
        "What is your PRIMARY action?",
        ["🟢 Sell all — technical + FII data confirm weakness ahead",
         "🟡 Sell 40% and hold rest through earnings",
         "🔵 Hold — earnings catalyst could push higher",
         "🟣 Buy protective puts for earnings hedge",
         "🔴 Do nothing — technical signals are lagging, not leading"],
        "Stocks", "HDFCBANK",
        "Reveals: Technical signal + fundamental event weighing.",
        "signal_synthesis"),

    _smcq("t2_s03", 2,
        "📊 You're 30% in cash. Sector rotation analysis shows money moving out of IT into Pharma.\n"
        "📰 NEWS: US FDA clears 3 ANDA filings for Dr. Reddy's. Sun Pharma Q4 beats 20%.\n"
        "NIFTY Pharma index at 52-week high. What do you do with your cash allocation?",
        ["🟢 Deploy 80% into Pharma — sector momentum is clear",
         "🟡 Deploy 40% into Pharma — cautious entry at 52W high",
         "🔵 Wait for a pullback — entering at 52W high is poor risk/reward",
         "🟣 Buy the IT laggards instead — sector rotation creates buying opportunities",
         "🔴 Stay in cash — 52W highs in any sector mean limited upside"],
        "Stocks", "SUNPHARMA",
        "Reveals: Sector rotation execution timing. Risk/reward at breakouts.",
        "sector_rotation"),

    _smcq("t2_s04", 2,
        "📊 You're short USDINR at 83.50 (rupee appreciation bet). Rupee is now at 83.20.\n"
        "📰 NEWS: India's trade deficit widens to $23B — 18-month high. USD starts to strengthen globally.\n"
        "Your position has a small profit. What do you do?",
        ["🟢 Close — trade deficit is structural headwind for rupee, close while profitable",
         "🟡 Hold half — rupee can stay stable if RBI intervenes",
         "🔵 Hold all — short-term data noise, FII flows are still supportive",
         "🟣 Add to the short — dollar strength is a global trend",
         "🔴 Reverse to long USDINR — trade deficit + strong dollar = rupee weakness"],
        "Futures", "USDINR",
        "Reveals: Currency macro reasoning. Willingness to reverse thesis.",
        "thesis_reversal"),

    _smcq("t2_s05", 2,
        "📊 You hold Brent Crude futures long at $80/bbl. Brent rises to $87/bbl (+8.75%).\n"
        "📰 NEWS: Houthi attacks intensify in Red Sea — shipping delays. OPEC+ meeting in 10 days.\n"
        "Bollinger Bands show upper band stretch. RSI at 74. What do you do?",
        ["🟢 Hold — geopolitical supply risk can push to $95+",
         "🟡 Take 60% profit — RSI overbought, OPEC meeting is a risk event",
         "🔵 Take full profit — geopolitical events are unpredictable, lock in gains",
         "🟣 Roll to a higher strike call option — reduce capital at risk while maintaining upside",
         "🔴 Short — overbought conditions + OPEC supply risk = reversal imminent"],
        "Commodities", "BRENT",
        "Reveals: Geopolitical risk premium assessment. Overbought handling.",
        "geopolitical_premium"),

    _smcq("t2_s06", 2,
        "📊 You're flat (no position). QQQ (Nasdaq ETF) at $430. 200-day MA: $405.\n"
        "📰 NEWS: Nvidia earnings beat by 40%. Guidance raised. Stock +15% after hours.\n"
        "QQQ poised to open +3% tomorrow. Do you:",
        ["🟢 Buy QQQ at open — Nvidia drives 6% of QQQ, mega-cap tech rally coming",
         "🟡 Wait for the open gap to partially fill before buying",
         "🔵 Buy individual chip stocks (AMD, AVGO) — more direct exposure than QQQ",
         "🟣 Skip — earnings are priced in, sell the news likely",
         "🔴 Buy puts on QQQ — gap up is exhaustion signal, fade the move"],
        "ETFs", "QQQ",
        "Reveals: Earnings response strategy. Index vs. single-stock exposure preference.",
        "earnings_response"),

    _smcq("t2_s07", 2,
        "📊 You hold 2 ETH at $3,500. ETH dominance is rising. BTC at $68,000.\n"
        "📰 NEWS: Ethereum staking yield drops from 4.2% to 3.1% as more validators join.\n"
        "ETH/BTC ratio is at 0.052 — 6-month high. What is your PRIMARY action?",
        ["🟢 Hold — rising ETH dominance and ETH/BTC ratio are bullish signals",
         "🟡 Sell 1 ETH and rotate to BTC — lower staking yield reduces ETH's value proposition",
         "🔵 Hold ETH and sell into any spike above $3,800",
         "🟣 Buy more ETH — more validators means more network adoption, bullish",
         "🔴 Sell all and wait — staking yield compression + high ETH/BTC = top signal"],
        "Crypto", "ETH",
        "Reveals: Staking dynamics understanding. Cross-asset crypto rotation.",
        "yield_vs_price"),

    _smcq("t2_s08", 2,
        "📊 NIFTY 50 breaks out above 24,000 for the first time. VIX drops to 11.5.\n"
        "📰 NEWS: India Q4 GDP 8.6% — beats estimates. GST collections record high.\n"
        "FII bought ₹12,000 crore this week. Your portfolio: 60% equity, 40% cash.\n"
        "Do you deploy your cash now?",
        ["🟢 Deploy 80% — macro data + FII flow + breakout is a clear buy signal",
         "🟡 Deploy 40% — cautious given the all-time high; scale in gradually",
         "🔵 Wait for a retest of 23,500 before deploying",
         "🟣 Deploy 100% — don't fight the trend; FOMO costs more than buying ATH",
         "🔴 Stay in cash — ATH breakouts are traps, wait for consolidation"],
        "ETFs", "NIFTY",
        "Reveals: ATH deployment psychology. Macro conviction vs. price caution.",
        "ath_psychology"),

    _smcq("t2_s09", 2,
        "📊 You're holding a covered call position: Long 100 Reliance @ ₹2,600, Short ₹2,700 call.\n"
        "📰 NEWS: Saudi Aramco partners with Reliance for $2B petrochemical deal.\n"
        "Reliance spikes to ₹2,750, breaching your short call strike.\n"
        "Your stock is being called away at ₹2,700. What is your reaction?",
        ["🟢 Accept it — you collected premium, ₹2,700 was your target anyway",
         "🟡 Buy back the call at a loss to keep the stock",
         "🔵 Roll the call to a higher strike — buy back ₹2,700, sell ₹2,900",
         "🟣 Let it happen and immediately re-enter at market price",
         "🔴 Regret the covered call — should have just held the stock"],
        "Stocks", "RELIANCE",
        "Reveals: Options strategy discipline. Understanding covered call payoff.",
        "options_discipline"),

    _smcq("t2_s10", 2,
        "📊 You're watching Silver at $26/oz. Gold/Silver ratio is at 85 (historically: 60-70).\n"
        "📰 NEWS: US manufacturing PMI beats at 52.8. EV battery demand for silver upgrades.\n"
        "Silver has been underperforming gold for 6 months. Do you:",
        ["🟢 Buy silver — ratio is stretched, mean reversion + industrial demand",
         "🟡 Buy a small position — interesting thesis but timing is unclear",
         "🔵 Wait — ratio can stay extreme for years, need a catalyst",
         "🟣 Sell gold and buy silver — pair trade on ratio normalisation",
         "🔴 Avoid — prefer equities over commodities in manufacturing upturn"],
        "Commodities", "SILVER",
        "Reveals: Relative value / ratio trading understanding.",
        "relative_value"),

    # ── Impact MCQs ───────────────────────────────────────────────────────────
    _imcq("t2_i01", 2,
        "📰 NEWS: MACD on NIFTY Bank Index shows bearish crossover after 8-week bull run.\n"
        "Bollinger Bands: price just touched upper band. RSI: 71.\n"
        "🏭 ASSET: Bank Nifty Futures — currently at 48,200.\n"
        "Key levels: Support 46,800 | Resistance 49,500.\n"
        "What is your technical assessment for the next 5 sessions?",
        ["🟢 Strongly bullish — momentum is strong, MACD crossovers can be false",
         "🟡 Mildly bullish — drift higher but pace of gains slowing",
         "⚪ Neutral — rangebound between 47,000-49,000",
         "🟠 Mildly bearish — pullback to 47,000 area likely",
         "🔴 Strongly bearish — sharp correction to 46,000 possible"],
        "Futures", "BANKNIFTY",
        "Reveals: Technical signal interpretation under real conditions."),

    _imcq("t2_i02", 2,
        "📰 NEWS: US CPI at 3.8% — higher than 3.5% expected. Probability of rate cut in June falls from 65% to 28%.\n"
        "🏭 ASSET: TLT (20+ Year Treasury Bond ETF) — currently at $95.\n"
        "Key levels: Support $91 | Recent high $101.\n"
        "What is your impact assessment for TLT?",
        _OPT_IMPACT,
        "ETFs", "TLT",
        "Reveals: Interest rate → bond price mechanics."),

    _imcq("t2_i03", 2,
        "📰 NEWS: SEC launches investigation into Binance for alleged market manipulation.\n"
        "🏭 ASSET: BNB (Binance Coin) — currently at $420.\n"
        "Key levels: Support $380 | 200-day MA $350.\n"
        "What is your impact assessment for BNB over the next 2 weeks?",
        _OPT_IMPACT,
        "Crypto", "BNB",
        "Reveals: Regulatory risk impact on native exchange tokens."),

    _imcq("t2_i04", 2,
        "📰 NEWS: India's PMI Manufacturing jumps to 57.8 — 15-year high. Capex cycle accelerating.\n"
        "🏭 ASSET: Nifty Smallcap 100 Index — currently at 16,800.\n"
        "Key levels: 52W high 17,200 | 200-day MA 14,500.\n"
        "What is your impact assessment for smallcaps over the next month?",
        _OPT_IMPACT,
        "Stocks", "NIFTYSMLCAP",
        "Reveals: PMI → smallcap connection. Capex cycle awareness."),

    _imcq("t2_i05", 2,
        "📰 NEWS: Natural gas inventories 18% above 5-year average. Winter demand forecast cut.\n"
        "🏭 ASSET: Natural Gas Futures (NG1!) — currently at $2.40/MMBtu.\n"
        "Key levels: Support $2.10 | Resistance $2.80.\n"
        "What is your impact assessment for Natural Gas?",
        _OPT_IMPACT,
        "Commodities", "NATGAS",
        "Reveals: Supply inventory → commodity price direction."),

    # ── Strategy SAQs ─────────────────────────────────────────────────────────
    _ssaq("t2_saq01", 2,
        "📊 MARKET STATE: NIFTY at 24,500. VIX at 16. FIIs net buyers 5 consecutive sessions.\n"
        "📰 NEWS: Q4 GDP 8.4%. US Fed signals H2 rate cuts. IT sector +3% this week.\n"
        "You have ₹5,00,000 to deploy over the next 2 weeks.\n"
        "Detail: (1) Which 2-3 sectors and why, (2) Lump sum or staggered entry?, "
        "(3) Where do you place stops?",
        "Stocks", "NIFTY",
        "Context: You have a 3-month investment horizon and medium risk tolerance.",
        word_limit=100),

    _ssaq("t2_saq02", 2,
        "📊 MARKET: BTC at $67,000 (+40% past 60 days). ETH at $3,600. SOL at $180.\n"
        "📰 NEWS: US spot ETH ETF approval expected within 30 days. Crypto fear/greed index: 82 (Greed).\n"
        "You want to play the ETH ETF catalyst with $10,000.\n"
        "Outline: asset selection, entry levels, position sizing, and how you manage the event risk.",
        "Crypto", "ETH",
        "Context: You can tolerate 30% drawdown. Time horizon: 60 days.",
        word_limit=100),

    # ── Risk SAQs ─────────────────────────────────────────────────────────────
    _rsaq("t2_raq01", 2,
        "⚠️ RISK SIGNAL: Your portfolio has rallied 42% in 8 months.\n"
        "Current allocation: 50% NIFTY midcap, 25% Crypto (BTC/ETH), 20% IT stocks, 5% Cash.\n"
        "📰 NEWS: Global bond yields rising. USD strengthening. FII starting to reduce India exposure.\n"
        "Do you lock in gains and how do you reposition for a risk-off environment?",
        "ETFs", "NIFTY",
        "Context: You have a capital gains tax event if you sell within 12 months.",
        word_limit=100),

    _rsaq("t2_raq02", 2,
        "⚠️ RISK SIGNAL: MACD bearish divergence on weekly Nifty chart. RSI declining from 74.\n"
        "You hold: 3 Nifty Futures contracts (lot size 50) at 24,200. Current Nifty: 23,950.\n"
        "Overnight news: US credit downgrade by Fitch. SGX Nifty futures down 1.2%.\n"
        "How do you manage your futures position at tomorrow's market open?",
        "Futures", "NIFTY",
        "Context: Each 100-point Nifty move = ₹15,000 P&L on your position.",
        word_limit=100),


    # ══════════════════════════════════════════════════════════════════════════
    # LEVEL 3 — Advanced (Greeks, vol surface, cross-asset, derivatives)
    # ══════════════════════════════════════════════════════════════════════════

    _smcq("t3_s01", 3,
        "📊 You are delta-neutral: Long 10 Nifty ATM straddles (24,000 strike, 7 DTE).\n"
        "Gamma is +350. Theta is -₹4,200/day. Nifty moves to 24,450 (+1.87%) in one session.\n"
        "📰 NEWS: Surprise RBI rate cut announcement — volatility expected to persist.\n"
        "Your straddle is now +₹18,000. What do you do?",
        ["🟢 Close 50% — strong move, take profit before theta destroys value",
         "🟡 Hold — RBI news suggests more volatility, straddle has more to give",
         "🔵 Re-centre the straddle — sell the 24,000s, buy 24,500 straddle",
         "🟣 Sell puts to convert to a long call — directionally bias upward",
         "🔴 Add more straddles — volatility regime is changing, compound the trade"],
        "Futures", "NIFTY",
        "Reveals: Gamma scalping vs. theta management. Event vol extension logic.",
        "gamma_theta_tradeoff"),

    _smcq("t3_s02", 3,
        "📊 You sold a NIFTY 24,500 Call for ₹180 premium (short call). Nifty is at 24,100.\n"
        "The call's delta is 0.28. Vega is +12. Expiry in 14 days.\n"
        "📰 NEWS: US CPI comes in hot. India VIX spikes from 14 to 19 (+35%) in one day.\n"
        "Your short call is now worth ₹240. Loss = ₹60 per lot. What do you do?",
        ["🟢 Buy it back immediately — vega spike will continue with high VIX",
         "🟡 Hold — IV will mean-revert; wait for VIX to settle",
         "🔵 Roll to a higher strike (25,000 call) — same premium, less delta risk",
         "🟣 Add a long 24,000 call to convert to a bull call spread — limit further loss",
         "🔴 Do nothing — time decay (theta) will eventually work in your favour"],
        "Futures", "NIFTY",
        "Reveals: Vega exposure management. Short vol discipline under spike.",
        "short_vega_management"),

    _smcq("t3_s03", 3,
        "📊 You hold an OTM BTC put (strike $58,000, BTC at $65,000). Premium paid: $800. DTE: 21.\n"
        "BTC rallies to $70,000. Your put is now worth $120 (down 85%).\n"
        "📰 NEWS: Crypto sentiment index at 88 (Extreme Greed). Open interest at all-time high.\n"
        "What do you do with the near-worthless put?",
        ["🟢 Close the put — cut the loss, don't let it go to zero",
         "🟡 Hold — extreme greed + high OI is a classic top signal, put could recover",
         "🔵 Roll to a higher strike put — pay more but get a closer-to-ATM hedge",
         "🟣 Buy more puts — this is the exact moment to be contrarian and hedge",
         "🔴 Let it expire — the premium is already lost, not worth commission"],
        "Crypto", "BTC",
        "Reveals: Contrarian thinking at extremes. Sunk cost vs. hedge value.",
        "contrarian_hedge"),

    _smcq("t3_s04", 3,
        "📊 You hold a long calendar spread: Short June Nifty 24,000 call, Long September 24,000 call.\n"
        "You are positive theta and positive vega. Nifty is at 23,900.\n"
        "📰 NEWS: India elections called for June 15. Market vol expected to spike. VIX at 21.\n"
        "The election date overlaps your short June expiry. How do you manage?",
        ["🟢 Close the entire spread — election vol risk is unpredictable",
         "🟡 Close only the short June call — convert to long theta position",
         "🔵 Hold — election vol benefits your long vega position",
         "🟣 Roll the short to a higher strike — collect more premium, reduce directional risk",
         "🔴 Add a short July call — create a diagonal spread to buffer election risk"],
        "Futures", "NIFTY",
        "Reveals: Calendar spread management around event risk. Vega exposure control.",
        "calendar_event_risk"),

    _smcq("t3_s05", 3,
        "📊 Copper futures: $4.10/lb (+12% past month). Your long from $3.70.\n"
        "📰 NEWS: China announces $300B infrastructure stimulus. Copper demand upgrade.\n"
        "Goldman Sachs raises 12-month copper target to $5.50/lb.\n"
        "Backwardation: Spot $4.10, 3-month $3.95, 6-month $3.80. What do you do?",
        ["🟢 Hold and add — stimulus + analyst upgrades = sustained bull run",
         "🟡 Take partial profit but stay long via call options instead",
         "🔵 Exit spot, buy 6-month calls — backwardation means roll cost is a drag",
         "🟣 Hold — backwardation shows strong immediate demand, fundamental support",
         "🔴 Exit — backwardation + analyst euphoria = price peak signal"],
        "Commodities", "COPPER",
        "Reveals: Futures curve structure (backwardation) impact on carry cost.",
        "backwardation_carry"),

    _smcq("t3_s06", 3,
        "📊 You hold a long-short equity position: Long HDFC Bank, Short Yes Bank (ratio 2:1).\n"
        "HDFC Bank +3%. Yes Bank +8% (bad loan provisions better than feared).\n"
        "📰 NEWS: RBI gives Yes Bank clean chit on governance. Short squeeze underway.\n"
        "Your pair trade is underwater -5%. What do you do?",
        ["🟢 Close both sides — Yes Bank news fundamentally breaks the short thesis",
         "🟡 Close the Yes Bank short only — keep HDFC Bank long",
         "🔵 Hold — short squeezes are temporary, reassess in 48 hours",
         "🟣 Add to both sides — your relative value thesis is still intact",
         "🔴 Reverse — go long Yes Bank, short HDFC Bank"],
        "Stocks", "YESBANK",
        "Reveals: Long-short pair trade discipline. Thesis vs. price-based exit.",
        "pair_trade_exit"),

    _smcq("t3_s07", 3,
        "📊 Vol surface analysis: NIFTY 1-month ATM IV = 14%. OTM put skew (25Δ) = 19%.\n"
        "Historical vol (30-day realised) = 10%.\n"
        "📰 NEWS: Market calm. Elections 3 months away. FII inflows stable.\n"
        "The vol risk premium is 40% (IV vs. realised). How do you trade this?",
        ["🟢 Sell strangles — IV is expensive vs. realised vol, collect premium",
         "🟡 Buy the dip in vol — calm markets eventually break",
         "🔵 Sell ATM but buy OTM puts — capture vol premium but keep tail protection",
         "🟣 Do nothing — vol premium can persist for months in calm markets",
         "🔴 Buy OTM puts only — skew is too high, election risk is underpriced"],
        "Futures", "NIFTY",
        "Reveals: Vol risk premium exploitation. Skew interpretation.",
        "vol_risk_premium"),

    _smcq("t3_s08", 3,
        "📊 You're long Gold (GLD) and short USD (via UUP). Classic inverse correlation play.\n"
        "Gold: $1,980/oz. DXY: 104.5. Both moving TOGETHER upward this week — correlation breaks.\n"
        "📰 NEWS: Geopolitical crisis — Russia-Ukraine escalation. Flight to safety in BOTH gold AND USD.\n"
        "Your long-short is flat. What do you do?",
        ["🟢 Close the short USD — flight-to-safety is a special regime, both assets rise",
         "🟡 Hold — correlation break is temporary, it will revert",
         "🔵 Close both — regime uncertainty makes the pair trade unstable",
         "🟣 Add to long Gold — geopolitical crisis benefits gold specifically",
         "🔴 Add to the short USD — gold will eventually win the flight-to-safety bid"],
        "Commodities", "GOLD",
        "Reveals: Correlation regime awareness. Crisis vs. normal market dynamics.",
        "correlation_break"),

    _smcq("t3_s09", 3,
        "📊 You run a momentum strategy. NIFTY Midcap 150: highest 52W momentum stocks signalling buy.\n"
        "The top 10 momentum stocks are all in Defense, Railway, PSU sectors.\n"
        "📰 NEWS: Government capex cut 20% in budget revision. Election spending priorities shift.\n"
        "Your momentum model still shows BUY signals for these stocks. What do you do?",
        ["🟢 Follow the model — momentum is a systematic signal, override is dangerous",
         "🟡 Reduce position size by 50% — fundamental override on capex cut",
         "🔵 Pause the strategy — macro override justified when policy directly targets your sector",
         "🟣 Run the full trade — capex cut news may already be priced into the recent correction",
         "🔴 Reverse — short the momentum basket, news is catastrophically negative"],
        "Stocks", "DEFENSEIND",
        "Reveals: Systematic vs. discretionary conflict. Macro override judgment.",
        "model_override"),

    _smcq("t3_s10", 3,
        "📊 You hold an OTM iron condor on NIFTY: Short 23,500P / Long 23,000P // Short 24,500C / Long 25,000C.\n"
        "Net credit received: ₹120. NIFTY at 24,000. 10 DTE.\n"
        "📰 NEWS: US Fed FOMC minutes release tonight — uncertainty high. NIFTY VIX up to 18.\n"
        "Your condor has ₹80 of value left. Max profit at expiry. What do you do?",
        ["🟢 Close at ₹80 — lock 33% profit (₹120-₹80=₹40 net), don't risk FOMC",
         "🟡 Hold — NIFTY is centred in the profitable zone, FOMC is US-specific",
         "🔵 Close the call side only — FOMC is more likely to cause upside than downside",
         "🟣 Hold through FOMC and close tomorrow morning",
         "🔴 Close the put side only — dollar strength = INR pressure = NIFTY downside"],
        "Futures", "NIFTY",
        "Reveals: Iron condor management before binary events. Early exit vs. theta collection.",
        "condor_event_management"),

    # ── Impact MCQs ───────────────────────────────────────────────────────────
    _imcq("t3_i01", 3,
        "📰 NEWS: US 10Y yield spikes from 4.2% to 4.8% in one week. Bond market panic.\n"
        "🏭 ASSET: Nasdaq 100 (QQQ) — currently at $435.\n"
        "Key levels: 200-day MA $415 | Recent high $461 | P/E multiple: 28x (avg: 22x).\n"
        "What is your impact assessment for QQQ over the next 2 weeks?",
        _OPT_IMPACT,
        "ETFs", "QQQ",
        "Reveals: Rate sensitivity of high-multiple tech stocks. Duration risk."),

    _imcq("t3_i02", 3,
        "📰 NEWS: BOJ (Bank of Japan) unexpectedly raises rates 15bps — first hike in 17 years.\n"
        "🏭 ASSET: USD/JPY — currently at 151.20.\n"
        "Global carry trade (borrow JPY, invest in higher-yield assets) estimated at $4 trillion.\n"
        "What is your impact assessment for USD/JPY?",
        ["🟢 Strongly bullish for USD (higher USD/JPY) — BOJ hike is one-off, dollar strength continues",
         "🟡 Mildly bullish for USD — temporary JPY strength then USD recovers",
         "⚪ Neutral — market anticipated this, already priced in",
         "🟠 Mildly bearish for USD — JPY carry unwind adds JPY demand",
         "🔴 Strongly bearish for USD — massive JPY carry unwind, USD/JPY to 140"],
        "Futures", "USDJPY",
        "Reveals: Carry trade unwind mechanics. BOJ policy transmission."),

    _imcq("t3_i03", 3,
        "📰 NEWS: Implied volatility skew on NIFTY: 25-delta put IV = 22%, ATM IV = 14%, 25-delta call IV = 11%.\n"
        "Implied move for monthly expiry: ±2.8%. Realised vol last 30 days: 8%.\n"
        "🏭 ASSET: NIFTY 50 Options — ATM straddle price ₹580.\n"
        "What is your vol market assessment?",
        ["🟢 Strongly bullish on vol — buy straddle, realised vol will catch up to implied",
         "🟡 Mildly bullish on vol — buy OTM straddle, better risk/reward",
         "⚪ Neutral — vol premium is fair given election uncertainty",
         "🟠 Mildly bearish on vol — sell straddle, IV is 75% above realised",
         "🔴 Strongly bearish on vol — sell iron condor, collect the premium"],
        "Futures", "NIFTY",
        "Reveals: Vol risk premium quantification. Skew reading."),

    _imcq("t3_i04", 3,
        "📰 NEWS: OPEC+ surprise: Saudi Arabia unilaterally cuts 500k bbl/day starting next month.\n"
        "🏭 ASSET: Brent Crude — currently at $82/bbl. Key levels: $78 support | $90 resistance.\n"
        "Contango: front-month $82, 6-month $79. Speculative long positions already at 12-month high.\n"
        "What is your impact assessment?",
        _OPT_IMPACT,
        "Commodities", "BRENT",
        "Reveals: Supply shock vs. speculative positioning. Futures curve context."),

    _imcq("t3_i05", 3,
        "📰 NEWS: Ethereum burns exceed issuance for 3rd consecutive month (net deflationary).\n"
        "Staking ratio rises to 28% of total ETH supply. L2 TVL up 60% MoM.\n"
        "🏭 ASSET: ETH — currently at $3,800.\n"
        "On-chain: Exchange supply at 3-year low. Futures funding rate: +0.02%/8hr (mild positive).\n"
        "What is your impact assessment for ETH?",
        _OPT_IMPACT,
        "Crypto", "ETH",
        "Reveals: On-chain fundamentals integration with price assessment."),

    # ── Strategy SAQs ─────────────────────────────────────────────────────────
    _ssaq("t3_saq01", 3,
        "📊 NIFTY at 24,200. VIX at 16. Elections in 6 weeks. FIIs net sellers past 3 sessions.\n"
        "📰 NEWS: Poll surveys split — hung parliament possible. Bond markets pricing in fiscal risk.\n"
        "You manage a ₹50L equity + derivatives portfolio.\n"
        "Design a specific election hedge: which instruments, strikes, sizing, and when do you remove it?",
        "Futures", "NIFTY",
        "Context: You cannot sell your equity holdings (tax implications).",
        word_limit=120),

    _ssaq("t3_saq02", 3,
        "📊 BTC at $66,000. ETH at $3,500. SOL at $175. Crypto VIX (DVOL) at 62 — elevated.\n"
        "📰 NEWS: BTC halving in 3 weeks. Historical post-halving rallies: +160%, +300%, +600%.\n"
        "Funding rates: BTC +0.05%/8hr (crowded longs). ETH +0.01% (moderate). SOL -0.01% (slight shorts).\n"
        "You have $20,000. Design a specific halving trade with position sizing, leverage decision, and exits.",
        "Crypto", "BTC",
        "Context: You understand perpetual futures and can use options.",
        word_limit=120),

    # ── Risk SAQs ─────────────────────────────────────────────────────────────
    _rsaq("t3_raq01", 3,
        "⚠️ RISK SIGNAL: Your options portfolio Greek exposure:\n"
        "Delta: +850 (equivalent to 17 Nifty lots long)\n"
        "Gamma: -240 (short gamma — large moves hurt you)\n"
        "Theta: +₹8,500/day (collecting time value)\n"
        "Vega: -₹12,000 per 1% IV change (short vega)\n"
        "📰 NEWS: Fed meeting in 48 hours. India VIX up 3 points to 19.\n"
        "How do you adjust your Greek exposure before the event?",
        "Futures", "NIFTY",
        "Context: Your portfolio is ₹30L notional. Max delta loss tolerance: ₹1.5L.",
        word_limit=120),

    _rsaq("t3_raq02", 3,
        "⚠️ RISK SIGNAL: You are long Copper, short Natural Gas, long Silver — commodity macro portfolio.\n"
        "📰 NEWS: China PMI: 47.8 (contraction). US GDP: 1.1% (below 2% estimate). Global recession fear rising.\n"
        "All three positions are moving against you. Portfolio down 18% in 5 days.\n"
        "Walk through your position-by-position risk management. What do you close first and why?",
        "Commodities", "COPPER",
        "Context: Total commodity exposure: $150,000. Max drawdown policy: 20%.",
        word_limit=120),


    # ══════════════════════════════════════════════════════════════════════════
    # LEVEL 4 — Expert (Stat arb, factor models, portfolio risk, quant signals)
    # (Abbreviated — 19 total)
    # ══════════════════════════════════════════════════════════════════════════

    _smcq("t4_s01", 4,
        "📊 Your stat arb model: Long HDFC Bank, Short ICICI Bank (cointegrated pair, Z-score +2.5).\n"
        "📰 NEWS: HDFC Bank announces merger completion with HDFC Ltd — accounting complexities emerge.\n"
        "Pair spread widens to +3.1 σ (your loss increases). What do you do?",
        ["🟢 Close — merger breaks the cointegration relationship permanently",
         "🟡 Reduce 50% — spread will partially mean-revert but relationship is altered",
         "🔵 Hold — extreme spreads are best entry points, mean reversion imminent",
         "🟣 Add to the trade — +3.1σ is historically rare, double down on reversion",
         "🔴 Reverse — spread expansion signals a new equilibrium, trade the other direction"],
        "Stocks", "HDFCBANK",
        "Reveals: Cointegration stability monitoring. Mean-reversion vs. regime change.",
        "stat_arb"),

    _smcq("t4_s02", 4,
        "📊 Your momentum factor portfolio is long top-decile 12-month winners. Sharpe 1.8 last 3 years.\n"
        "📰 NEWS: Fed pivots dovish. Risk-off assets rally. Your momentum portfolio down 8% in 3 sessions.\n"
        "Momentum factor returns now -6% YTD. What do you do?",
        ["🟢 Close — factor crowding = sharp reversals, momentum is broken",
         "🟡 Reduce 40% — de-risk but keep systematic exposure",
         "🔵 Hold — momentum drawdowns are normal; factor timing is futile",
         "🟣 Add — buying factor dips has historically worked",
         "🔴 Rotate to value factor — momentum-value rotation is a known pattern"],
        "Stocks", "NIFTY",
        "Reveals: Factor timing vs. discipline. Momentum crash understanding.",
        "factor_discipline"),

    _smcq("t4_s03", 4,
        "📊 Your risk parity portfolio: 40% bonds, 30% equities, 20% commodities, 10% vol.\n"
        "Bond-equity correlation flips to +0.72 (from typical -0.3). All assets falling together.\n"
        "📰 NEWS: Stagflation data — CPI 7.2%, GDP -0.4%. Classic regime the model wasn't trained on.\n"
        "Risk parity framework is failing. What do you do?",
        ["🟢 Liquidate all — risk parity model assumptions broken, preserve capital",
         "🟡 Reduce total exposure 50% — de-lever while regime is unclear",
         "🔵 Hold — temporary correlation spike, mean reversion expected",
         "🟣 Shift to real assets (gold, commodities) — stagflation historically favours them",
         "🔴 Add vol hedge — buy VIX calls to offset cross-asset losses"],
        "ETFs", "SPY",
        "Reveals: Risk parity limitations awareness. Stagflation regime knowledge.",
        "risk_parity_failure"),

    _smcq("t4_s04", 4,
        "📊 You run a volatility arbitrage book. You are long realized vol (via gamma scalping) and short implied vol.\n"
        "Realized vol: 14%. Implied vol (VIX): 22%. Vol risk premium = 8% — historically rich.\n"
        "📰 NEWS: Major bank failure announced after market close. Pre-market futures down 4%.\n"
        "Your short implied vol position is now deeply underwater. What do you do at open?",
        ["🟢 Buy back all short vol immediately — tail risk event, no ceiling on IV",
         "🟡 Buy back 50% short vol — partial hedge, event may be contained",
         "🔵 Hold — bank failure impact may be one-day event, IV will crash back",
         "🟣 Sell more IV (double down) — eventual vol crush will be profitable",
         "🔴 Hedge the short vol with long VIX calls as a tail hedge only"],
        "ETFs", "VIX",
        "Reveals: Tail risk management in vol books. Regime-change response.",
        "vol_arb_tail_risk"),

    _smcq("t4_s05", 4,
        "📊 Your long/short equity fund: Long quality (low leverage, high ROE). Short junk (high leverage).\n"
        "📰 NEWS: Fed signals emergency liquidity program — zombie companies get lifeline.\n"
        "Your short book (junk equity) rallies 15% in 2 days. Fund NAV down 8%. What do you do?",
        ["🟢 Close shorts immediately — Fed backstop eliminates the fundamental thesis",
         "🟡 Reduce short book by 50% — risk manages without fully capitulating",
         "🔵 Hold — policy cannot change balance sheet reality; reversion coming",
         "🟣 Add to longs — quality will also benefit; reduce short/long ratio",
         "🔴 Reverse some shorts to longs — Fed liquidity trade is multi-month"],
        "Stocks", "SPY",
        "Reveals: Factor investing vs. policy intervention. Thesis discipline under pain.",
        "policy_override"),

    _smcq("t4_s06", 4,
        "📊 You have a basis trade: Long US Treasuries (physical), Short Treasury futures.\n"
        "Basis = physical price - futures price. Basis has widened from 0.12 to 0.38 (abnormal).\n"
        "📰 NEWS: Prime brokerage margin calls rising across hedge funds. Repo market stress visible.\n"
        "You are profitable on the trade but seeing 2020-style basis blowout risks. What do you do?",
        ["🟢 Close immediately — repo stress signals forced selling will widen basis further",
         "🟡 Hold but reduce size by half — basis always converges at expiry",
         "🔵 Add to the trade — widening basis = larger eventual profit at convergence",
         "🟣 Hedge the funding risk with repo rate derivatives only",
         "🔴 Do nothing — basis trades are duration plays, short-term noise"],
        "ETFs", "TLT",
        "Reveals: Basis trade mechanics. Funding risk vs. convergence thesis.",
        "basis_trade_stress"),

    _smcq("t4_s07", 4,
        "📊 Your CTA trend-following model: long equities, long commodities, short bonds (all signals green).\n"
        "Portfolio is +18% YTD. Model confidence: 82%. All positions at max conviction.\n"
        "📰 NEWS: Flash crash — S&P -7% in 20 minutes on thin liquidity (algo-driven).\n"
        "Model signal: unchanged (trend still intact). Your discretionary view: temporary dislocation.\n"
        "What do you do?",
        ["🟢 Follow the model exactly — systematic trading means zero discretionary override",
         "🟡 Reduce equity long 30% — protect YTD gains while model signal holds",
         "🔵 Pause the model for 24 hours — flash crash violates model assumptions",
         "🟣 Buy more equities — flash crashes are mean-reverting within days",
         "🔴 Exit all model positions — black swan events are exactly what models miss"],
        "ETFs", "SPY",
        "Reveals: Systematic vs. discretionary tension. Black swan protocol.",
        "model_override"),

    _smcq("t4_s08", 4,
        "📊 Convertible arb position: Long TATA Motors convertible bond (5% coupon, converts at ₹550).\n"
        "Short TATA Motors equity (current: ₹520). Delta of the convert: 0.65.\n"
        "📰 NEWS: Tata Motors announces ₹15,000 crore rights issue — dilution confirmed.\n"
        "Stock drops 12% to ₹458. What is your delta hedge adjustment?",
        ["🟢 Buy back equity shorts — rights issue dilution reduces delta, re-hedge lower",
         "🟡 Add to equity shorts — dilution increases downside pressure",
         "🔵 Close the entire position — rights issue changes the convert's economics",
         "🟣 Hold — wait to recalculate delta post-rights issue announcement",
         "🔴 Exercise conversion option if in the money — collapse the arb"],
        "Stocks", "TATAMOTORS",
        "Reveals: Convert arb delta management. Dilution event impact on arb.",
        "convert_arb"),

    _smcq("t4_s09", 4,
        "📊 Your multi-factor model signals: Value factor (strong +), Momentum factor (weak -), Quality (neutral).\n"
        "Current portfolio: overweight value, underweight momentum.\n"
        "📰 NEWS: Macro regime shift — growth stocks surging. Momentum factor +8% in 5 days.\n"
        "Factor rotation underway. Your portfolio underperforms benchmark by 3.5% this week.\n"
        "What do you do?",
        ["🟢 Rotate to momentum immediately — factor signals matter more than model conviction",
         "🟡 Tilt 30% toward momentum — gradual adjustment to new regime",
         "🔵 Hold factor weights — 5-day factor moves are noise, not regime change",
         "🟣 Add to value positions — momentum factor crowding creates mean-reversion setup",
         "🔴 Exit factor model entirely until regime stabilizes"],
        "Stocks", "NIFTY",
        "Reveals: Factor timing vs. discipline. Multi-factor interaction understanding.",
        "factor_rotation"),

    _smcq("t4_s10", 4,
        "📊 You run an index arbitrage desk: buy cheapest constituents, short the index.\n"
        "Current basket discount to index: 0.85% (threshold: 0.50%). Signal: EXECUTE.\n"
        "📰 NEWS: SEBI announces emergency circuit breaker — market paused for 30 minutes.\n"
        "During the pause, your short index position loses hedging protection.\n"
        "Market resumes with a gap up 2%. Your arb is now -1.15%. What do you do?",
        ["🟢 Immediately unwind both legs — arb window closed, prevent further loss",
         "🟡 Unwind only the shorts — keep longs for recovery",
         "🔵 Hold entire position — basket-index convergence still mathematically certain",
         "🟣 Add to the arb position — wider spread = larger eventual profit",
         "🔴 Cover shorts, hold longs and pivot to a directional trade"],
        "Stocks", "NIFTY",
        "Reveals: Index arb mechanics. Circuit breaker risk management.",
        "index_arb_disruption"),

    # ── Level 4 Impact MCQs (5) ───────────────────────────────────────────────

    _imcq("t4_i01", 4,
        "📰 NEWS: FOMC minutes reveal 3 members dissented — want faster tightening than consensus.\n"
        "10-year US yield jumps 18bps in 2 hours. 2s10s yield curve: -42bps (deeper inversion).\n"
        "🏭 ASSET: Financial sector ETF (XLF) — currently at $38.50.\n"
        "Key levels: Support $37.20 (200d MA) | Resistance $40.10.\n"
        "What is your impact assessment for XLF over the next 2 weeks?",
        ["🟢 Strongly bullish — steeper short rates = more NIM for banks",
         "🟡 Mildly bullish — yield curve still inverted, limited NIM benefit",
         "⚪ Neutral — rate uncertainty offset by strong bank balance sheets",
         "🟠 Mildly bearish — deeper inversion signals recession risk for loan books",
         "🔴 Strongly bearish — inverted curve is a leading recession indicator, reduce financials"],
        "ETFs", "XLF",
        "Reveals: Yield curve → bank profitability mechanics. Recession signal literacy."),

    _imcq("t4_i02", 4,
        "📰 NEWS: India VIX drops from 21 to 13 in 3 sessions post-election clarity.\n"
        "📰 NEWS 2: FII options short covering accelerates. Put/Call ratio drops to 0.72.\n"
        "🏭 ASSET: NIFTY ATM Straddle (24,000 strike, 15 DTE) — currently priced at ₹520.\n"
        "What is your vol assessment?",
        ["🟢 Buy the straddle — vol crush is overdone, mean reversion inevitable",
         "🟡 Sell the straddle — vol crush still has room, collect theta",
         "⚪ Neutral — straddle price reflects fair value given current regime",
         "🟠 Sell the put side only — directional vol skew favours call sellers",
         "🔴 Buy the strangle (wider strikes) — cheaper than straddle, captures residual vol"],
        "Futures", "NIFTY",
        "Reveals: Vol surface reading. Post-event IV dynamics."),

    _imcq("t4_i03", 4,
        "📰 NEWS: DXY (US Dollar Index) breaks above 107 — 2-year high. 13 of G20 currencies weaken.\n"
        "📰 NEWS 2: Dollar-denominated commodity imports becoming significantly more expensive for EMs.\n"
        "🏭 ASSET: EEM (Emerging Markets ETF) — currently at $39.20.\n"
        "Key levels: Support $37.80 (2023 low) | Resistance $41.50.\n"
        "What is your impact assessment for EEM?",
        _OPT_IMPACT,
        "ETFs", "EEM",
        "Reveals: Dollar strength → EM asset transmission. Import cost → growth impact."),

    _imcq("t4_i04", 4,
        "📰 NEWS: Hedge fund Lone Pine Capital discloses a new 8% stake in Zomato (through 13F).\n"
        "📰 NEWS 2: Tiger Global reduces India fintech exposure by 40%.\n"
        "🏭 ASSET: Zomato (ZOMATO.NS) — at ₹185. FII ownership: 28%. Key levels: ₹170 | ₹205.\n"
        "What is your impact assessment for Zomato?",
        _OPT_IMPACT,
        "Stocks", "ZOMATO",
        "Reveals: Institutional flow reading. Conviction vs. crowding assessment."),

    _imcq("t4_i05", 4,
        "📰 NEWS: Global earnings revision cycle turns negative — S&P 500 EPS estimates cut 8% for next year.\n"
        "📰 NEWS 2: PE multiple of S&P 500 at 22x forward earnings (historical: 17x).\n"
        "🏭 ASSET: SPY — currently at $502. 200-day MA: $468. 52W high: $519.\n"
        "What is your impact assessment for SPY over the next 3 months?",
        _OPT_IMPACT,
        "ETFs", "SPY",
        "Reveals: Earnings revision → equity valuation. Multiple compression awareness."),

    # ── Level 4 Strategy SAQs (2) ─────────────────────────────────────────────

    _ssaq("t4_saq01", 4,
        "📊 Your multi-leg options book on NIFTY:\n"
        "  Long 24,000 straddle (10 lots) — net debit ₹4.8L\n"
        "  Short 24,800 call (5 lots) — premium collected ₹1.2L\n"
        "  Long 23,200 put (5 lots) — insurance hedge, paid ₹0.8L\n"
        "NIFTY gaps up 2% at open to 24,490. VIX drops from 18 to 14 in 30 minutes.\n"
        "📰 NEWS: Positive budget surprise triggered the gap.\n"
        "Walk through your position-by-position P&L assessment and adjustments for the day.",
        "Futures", "NIFTY",
        "Context: You manage this book professionally. Max daily loss limit: ₹3L.",
        word_limit=150),

    _ssaq("t4_saq02", 4,
        "📊 Factor exposures in your long/short equity portfolio:\n"
        "  Value: +2.1 sigma overweight\n"
        "  Momentum: -0.8 sigma underweight\n"
        "  Quality: +0.4 sigma\n"
        "  Low volatility: -1.2 sigma underweight\n"
        "📰 NEWS: Risk-off regime begins — VIX 28, credit spreads widening 120bps.\n"
        "Your portfolio beta = 1.4 (high for a L/S fund). Drawdown: -7% in 10 days.\n"
        "Design a specific factor rotation plan including instruments, timing, and risk targets.",
        "Stocks", "NIFTY",
        "Context: AUM $50M. Investor mandated max drawdown: 12%. Current: -7%.",
        word_limit=150),

    # ── Level 4 Risk SAQs (2) ─────────────────────────────────────────────────

    _rsaq("t4_raq01", 4,
        "⚠️ RISK SIGNAL: Your convertible bond arb book Greeks:\n"
        "  Delta: +340 (long equities equivalent)\n"
        "  Gamma: +180 (benefits from large moves)\n"
        "  Rho: -$85,000 per 100bps rate rise (significant rate exposure)\n"
        "  Credit delta: +$120,000 per 100bps credit spread tightening\n"
        "📰 NEWS: Fed surprise 50bps hike. Credit spreads widen 180bps simultaneously.\n"
        "Portfolio down 12% in 24 hours. Both rate and credit risk hit together.\n"
        "How do you manage the convergence of your risk exposures?",
        "ETFs", "TLT",
        "Context: Fund size $200M. Prime broker margin call triggered at -15%.",
        word_limit=150),

    _rsaq("t4_raq02", 4,
        "⚠️ RISK SIGNAL: Correlation matrix breakdown:\n"
        "  Your portfolio assumes: Gold/Equities = -0.30, Bonds/Equities = -0.45\n"
        "  Current realized: Gold/Equities = +0.62, Bonds/Equities = +0.58\n"
        "  Result: Risk parity portfolio is 2.4x more volatile than model expected.\n"
        "📰 NEWS: Liquidity crisis — all assets selling simultaneously. Cash is the only safe haven.\n"
        "Your Sharpe ratio dropped from 1.8 to 0.3 in 6 weeks.\n"
        "How do you restructure the portfolio's risk framework?",
        "ETFs", "GLD",
        "Context: Portfolio $150M. Investors expect max 10% annual drawdown. Current: -9.5%.",
        word_limit=150),

    # ══════════════════════════════════════════════════════════════════════════
    # LEVEL 5 — Master (Regime models, systemic risk, ML signal interpretation)
    # (Abbreviated — 19 total)
    # ══════════════════════════════════════════════════════════════════════════

    _smcq("t5_s01", 5,
        "📊 Your regime model detects a shift from Risk-On to Risk-Off (confidence 78%).\n"
        "Current portfolio: 60% equities, 20% crypto, 15% commodities, 5% cash.\n"
        "📰 NEWS: Correlation matrix shows all assets moving to +0.85 (high positive correlation).\n"
        "The model recommends: reduce equity 40%, raise cash 30%, add bonds 10%. Do you follow?",
        ["🟢 Yes, fully — regime models are built for this exact scenario",
         "🟡 Partially — 50% of recommended shift",
         "🔵 Wait 24 hours — confirm the regime with price action",
         "🟣 No — 78% confidence is not enough to override current allocation",
         "🔴 Opposite — regime models are overfitted, trade against them"],
        "ETFs", "SPY",
        "Reveals: Model vs. discretion balance. Confidence thresholds.",
        "regime_model"),

    _smcq("t5_s02", 5,
        "📊 Your ML signal: Random forest model predicts -8.5% NIFTY return (90-day horizon).\n"
        "Feature importance: bond yield spread (32%), FII flow (28%), rupee trend (22%), PMI (18%).\n"
        "📰 NEWS: All four features currently flashing negative simultaneously — rare confluence.\n"
        "You are 100% long equities. How much do you reduce equity exposure?",
        ["🟢 Reduce to 0% — 4/4 features aligned is a strong signal, full exit",
         "🟡 Reduce to 40% — respect the signal but avoid model overfit risk",
         "🔵 Reduce to 70% — partial hedge; model confidence at 72%, not certainty",
         "🟣 Hold 100% — ML models are backfit, live signal quality is unknown",
         "🔴 Go short equities — feature alignment this strong historically means sharp falls"],
        "ETFs", "NIFTY",
        "Reveals: ML signal trust calibration. Overfitting awareness.",
        "ml_signal_trust"),

    _smcq("t5_s03", 5,
        "📊 Global macro regime model outputs:\n"
        "  Growth: Decelerating (z-score: -1.8)\n"
        "  Inflation: Sticky (z-score: +1.2)\n"
        "  Liquidity: Tightening (z-score: -2.1)\n"
        "  Risk Appetite: Declining (z-score: -1.5)\n"
        "Historical asset performance in this quadrant (Stagflation-adjacent): Gold +18%, Bonds -12%, Equities -15%.\n"
        "Your portfolio: 65% equities, 20% bonds, 10% gold, 5% cash.\n"
        "What is your immediate reallocation?",
        ["🟢 Mirror historical: cut equities to 20%, bonds to 5%, gold to 55%, cash 20%",
         "🟡 Partial shift: equities 45%, bonds 10%, gold 35%, cash 10%",
         "🔵 Tilt gold only: equities 55%, bonds 15%, gold 25%, cash 5%",
         "🟣 Hold — one regime model reading is insufficient to trade",
         "🔴 Go max defensive: all cash until regime clears"],
        "ETFs", "GLD",
        "Reveals: Macro quadrant analysis. Historical analogue confidence.",
        "macro_quadrant"),

    _smcq("t5_s04", 5,
        "📊 Systemic risk dashboard:\n"
        "  LIBOR-OIS spread: 85bps (normal: 10-15bps)\n"
        "  IG credit spreads: 320bps (normal: 100-150bps)\n"
        "  HY default swap index: 720bps\n"
        "  Dollar swap demand: +$400B (Fed swap lines activated)\n"
        "📰 NEWS: Two regional banks fail. Contagion fears spread. FDIC emergency meeting.\n"
        "You manage a $1B multi-asset fund. What is your immediate priority?",
        ["🟢 Liquidate all credit and equity — systemic stress of this level is 2008-level",
         "🟡 Move 50% to cash and short-term Treasuries — flight to quality not full exit",
         "🔵 Buy financial sector protection (CDS) while holding core positions",
         "🟣 Buy at these spreads — systemic stress creates generational buying opportunity",
         "🔴 Assess each position's direct bank exposure; exit only those at risk"],
        "ETFs", "SPY",
        "Reveals: Systemic risk indicators literacy. Crisis management decision tree.",
        "systemic_crisis"),

    _smcq("t5_s05", 5,
        "📊 Cross-asset signal dashboard at 9:15 AM:\n"
        "  Gold: +1.8% (safety bid)\n"
        "  JPY: +1.2% (yen strengthening — risk off)\n"
        "  VIX: +22% (fear spike)\n"
        "  Oil: -3.5% (demand destruction signal)\n"
        "  US 10Y yield: -18bps (flight to bonds)\n"
        "📰 NEWS: No major headline yet. This cross-asset move is pre-news.\n"
        "Something significant is happening that hasn't been announced. What do you do?",
        ["🟢 Full risk-off immediately — 5/5 asset class signals unanimous = serious event",
         "🟡 Reduce risk by 40% and wait for the news — signals are strong but unknown",
         "🔵 Buy gold and JPY specifically — classic safe-haven play without guessing news",
         "🟣 Do nothing until news is confirmed — acting on pre-news signals is speculation",
         "🔴 Fade the moves — pre-news cross-asset dislocations often reverse quickly"],
        "ETFs", "GLD",
        "Reveals: Cross-asset signal synthesis. Pre-news regime detection.",
        "cross_asset_leading"),

    _smcq("t5_s06", 5,
        "📊 Currency carry trade portfolio: Long AUD/JPY, Long MXN/JPY, Long BRL/USD.\n"
        "All positions profitable YTD (+14%). Carry income: 6-8% annualized.\n"
        "📰 NEWS: Japan CPI hits 3.8% — BoJ signals potential rate hike (rare).\n"
        "JPY strengthens 3% in 24 hours. Your entire carry book loses -8% instantly.\n"
        "What is your carry trade management response?",
        ["🟢 Close all carry positions — BoJ policy change is structural, not temporary",
         "🟡 Close JPY shorts only — restructure to non-JPY pairs",
         "🔵 Hold — BoJ has disappointed hawks before; wait for actual hike",
         "🟣 Add to positions — JPY strengthening overshoots, reversion trade",
         "🔴 Rotate to commodity currencies only — less BoJ exposure"],
        "Futures", "USDJPY",
        "Reveals: Carry trade unwind dynamics. BoJ policy surprise management.",
        "carry_unwind"),

    _smcq("t5_s07", 5,
        "📊 Your algorithmic HFT signal detects: bid-ask spreads on NIFTY futures widening 400% in 90 seconds.\n"
        "Market depth (L2 order book): top 5 levels are 60% thinner than normal.\n"
        "Your momentum signal says: BUY. Your liquidity signal says: DANGER.\n"
        "📰 NEWS: None available. This is pure market microstructure signal.\n"
        "What do you do with your intraday long position (100 lots NIFTY)?",
        ["🟢 Exit immediately — thin book + wide spreads = flash crash risk",
         "🟡 Reduce to 40 lots — maintain some exposure but manage liquidity risk",
         "🔵 Hold — momentum signal overrides microstructure noise in this strategy",
         "🟣 Add on the momentum signal — spread widening is temporary",
         "🔴 Place resting bids at lower levels — provide liquidity and accumulate"],
        "Futures", "NIFTY",
        "Reveals: Microstructure vs. momentum signal conflict. Flash crash preparation.",
        "microstructure_risk"),

    _smcq("t5_s08", 5,
        "📊 Crypto on-chain analytics:\n"
        "  Exchange inflows (BTC): +45,000 BTC in 6 hours (3x normal)\n"
        "  Miner outflows: +8,200 BTC (miner capitulation signal)\n"
        "  Whale addresses (>1000 BTC): Net SELLERS (-12,400 BTC)\n"
        "  Funding rate: -0.08% per 8h (heavy short positioning)\n"
        "📰 NEWS: BTC currently at $58,000. Market sentiment: Fear (index 28).\n"
        "On-chain data paints a bearish picture. Funding rates are contrarian bullish.\n"
        "What is your 48-hour trade?",
        ["🟢 Short BTC — exchange inflows + whale selling + miner capitulation = sell",
         "🟡 Wait — conflicting signals (bearish on-chain, bullish funding) — no edge",
         "🔵 Buy BTC — extreme negative funding = forced short squeeze imminent",
         "🟣 Buy a straddle — conflicting signals = high expected volatility, direction unknown",
         "🔴 Buy altcoins — BTC weakness redistributes to alts during consolidation"],
        "Crypto", "BTC",
        "Reveals: On-chain analytics synthesis. Contrarian funding rate signal.",
        "onchain_synthesis"),

    _smcq("t5_s09", 5,
        "📊 Your global macro portfolio positions:\n"
        "  Long US tech (SPY, QQQ) — +22% YTD\n"
        "  Long India equities (NIFTY ETF) — +18% YTD\n"
        "  Short China equities (FXI puts) — -8% YTD\n"
        "  Long Gold — +14% YTD\n"
        "📰 NEWS: China announces unexpected $1T stimulus. Chinese equities surge 12% in one day.\n"
        "Your China short is being crushed. But US tech and India may also benefit from China recovery.\n"
        "What is your multi-leg portfolio response?",
        ["🟢 Close China short immediately — $1T stimulus breaks the bear thesis",
         "🟡 Close short, rotate gains from gold to China long — flip the position",
         "🔵 Hold short — stimulus announcements are often less effective than they appear",
         "🟣 Close short, add to India — China recovery benefits India more than US tech",
         "🔴 Close short, reduce all — stimulus-driven rallies are typically short-lived"],
        "ETFs", "FXI",
        "Reveals: Multi-leg portfolio management. Policy stimulus impact across correlated markets.",
        "china_stimulus_cascade"),

    _smcq("t5_s10", 5,
        "📊 Systematic global macro strategy triggers three simultaneous signals:\n"
        "  Signal 1: Go long USD (score: 88/100)\n"
        "  Signal 2: Go long Treasuries (score: 82/100)\n"
        "  Signal 3: Go short equities (score: 79/100)\n"
        "These are classic 'risk-off' signals. But: signal correlation is 0.94 — these are the SAME macro bet, tripling your risk.\n"
        "📰 NEWS: No catalyst yet — pure quantitative signal.\n"
        "How do you size and execute?",
        ["🟢 Full execution of all three — 88% model confidence warrants full conviction",
         "🟡 Execute two of three — reduce correlation risk by dropping the weakest signal",
         "🔵 Size down by 60% on all three — high correlation = 3x the intended bet",
         "🟣 Execute only the strongest signal (USD) and wait for others to confirm",
         "🔴 Reject all three — correlated signals don't provide diversified edge"],
        "ETFs", "SPY",
        "Reveals: Signal correlation awareness. Portfolio construction vs. single-signal sizing.",
        "correlated_signals"),

    # ── Level 5 Impact MCQs (5) ───────────────────────────────────────────────

    _imcq("t5_i01", 5,
        "📰 NEWS: US Treasury announces unlimited buyback program for off-the-run bonds.\n"
        "Simultaneous: Fed expands reverse repo facility by $500B. Dollar liquidity injection.\n"
        "🏭 ASSET: DXY (US Dollar Index) — currently at 106.8.\n"
        "Historical analog: 2019 repo crisis intervention, 2020 QE.\n"
        "What is your DXY impact assessment over the next month?",
        ["🟢 Strongly bullish — Treasury demand → dollar demand, classic flight to safety",
         "🟡 Mildly bullish — short-term safety bid but liquidity injection is bearish medium-term",
         "⚪ Neutral — offsetting forces cancel out",
         "🟠 Mildly bearish — liquidity expansion weakens dollar on 4-6 week lag",
         "🔴 Strongly bearish — unlimited buyback signals desperation, dollar confidence collapses"],
        "Futures", "USDIDX",
        "Reveals: Monetary policy → currency transmission. Liquidity vs. safety bid conflict."),

    _imcq("t5_i02", 5,
        "📰 NEWS: IMF downgrades global GDP forecast from 3.2% to 2.1% — citing 'synchronised slowdown'.\n"
        "Simultaneously: Global PMI composite falls below 50 for 4th consecutive month.\n"
        "🏭 ASSET: Commodity index (BCOM) — currently at 112. Key levels: 105 | 118.\n"
        "Historical precedent: 2015-16 commodity bear market during China slowdown.\n"
        "What is your commodity index impact assessment over 3 months?",
        _OPT_IMPACT,
        "Commodities", "BCOM",
        "Reveals: Global growth → commodity demand chain. Historical analogue calibration."),

    _imcq("t5_i03", 5,
        "📰 NEWS: Federal Reserve releases Beige Book — 8 of 12 districts report 'deteriorating conditions'.\n"
        "📰 NEWS 2: Yield curve (2s10s) uninverts after 18 months — classic recession onset signal.\n"
        "🏭 ASSET: US high-yield bond ETF (HYG) — currently at $76. IG spreads at 165bps.\n"
        "Key historical level: 2020 crisis low $64, 2022 peak $87.\n"
        "What is your HYG impact assessment?",
        _OPT_IMPACT,
        "ETFs", "HYG",
        "Reveals: Yield curve uninversion mechanics. Credit spread → equity lead."),

    _imcq("t5_i04", 5,
        "📰 NEWS: Central bank digital currency (CBDC) pilot announced — ECB to test digital euro with 12 banks.\n"
        "📰 NEWS 2: BIS paper argues CBDCs could replace commercial bank deposits over 10 years.\n"
        "🏭 ASSET: EUR/USD — currently at 1.0850. Key levels: 1.0650 | 1.1050.\n"
        "What is your EUR/USD impact assessment over 6 months?",
        _OPT_IMPACT,
        "Futures", "EURUSD",
        "Reveals: CBDC structural impact on fiat currency. Long-horizon macro thinking."),

    _imcq("t5_i05", 5,
        "📰 NEWS: AI compute demand surges — Nvidia backlog extends to 18 months. Power consumption from data centres up 40% YoY.\n"
        "📰 NEWS 2: Uranium spot price hits 15-year high. Nuclear power re-emerges as AI-era baseload solution.\n"
        "🏭 ASSET: URA (Global Uranium ETF) — currently at $32. Up 180% in 2 years.\n"
        "Key levels: Support $27 | Resistance: new highs being set.\n"
        "What is your URA impact assessment over 12 months?",
        _OPT_IMPACT,
        "ETFs", "URA",
        "Reveals: AI → energy → nuclear commodity chain. Structural thematic vs. valuation."),

    # ── Level 5 Strategy SAQs (2) ─────────────────────────────────────────────

    _ssaq("t5_saq01", 5,
        "📊 MACRO REGIME ANALYSIS (your proprietary model):\n"
        "  Regime: Late-cycle expansion → early contraction transition (confidence 74%)\n"
        "  Bull case (26%): soft landing — Fed cuts, growth holds\n"
        "  Bear case (74%): hard landing — recession, credit stress\n"
        "📰 NEWS: Leading indicators (LEI) down 6th consecutive month. Yield curve uninverting.\n"
        "You manage a $500M macro hedge fund. Design a barbell portfolio:\n"
        "Left tail hedge + core allocation + right tail upside.\n"
        "Specify instruments, sizing logic, and trigger conditions for rebalancing.",
        "ETFs", "SPY",
        "Context: Investors expect capital preservation in bear, 80% upside capture in bull.",
        word_limit=200),

    _ssaq("t5_saq02", 5,
        "📊 You are building a systematic global macro strategy. Your three signal modules:\n"
        "  Module A: Trend (12M momentum) — currently: RISK-ON\n"
        "  Module B: Value (PPP-adjusted currencies, CAPE ratios) — currently: RISK-OFF\n"
        "  Module C: Macro regime (yield curve, PMI, credit) — currently: NEUTRAL\n"
        "📰 NEWS: Conflicting regime — 2 modules disagree. Trend says buy, value says sell.\n"
        "This divergence has happened 6 times in 20 years. Historical outcomes split 3-3.\n"
        "Design your position sizing and signal blending approach for this conflict scenario.",
        "ETFs", "SPY",
        "Context: Annual target return 15%. Max drawdown 10%. Leverage limit 2x.",
        word_limit=200),

    # ── Level 5 Risk SAQs (2) ─────────────────────────────────────────────────

    _rsaq("t5_raq01", 5,
        "⚠️ SYSTEMIC RISK ALERT: Your cross-asset risk model detects:\n"
        "  Asset correlation spike: average pairwise correlation 0.88 (normal: 0.25)\n"
        "  Liquidity score: 2.1/10 (critical — worst 5% of readings since 2008)\n"
        "  VaR model breakdown: 99% 1-day VaR was $8M, actual loss today: $31M\n"
        "  Margin utilization: 87% of prime broker limit\n"
        "📰 NEWS: Three simultaneous events — geopolitical shock, credit market freeze, EM currency crisis.\n"
        "Your risk model has failed. Manual intervention required.\n"
        "Design your crisis management protocol: what do you sell first, second, third, and why?",
        "ETFs", "SPY",
        "Context: Fund AUM $800M. Prime broker margin call threshold: 92% utilization.",
        word_limit=200),

    _rsaq("t5_raq02", 5,
        "⚠️ DRAWDOWN ALERT: Your quant fund is -18% from peak (8-month drawdown).\n"
        "Strategy Sharpe ratio: live = 0.4 vs. backtest = 1.6 (significant degradation).\n"
        "Feature drift analysis: 3 of 5 key ML features have shifted out of training distribution.\n"
        "📰 NEWS: Market microstructure has changed — bid-ask spreads 3x wider than backtested period.\n"
        "Investor redemption requests: 12% of AUM requested.\n"
        "You face a choice: defend the strategy or pivot.\n"
        "What is your risk management and investor communication framework?",
        "ETFs", "SPY",
        "Context: Model re-training takes 6 weeks. Redemptions due in 30 days.",
        word_limit=200),

    # ══════════════════════════════════════════════════════════════════════════
    # LEVEL 20 — Global Macro Events (Fed, geopolitics, crises)
    # (Abbreviated — 19 total, last Q is global synthesis)
    # ══════════════════════════════════════════════════════════════════════════

    _smcq("t20_s01", 20,
        "📊 You hold: 40% US tech, 30% EM equities, 20% Gold, 10% Cash.\n"
        "📰 BREAKING: Fed announces emergency 75bps rate HIKE between meetings (unprecedented).\n"
        "S&P futures -6%, EM currencies -4%, Gold -2%, VIX +40%. What is your immediate action?",
        ["🟢 Sell all risk assets — emergency hikes signal systemic crisis",
         "🟡 Sell EM equities only — they are most vulnerable to dollar strength",
         "🔵 Buy more gold — eventual flight to safety will favour it",
         "🟣 Do nothing — panic selling is irrational",
         "🔴 Buy US equities — aggressive Fed = inflation control = eventual bull market"],
        "ETFs", "SPY",
        "Reveals: Crisis response speed. Cross-asset cascade understanding.",
        "systemic_shock"),

    _smcq("t20_s02", 20,
        "📊 You hold: Long 10-Year US Treasuries ($5M notional).\n"
        "📰 BREAKING: US loses AAA credit rating — second downgrade in history (echoing 2011).\n"
        "10Y yield spikes 45bps in 90 minutes. Bond prices drop 4%. What do you do?",
        ["🟢 Buy more — credit downgrade increases supply, but long-run demand is unchanged",
         "🟡 Hold — short-term panic will reverse; US treasuries remain the global safe asset",
         "🔵 Sell all and move to TIPS — inflation-protected bonds are more resilient to downgrade",
         "🟣 Sell treasuries, buy German Bunds — eurozone sovereign credit remains AAA",
         "🔴 Short more Treasuries — downgrade signals structural USD weakness cycle begins"],
        "ETFs", "TLT",
        "Reveals: Sovereign debt crisis response. Alternative safe haven awareness.",
        "sovereign_downgrade"),

    _smcq("t20_s03", 20,
        "📊 Portfolio: 60% EM equities, 25% EM bonds, 15% cash (USD).\n"
        "📰 BREAKING: Fed announces surprise 100bps hike — fastest tightening in 40 years.\n"
        "EM currencies down 6%, EM bonds down 9%, capital flight to USD. What do you do?",
        ["🟢 Liquidate all EM — dollar surge is fatal to EM assets; preserve in USD cash",
         "🟡 Sell EM bonds, hold EM equities — exporters benefit from weak local currencies",
         "🔵 Buy more EM selectively — countries with current account surpluses will survive",
         "🟣 Hedge currency risk with USD calls — keep exposure but eliminate FX risk",
         "🔴 Hold everything — EM valuations now at 2008-level discounts, buy the pain"],
        "ETFs", "EEM",
        "Reveals: Dollar tightening → EM contagion pathway. Differentiated EM analysis.",
        "em_currency_crisis"),

    _smcq("t20_s04", 20,
        "📊 You manage a commodity macro book. Positions: Long Gold, Long Oil, Short Copper.\n"
        "📰 BREAKING: Major Middle East escalation — three oil producing nations involved.\n"
        "Oil spikes 18% in 3 hours. Gold up 4%. Copper flat (demand uncertainty).\n"
        "Geopolitical premium now embedded. What is your next move?",
        ["🟢 Hold all positions — geopolitical events are sustained for months",
         "🟡 Take oil profits at +18%, maintain gold — lock in windfall, keep safety hedge",
         "🔵 Short oil at these levels — geopolitical spikes historically revert in 2-4 weeks",
         "🟣 Add to gold, close oil — gold is the sustained geopolitical hedge, not oil",
         "🔴 Add copper long — supply chain disruption will eventually boost all commodities"],
        "Commodities", "WTI",
        "Reveals: Geopolitical premium sustainability. Commodity crisis vs. sustained move.",
        "geopolitical_oil_spike"),

    _smcq("t20_s05", 20,
        "📊 Global bank: $2B cross-asset portfolio — equities 40%, bonds 35%, alternatives 25%.\n"
        "📰 BREAKING: Major European bank fails — contagion fears spread to 6 other European banks.\n"
        "CDS on European financials up 400%. ECB emergency meeting called for tomorrow.\n"
        "Your European bank bond exposure: $180M. What is your 30-minute decision?",
        ["🟢 Sell all European bank bonds immediately — 2008-style contagion is not manageable",
         "🟡 Sell 60%, wait for ECB response — central bank intervention likely within 24h",
         "🔵 Hold all — ECB will backstop; selling now locks in the panic bottom",
         "🟣 Buy ECB-eligible bonds only — restructure within European exposure for safety",
         "🔴 Buy more at these spreads — bank failures are temporary, spreads will tighten post-ECB"],
        "ETFs", "XLF",
        "Reveals: Banking crisis protocol. 30-minute decision under incomplete information.",
        "banking_contagion"),

    _smcq("t20_s06", 20,
        "📊 Your long-only equity fund. Holdings: 35% US tech, 25% EM, 20% Europe, 20% India.\n"
        "📰 BREAKING: Taiwan strait military escalation — semiconductors at risk.\n"
        "US tech -8%, TSMC (in India fund) -22%, semiconductor ETF -18%.\n"
        "Your tech-heavy fund is down 11% in 4 hours. What is your response?",
        ["🟢 Sell all semiconductor exposure immediately — supply chain disruption is existential",
         "🟡 Sell 50% — hedge the disruption but maintain long-term upside if resolved",
         "🔵 Rotate to defence stocks — geopolitical tension benefits defence, not pure tech",
         "🟣 Hold — military escalations historically resolved within weeks; tech bounces hard",
         "🔴 Buy more TSMC — supply constraint for everyone is a pricing power event"],
        "Stocks", "TSMC",
        "Reveals: Geopolitical supply chain risk. Semiconductor concentration awareness.",
        "taiwan_semiconductor"),

    _smcq("t20_s07", 20,
        "📊 Portfolio: 30% US tech, 30% crypto (BTC + ETH), 20% gold, 20% bonds.\n"
        "📰 BREAKING: US government announces crypto regulatory framework — licenses required.\n"
        "Initial reaction: BTC -12%, ETH -18%, altcoins -35%.\n"
        "24 hours later: BTC stabilises at -8%. ETH recovers to -10%.\n"
        "What is your crypto portfolio response on day 2?",
        ["🟢 Buy more BTC/ETH — regulation provides institutional clarity, long-term bullish",
         "🟡 Hold BTC, sell ETH — ETH's smart contract use cases face more regulatory scrutiny",
         "🔵 Sell all crypto — regulation signals government control of a decentralization asset",
         "🟣 Wait 2 weeks — regulatory impact requires time to fully understand",
         "🔴 Buy altcoins that will get licensed — regulatory clarity creates winners"],
        "Crypto", "BTC",
        "Reveals: Regulatory regime change impact. BTC vs. ETH regulatory risk differentiation.",
        "crypto_regulation"),

    _smcq("t20_s08", 20,
        "📊 You manage a global macro hedge fund ($1B AUM).\n"
        "📰 BREAKING: IMF announces emergency SDR allocation of $650B to developing nations.\n"
        "Impact: USD weakens 3%, Gold +5%, EM currencies strengthen broadly.\n"
        "Your current position: Long USD, Short Gold. Both are underwater simultaneously.\n"
        "What is your macro response?",
        ["🟢 Close both positions immediately — IMF SDR is a structural dollar-negative event",
         "🟡 Close USD long, hold short gold — USD weakness doesn't guarantee gold continuation",
         "🔵 Hold both — SDR allocations are historically limited in sustained market impact",
         "🟣 Reverse to short USD, long Gold — position with the SDR narrative",
         "🔴 Buy EM currencies directly — SDR benefits are most direct for EM FX"],
        "Futures", "USDIDX",
        "Reveals: IMF SDR mechanism understanding. Dollar liquidity vs. gold correlation.",
        "imf_sdr_response"),

    _smcq("t20_s09", 20,
        "📊 Your portfolio during a global liquidity crisis: All assets falling simultaneously.\n"
        "Cash position: 5%. Prime broker is issuing warnings. Redemption queue forming.\n"
        "📰 BREAKING: Three central banks announce coordinated intervention — but markets still falling.\n"
        "VIX at 58. Bid-ask spreads on SPY: $0.85 (normal: $0.01). Liquidity has evaporated.\n"
        "In this environment, what is your primary objective?",
        ["🟢 Liquidate at any price — capital preservation is the only objective",
         "🟡 Liquidate only illiquid positions — ETFs and large caps first, alternatives last",
         "🔵 Stop all selling — central bank intervention is the turning point",
         "🟣 Buy at these levels — central bank coordination historically reverses markets",
         "🔴 Maintain positions but hedge with long vol (VIX calls) — buy time"],
        "ETFs", "SPY",
        "Reveals: Crisis triage. Liquidity crisis vs. solvency crisis distinction.",
        "liquidity_crisis_triage"),

    # ── Level 20 Impact MCQs (5) ──────────────────────────────────────────────

    _imcq("t20_i01", 20,
        "📰 BREAKING: China announces full convertibility of the renminbi — capital account opens.\n"
        "Simultaneously: China proposes renminbi-settled oil trade with OPEC nations.\n"
        "🏭 ASSET: Gold (XAU/USD) — currently at $2,180/oz.\n"
        "Historical analog: 1971 Nixon Shock (dollar depegged from gold).\n"
        "What is your impact assessment for Gold over 12 months?",
        ["🟢 Strongly bullish — dollar reserve status erosion = gold re-monetisation",
         "🟡 Mildly bullish — RMB internationalisation takes decades, modest dollar impact",
         "⚪ Neutral — alternative reserve currency narrative has been raised for 20 years",
         "🟠 Mildly bearish — RMB convertibility increases global risk appetite, rotation to equities",
         "🔴 Strongly bearish — RMB strength → weaker need for gold as alt reserve"],
        "Commodities", "GOLD",
        "Reveals: Global reserve currency shift mechanics. Long-horizon gold thesis."),

    _imcq("t20_i02", 20,
        "📰 BREAKING: G20 announces coordinated fiscal stimulus — $3 trillion global package.\n"
        "All G20 nations agree to spend simultaneously for first time since 2009.\n"
        "🏭 ASSET: MSCI World Equity Index (ACWI ETF) — currently at $98.\n"
        "Key historical comparison: 2009 G20 stimulus reversed global recession in 6 months.\n"
        "What is your impact assessment for global equities over 6 months?",
        _OPT_IMPACT,
        "ETFs", "ACWI",
        "Reveals: Coordinated global stimulus impact. 2009 analogue calibration."),

    _imcq("t20_i03", 20,
        "📰 BREAKING: Major cyber attack disables SWIFT banking network for 6 hours.\n"
        "Estimated $2.4 trillion in transactions stuck. Three central banks issue emergency statements.\n"
        "🏭 ASSET: Bitcoin (BTC) — currently at $72,000.\n"
        "The narrative: 'if SWIFT can be attacked, crypto is the alternative infrastructure'.\n"
        "What is your impact assessment for BTC over the next 48 hours?",
        _OPT_IMPACT,
        "Crypto", "BTC",
        "Reveals: Macro narrative vs. technical reality. Crisis-driven crypto thesis."),

    _imcq("t20_i04", 20,
        "📰 BREAKING: WHO declares new pandemic (respiratory, R0=3.2, mortality 1.8%).\n"
        "Travel restrictions beginning in 12 countries. Markets pricing in 2020-repeat.\n"
        "🏭 ASSET: Airlines sector ETF (JETS) — currently at $22. 52W high: $29. 2020 low: $11.\n"
        "What is your impact assessment for JETS over the next 3 months?",
        _OPT_IMPACT,
        "ETFs", "JETS",
        "Reveals: Pandemic severity calibration. 2020 analogue vs. different starting conditions."),

    _imcq("t20_i05", 20,
        "📰 BREAKING: US Treasury announces sanctions on Russia's primary oil export mechanisms.\n"
        "Simultaneously: EU bans import of Russian LNG — complete energy divorce.\n"
        "🏭 ASSET: European natural gas futures (TTF) — currently at €45/MWh. 2022 peak: €340.\n"
        "What is your impact assessment for European natural gas over the next quarter?",
        _OPT_IMPACT,
        "Commodities", "NATGAS",
        "Reveals: Geopolitical energy sanctions → commodity supply impact. Storage dependency."),

    # ── Level 20 Strategy SAQs (2) ────────────────────────────────────────────

    _ssaq("t20_saq01", 20,
        "🌍 GLOBAL MACRO STATE:\n"
        "  US: Recession probability 68% (yield curve inverted 14 months)\n"
        "  China: Stimulus deployed but deflation persists (CPI -0.4%)\n"
        "  Europe: Energy shock + bank stress, ECB pausing hikes\n"
        "  EM: Currency crisis in 5 nations, IMF programs underway\n"
        "  Gold: +24% YTD. USD: +8% YTD. Oil: -15% YTD.\n"
        "You manage $2B for a sovereign wealth fund.\n"
        "Design a 6-month asset allocation with specific allocations, rationale, and trigger levels for repositioning.",
        "ETFs", "ACWI",
        "Context: Mandate: preserve real capital, 8% return target. Max drawdown: 15%.",
        word_limit=250),

    _ssaq("t20_saq02", 20,
        "🌍 SCENARIO: Concurrent global shocks (happening simultaneously):\n"
        "  1. US election contested — 3-month legal uncertainty\n"
        "  2. China invades disputed territory — tech sanctions imminent\n"
        "  3. Eurozone sovereign debt crisis — Italy/Spain spreads at 650bps\n"
        "  4. Fed pivots unexpectedly dovish (cut 75bps in one meeting)\n"
        "  5. Oil supply shock — OPEC+ cuts 3M bbl/day\n"
        "Each event alone would be a 2-sigma market move. All five are simultaneous.\n"
        "How do you manage a $500M multi-asset portfolio in this environment?\n"
        "Include: immediate actions (Day 1), short-term strategy (Week 1-4), and 3-month outlook.",
        "ETFs", "SPY",
        "Context: Highly liquid portfolio. No restrictions on instruments or leverage.",
        word_limit=250),

    # ── Level 20 Risk SAQs (2) ────────────────────────────────────────────────

    _rsaq("t20_raq01", 20,
        "⚠️ SYSTEMIC CRISIS: All your risk models are failing simultaneously.\n"
        "  VaR model: predicted $15M max loss. Actual: -$89M in 2 days\n"
        "  Correlation model: all assets +0.93 correlation (model assumed 0.3)\n"
        "  Liquidity model: assumed T+1 liquidation. Reality: T+5 minimum\n"
        "  Vol model: 20-day realised vol 35%, model used 12%\n"
        "📰 NEWS: Global margin call cascade. Hedge fund failures reported.\n"
        "Your fund has 60 hours of liquidity runway before prime broker liquidates you.\n"
        "Design your 60-hour crisis survival plan with priorities and sequencing.",
        "ETFs", "SPY",
        "Context: Fund AUM $600M. Creditors: pension funds expecting capital preservation.",
        word_limit=250),

    _rsaq("t20_raq02", 20,
        "⚠️ MULTI-YEAR DRAWDOWN: Your global macro fund has underperformed 3 years running.\n"
        "  Year 1: -8% (fund), benchmark -2% | Year 2: +4% (fund), benchmark +18% | Year 3: -12% (fund), benchmark +6%\n"
        "  Cumulative underperformance vs. benchmark: -31% over 3 years\n"
        "Redemptions: 38% of AUM redeemed. Remaining AUM: $320M (from $520M).\n"
        "📰 NEWS: Two anchor investors threatening to redeem unless you change the strategy.\n"
        "The macro regime your strategy was built for has not materialized.\n"
        "Design a comprehensive strategy review and investor communication plan.",
        "ETFs", "SPY",
        "Context: Your strategy thesis is intact but has been early by 3 years.",
        word_limit=250),

    # ── Level 20 FINAL QUESTION: Global Synthesis SAQ ─────────────────────────
    _ssaq("t20_saq_final", 20,
        "🌍 GLOBAL MACRO SYNTHESIS:\n"
        "Identify the 5 most impactful global events happening NOW and explain:\n"
        "1. How each affects specific asset classes (stocks, bonds, commodities, crypto, currencies)\n"
        "2. Your specific trading strategy for the next 7 days\n"
        "3. Risk management framework given cross-asset contagion\n"
        "This is your opportunity to demonstrate synthesis of macro, markets, and execution.",
        "ETFs", "GLOBAL",
        "Context: Portfolio size $500k. Multi-asset access. Professional risk management required.",
        word_limit=200),
]