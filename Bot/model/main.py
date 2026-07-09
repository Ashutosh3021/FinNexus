"""
FinNexus Bot — ML Model
XGBoost-based model that:
  1. Loads pre-trained artifacts from disk (trained on cleaned CSVs)
  2. Extracts a feature vector from a user's HITL answers
  3. Predicts market direction confidence improvement
  4. Supports online updates (incremental learning via warm_start re-fit)

The model is intentionally lightweight — it augments, not replaces,
the main prediction pipeline.
"""

from __future__ import annotations

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Optional heavy imports ────────────────────────────────────────────────────
try:
    import xgboost as xgb  # type: ignore
    _XGB_AVAILABLE = True
except ImportError:
    _XGB_AVAILABLE = False
    logger.warning("xgboost not installed — MLModel will use a dummy scorer")

try:
    from sklearn.preprocessing import StandardScaler  # type: ignore
    _SKL_AVAILABLE = True
except ImportError:
    _SKL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Feature extraction constants
# ---------------------------------------------------------------------------

# One entry per feature slot — order MUST stay stable after first training
FEATURE_NAMES: List[str] = [
    "avg_score",           # mean score across all answers in session
    "mcq_accuracy",        # fraction of MCQs correct (score >= 0.5)
    "saq_avg_score",       # mean SAQ score
    "level",               # current level 1-5 (20 for global events)
    "questions_answered",  # total answered this session
    "score_variance",      # variance in scores — measures consistency
    "top_score",           # best single score
    "bottom_score",        # worst single score
    "streak",              # longest consecutive correct streak
    "level_20_flag",       # 1 if any level-20 answer present
]

N_FEATURES = len(FEATURE_NAMES)


# ---------------------------------------------------------------------------
# Feature extractor
# ---------------------------------------------------------------------------

def extract_features(answers: Dict[str, Any], level: int) -> np.ndarray:
    """
    Convert a dict of {question_id: AnswerRecord | dict} into a
    fixed-length float32 feature vector.

    Works with both AnswerRecord objects and plain dicts (from DB).
    """
    if not answers:
        return np.zeros(N_FEATURES, dtype=np.float32)

    scores: List[float] = []
    mcq_scores: List[float] = []
    saq_scores: List[float] = []
    has_level_20 = False

    for rec in answers.values():
        # Accept both dataclass and dict
        score: float = rec.score if hasattr(rec, "score") else rec.get("score", 0.0)
        qtype: str = (
            rec.question_type.value
            if hasattr(rec, "question_type") and hasattr(rec.question_type, "value")
            else str(rec.question_type if hasattr(rec, "question_type") else rec.get("question_type", ""))
        )
        is_20: bool = rec.is_level_20 if hasattr(rec, "is_level_20") else bool(rec.get("is_level_20", False))

        scores.append(score)
        if "mcq" in qtype:
            mcq_scores.append(score)
        elif "saq" in qtype:
            saq_scores.append(score)
        if is_20:
            has_level_20 = True

    arr = scores
    avg = float(np.mean(arr)) if arr else 0.0
    mcq_acc = float(np.mean([1.0 if s >= 0.5 else 0.0 for s in mcq_scores])) if mcq_scores else 0.0
    saq_avg = float(np.mean(saq_scores)) if saq_scores else 0.0
    variance = float(np.var(arr)) if len(arr) > 1 else 0.0
    top = float(max(arr)) if arr else 0.0
    bot = float(min(arr)) if arr else 0.0

    # Longest correct streak (score >= 0.5 considered correct)
    streak = _longest_streak([s >= 0.5 for s in arr])

    feat = np.array([
        avg,
        mcq_acc,
        saq_avg,
        float(level) / 20.0,      # normalise level to [0,1]
        float(len(arr)) / 19.0,   # normalise to max questions
        variance,
        top,
        bot,
        float(streak) / 19.0,
        1.0 if has_level_20 else 0.0,
    ], dtype=np.float32)

    return feat


def _longest_streak(bools: List[bool]) -> int:
    best = cur = 0
    for b in bools:
        cur = cur + 1 if b else 0
        best = max(best, cur)
    return best


# ---------------------------------------------------------------------------
# MLModel class
# ---------------------------------------------------------------------------

class MLModel:
    """
    Thin wrapper around an XGBoost regressor that predicts a
    'prediction_improvement' score (how much a user's HITL answers
    are expected to improve the ML model's confidence).

    Falls back to a simple heuristic scorer if XGBoost is not available.
    """

    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._model: Optional[Any] = None
        self._scaler: Optional[Any] = None
        self._training_buffer: List[tuple] = []  # (X, y) pairs pending fit
        self._n_trained: int = 0
        self._val_metrics: dict = {}

        self._load()
        # Pre-train with synthetic data if no model exists yet
        if self._model is None:
            self._pretrain_synthetic()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _model_path(self) -> Path:
        return self.model_dir / "hitl_xgb.pkl"

    def _scaler_path(self) -> Path:
        return self.model_dir / "hitl_scaler.pkl"

    def _meta_path(self) -> Path:
        return self.model_dir / "hitl_meta.json"

    def _load(self) -> None:
        mp = self._model_path()
        sp = self._scaler_path()
        if mp.exists():
            with open(mp, "rb") as f:
                self._model = pickle.load(f)
            logger.info("MLModel: loaded XGB model from %s", mp)
        if sp.exists() and _SKL_AVAILABLE:
            with open(sp, "rb") as f:
                self._scaler = pickle.load(f)
        if self._meta_path().exists():
            meta = json.loads(self._meta_path().read_text())
            self._n_trained = meta.get("n_trained", 0)
            self._val_metrics = meta.get("val_metrics", {})

    def _atomic_dump(self, path: Path, obj: Any) -> None:
        # H3: write to a temp file in the same directory, then atomically
        # replace. Prevents two concurrent gunicorn workers from writing the
        # pickle simultaneously and producing a corrupt/partial file.
        import tempfile
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                pickle.dump(obj, f)
            os.replace(tmp, str(path))
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def _save(self) -> None:
        if self._model:
            self._atomic_dump(self._model_path(), self._model)
        if self._scaler:
            self._atomic_dump(self._scaler_path(), self._scaler)
        self._meta_path().write_text(json.dumps({
            "n_trained": self._n_trained,
            "val_metrics": self._val_metrics,
        }))

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict_improvement(self, answers: Dict[str, Any], level: int) -> float:
        """
        Return a 0-1 score representing expected improvement to the
        prediction pipeline from this user's answers.
        """
        feat = extract_features(answers, level).reshape(1, -1)

        if self._model and _XGB_AVAILABLE:
            try:
                if self._scaler:
                    feat = self._scaler.transform(feat)
                pred = float(self._model.predict(feat)[0])
                return float(np.clip(pred, 0.0, 1.0))
            except Exception as exc:
                logger.warning("MLModel.predict failed: %s — using heuristic", exc)

        # Heuristic fallback: avg_score × quality bonus
        avg_score = float(feat[0, 0])
        return float(np.clip(avg_score * 1.1, 0.0, 1.0))

    # ── Online update ─────────────────────────────────────────────────────────

    def train_on_answers(
        self,
        user_id: int,
        answers: Dict[str, Any],
        market_outcome: float,
        level: int,
    ) -> None:
        """
        Accumulate a (features, label) pair in the buffer.
        Re-fit when buffer reaches 50 samples to avoid constant retraining.
        market_outcome: actual directional accuracy improvement (0-1) observed
        """
        feat = extract_features(answers, level)
        self._training_buffer.append((feat, float(market_outcome)))
        logger.debug("MLModel: buffer size %d for user %d", len(self._training_buffer), user_id)

        if len(self._training_buffer) >= 50:
            self._fit_buffer()

    def _fit_buffer(self) -> None:
        if not _XGB_AVAILABLE:
            logger.warning("MLModel: xgboost unavailable, skipping fit")
            self._training_buffer.clear()
            return

        X = np.array([x for x, _ in self._training_buffer], dtype=np.float32)
        y = np.array([y for _, y in self._training_buffer], dtype=np.float32)

        # Train/validation split (80/20) for performance tracking
        n_val = max(1, len(X) // 5)
        X_train, X_val = X[:-n_val], X[-n_val:]
        y_train, y_val = y[:-n_val], y[-n_val:]

        if _SKL_AVAILABLE:
            from sklearn.preprocessing import StandardScaler
            if self._scaler is None:
                self._scaler = StandardScaler()
            # Always re-fit scaler on the current buffer to capture distribution shifts
            self._scaler.fit(X_train)
            X_train = self._scaler.transform(X_train)
            X_val = self._scaler.transform(X_val)

        if self._model is None:
            self._model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbosity=0,
            )
            self._model.fit(X_train, y_train)
        else:
            # Warm-start: update with new data using all training samples
            self._model.fit(X_train, y_train, xgb_model=self._model.get_booster())

        # Validation metrics
        if len(X_val) > 0:
            val_preds = self._model.predict(X_val)
            val_mae = float(np.mean(np.abs(val_preds - y_val)))
            val_rmse = float(np.sqrt(np.mean((val_preds - y_val) ** 2)))
            self._val_metrics = {"mae": round(val_mae, 4), "rmse": round(val_rmse, 4)}
            logger.info(
                "MLModel: validation MAE=%.4f RMSE=%.4f (%d val samples)",
                val_mae, val_rmse, len(X_val),
            )
        else:
            self._val_metrics = {}

        self._n_trained += len(self._training_buffer)
        self._training_buffer.clear()
        self._save()
        logger.info("MLModel: re-fitted on %d total samples", self._n_trained)

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        return {
            "model_available": self._model is not None,
            "xgboost_available": _XGB_AVAILABLE,
            "n_trained": self._n_trained,
            "buffer_size": len(self._training_buffer),
            "feature_names": FEATURE_NAMES,
            "model_path": str(self._model_path()),
            "val_metrics": self._val_metrics,
        }

    # ── Synthetic pre-training ─────────────────────────────────────────────────

    def _pretrain_synthetic(self) -> None:
        """
        Generate synthetic training data and train the initial XGBoost model.
        Called once at startup when no pre-trained model exists in artifacts/.
        Uses 80 samples (>50 threshold) so training triggers immediately.
        """
        if not _XGB_AVAILABLE:
            logger.warning("MLModel: xgboost unavailable — cannot pre-train")
            return

        logger.info("MLModel: no pre-trained model found — generating synthetic training data...")
        rng = np.random.default_rng(42)
        n_samples = 80

        # Generate plausible HITL feature vectors
        X_list = []
        y_list = []
        for _ in range(n_samples):
            avg_score = rng.uniform(0.1, 1.0)
            mcq_acc = rng.uniform(max(0.0, avg_score - 0.3), min(1.0, avg_score + 0.3))
            saq_avg = rng.uniform(max(0.0, avg_score - 0.25), min(1.0, avg_score + 0.25))
            level_norm = rng.uniform(0.05, 1.0)
            q_answered_norm = rng.uniform(0.1, 1.0)
            variance = rng.uniform(0.0, 0.15)
            top_score = min(1.0, avg_score + rng.uniform(0.0, 0.3))
            bot_score = max(0.0, avg_score - rng.uniform(0.0, 0.3))
            streak_norm = rng.uniform(0.0, q_answered_norm)
            level_20_flag = float(rng.random() < 0.1)

            feat = np.array([
                avg_score, mcq_acc, saq_avg,
                level_norm, q_answered_norm, variance,
                top_score, bot_score, streak_norm, level_20_flag,
            ], dtype=np.float32)

            # Target: improvement correlated with scores, with noise
            target = float(np.clip(
                avg_score * 0.6 + mcq_acc * 0.2 + saq_avg * 0.2 + rng.normal(0, 0.05),
                0.0, 1.0,
            ))
            X_list.append(feat)
            y_list.append(target)

        # Queue all samples in the buffer
        for feat, target in zip(X_list, y_list):
            self._training_buffer.append((feat, target))

        # Fit (buffer ≥ 50 samples triggers the full fit + val split)
        self._fit_buffer()
        logger.info("MLModel: synthetic pre-training complete — model saved to %s", self._model_path())
