"""
Data Cleaning Module — FinNexus
Handles cleaning for all asset types: Crypto, Stocks, Commodities, ETFs, Futures/Options
"""

import os
import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

PRICE_COLS = ["Open", "High", "Low", "Close"]
VOLUME_COL = "Volume"
DATE_COL = "Date"

# Max allowed missing-day fraction before we drop the asset entirely
MAX_MISSING_FRACTION = 0.05

# Outlier thresholds
Z_SCORE_THRESHOLD = 3.0
IQR_MULTIPLIER = 3.0


# ─── Public API ───────────────────────────────────────────────────────────────

def clean_dataset(
    df: pd.DataFrame,
    asset_name: str,
    asset_type: str = "generic",
) -> Tuple[pd.DataFrame, dict]:
    """
    Main entry point. Returns (cleaned_df, quality_report_dict).

    Parameters
    ----------
    df         : Raw OHLCV DataFrame (must have Date, Open, High, Low, Close, Volume)
    asset_name : Human-readable label (e.g. "BTC", "N50_HDFCBANK")
    asset_type : One of 'crypto', 'stock', 'commodity', 'etf', 'futures', 'generic'
    """
    report: dict = {
        "asset": asset_name,
        "asset_type": asset_type,
        "original_rows": len(df),
        "issues": [],
    }

    df = _validate_columns(df, asset_name)
    df = _parse_dates(df, asset_name, report)
    df = _validate_data_types(df, asset_name, report)
    df = _deduplicate(df, asset_name, report)
    df = _sort_by_date(df)
    df = _check_missing_fraction(df, asset_name, report)
    df = _fill_missing_dates(df, asset_name, asset_type, report)
    df = _fix_ohlc_consistency(df, asset_name, report)
    df = _fix_volume(df, asset_name, report)
    df = _detect_and_flag_outliers(df, asset_name, report)
    df = _add_quality_score_column(df)

    report["final_rows"] = len(df)
    report["missing_pct"] = round(
        100.0 * df[PRICE_COLS + [VOLUME_COL]].isnull().any(axis=1).mean(), 2
    )
    report["outlier_rows"] = int(df.get("is_outlier", pd.Series(0)).sum())
    report["quality_score"] = _compute_quality_score(df, report)

    logger.info(
        f"[{asset_name}] cleaned: {report['original_rows']} → {report['final_rows']} rows | "
        f"quality={report['quality_score']:.1f}/100"
    )
    return df, report


def validate_data(df: pd.DataFrame) -> list:
    """Run all validation checks and return a list of issue strings."""
    issues = []
    required = [DATE_COL] + PRICE_COLS + [VOLUME_COL]
    for col in required:
        if col not in df.columns:
            issues.append(f"Missing column: {col}")

    if DATE_COL in df.columns:
        dupes = df[DATE_COL].duplicated().sum()
        if dupes:
            issues.append(f"Duplicate dates: {dupes}")
        if not pd.api.types.is_datetime64_any_dtype(df[DATE_COL]):
            issues.append("Date column is not datetime type")

    for col in PRICE_COLS:
        if col in df.columns and (df[col] <= 0).any():
            issues.append(f"Non-positive values in {col}")

    if VOLUME_COL in df.columns and (df[VOLUME_COL] < 0).any():
        issues.append("Negative volume detected")

    if all(c in df.columns for c in ["High", "Low", "Open", "Close"]):
        if (df["High"] < df["Low"]).any():
            issues.append("High < Low detected")
        if (df["High"] < df["Open"]).any():
            issues.append("High < Open detected")
        if (df["High"] < df["Close"]).any():
            issues.append("High < Close detected")
        if (df["Low"] > df["Open"]).any():
            issues.append("Low > Open detected")
        if (df["Low"] > df["Close"]).any():
            issues.append("Low > Close detected")

    return issues


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Public helper: forward-fill short gaps, interpolate medium gaps."""
    df = df.copy()
    for col in PRICE_COLS + [VOLUME_COL]:
        if col not in df.columns:
            continue
        null_mask = df[col].isnull()
        if not null_mask.any():
            continue

        # Identify gap lengths
        gap_starts = null_mask & ~null_mask.shift(1, fill_value=False)
        gap_ids = gap_starts.cumsum()
        gap_ids[~null_mask] = 0
        gap_lengths = gap_ids.map(gap_ids[null_mask].value_counts()).where(null_mask, 0)

        # ≤2 days → forward-fill
        short_mask = null_mask & (gap_lengths <= 2)
        df.loc[short_mask, col] = df[col].ffill()[short_mask]

        # 3–10 days → linear interpolation
        medium_mask = df[col].isnull() & (gap_lengths <= 10)
        df.loc[medium_mask, col] = df[col].interpolate(method="linear")[medium_mask]

        # >10 days → leave as NaN (will be dropped downstream)

    return df


def detect_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Return a boolean Series — True where any price is an outlier."""
    outlier_mask = pd.Series(False, index=df.index)

    for col in PRICE_COLS:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if len(series) < 30:
            continue

        # IQR method
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - IQR_MULTIPLIER * iqr, q3 + IQR_MULTIPLIER * iqr
        iqr_flag = (df[col] < lo) | (df[col] > hi)

        # Z-score on log-returns
        log_ret = np.log(df[col] / df[col].shift(1)).dropna()
        z_scores = (log_ret - log_ret.mean()) / log_ret.std()
        z_flag = z_scores.abs() > Z_SCORE_THRESHOLD
        z_flag = z_flag.reindex(df.index, fill_value=False)

        outlier_mask |= iqr_flag.fillna(False) | z_flag

    return outlier_mask


# ─── Private Helpers ──────────────────────────────────────────────────────────

def _validate_columns(df: pd.DataFrame, asset_name: str) -> pd.DataFrame:
    """Ensure required columns exist; normalise column names."""
    df = df.copy()
    # normalise header capitalisation
    df.columns = [c.strip().title().replace(" ", "_") for c in df.columns]
    # map common variants
    renames = {
        "Datetime": "Date",
        "Timestamp": "Date",
        "Price": "Close",
        "Vol": "Volume",
        "Vol.": "Volume",
    }
    df = df.rename(columns=renames)
    required = [DATE_COL] + PRICE_COLS + [VOLUME_COL]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"[{asset_name}] Missing required columns: {missing}. "
            f"Found: {list(df.columns)}"
        )
    return df


def _parse_dates(df: pd.DataFrame, asset_name: str, report: dict) -> pd.DataFrame:
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[DATE_COL]):
        try:
            df[DATE_COL] = pd.to_datetime(df[DATE_COL], utc=False)
        except Exception as e:
            report["issues"].append(f"Date parse error: {e}")
    # normalise to date-only (drop time component) – keep it tz-naive
    df[DATE_COL] = pd.to_datetime(df[DATE_COL]).dt.normalize()
    return df


def _validate_data_types(df: pd.DataFrame, asset_name: str, report: dict) -> pd.DataFrame:
    df = df.copy()
    for col in PRICE_COLS + [VOLUME_COL]:
        if col in df.columns:
            before_nulls = df[col].isnull().sum()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            after_nulls = df[col].isnull().sum()
            if after_nulls > before_nulls:
                n = after_nulls - before_nulls
                report["issues"].append(
                    f"Coerced {n} non-numeric values to NaN in {col}"
                )
    return df


def _deduplicate(df: pd.DataFrame, asset_name: str, report: dict) -> pd.DataFrame:
    dupes = df.duplicated(subset=[DATE_COL], keep="last").sum()
    if dupes:
        report["issues"].append(f"Removed {dupes} duplicate date rows")
    return df.drop_duplicates(subset=[DATE_COL], keep="last")


def _sort_by_date(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(DATE_COL).reset_index(drop=True)


def _check_missing_fraction(
    df: pd.DataFrame, asset_name: str, report: dict
) -> pd.DataFrame:
    """Warn (but don't drop) if too many NaN values exist."""
    frac = df[PRICE_COLS + [VOLUME_COL]].isnull().any(axis=1).mean()
    report["missing_fraction_before_fill"] = round(float(frac), 4)
    if frac > MAX_MISSING_FRACTION:
        report["issues"].append(
            f"High missing data fraction: {frac:.1%} (threshold {MAX_MISSING_FRACTION:.0%})"
        )
    return df


def _fill_missing_dates(
    df: pd.DataFrame, asset_name: str, asset_type: str, report: dict
) -> pd.DataFrame:
    """Reindex to a full calendar and fill gaps."""
    df = df.set_index(DATE_COL)
    full_range = pd.date_range(df.index.min(), df.index.max(), freq="D")

    if asset_type in ("stock", "etf", "futures"):
        # Business days only
        full_range = pd.bdate_range(df.index.min(), df.index.max())

    new_dates = full_range.difference(df.index)
    if len(new_dates):
        report["issues"].append(
            f"Reindexed: filled {len(new_dates)} missing calendar dates"
        )

    df = df.reindex(full_range)

    # Forward-fill ≤2 trading days
    df = df.ffill(limit=2)

    # Interpolate remaining gaps ≤10 days
    for col in PRICE_COLS + [VOLUME_COL]:
        df[col] = df[col].interpolate(method="linear", limit=10)

    df.index.name = DATE_COL
    df = df.reset_index()
    return df


def _fix_ohlc_consistency(
    df: pd.DataFrame, asset_name: str, report: dict
) -> pd.DataFrame:
    """Enforce High >= Open,Close >= Low."""
    df = df.copy()
    bad = (
        (df["High"] < df["Low"])
        | (df["High"] < df["Open"])
        | (df["High"] < df["Close"])
        | (df["Low"] > df["Open"])
        | (df["Low"] > df["Close"])
    )
    n_bad = bad.sum()
    if n_bad:
        report["issues"].append(f"Fixed {n_bad} OHLC consistency violations")
        # Recompute High/Low from the four prices
        df.loc[bad, "High"] = df.loc[bad, PRICE_COLS].max(axis=1)
        df.loc[bad, "Low"] = df.loc[bad, PRICE_COLS].min(axis=1)
    return df


def _fix_volume(df: pd.DataFrame, asset_name: str, report: dict) -> pd.DataFrame:
    df = df.copy()
    neg = (df[VOLUME_COL] < 0).sum()
    if neg:
        report["issues"].append(f"Set {neg} negative volume rows to 0")
        df.loc[df[VOLUME_COL] < 0, VOLUME_COL] = 0.0
    # Fill remaining NaN volume with 0
    zero_filled = df[VOLUME_COL].isnull().sum()
    if zero_filled:
        df[VOLUME_COL] = df[VOLUME_COL].fillna(0.0)
    return df


def _detect_and_flag_outliers(
    df: pd.DataFrame, asset_name: str, report: dict
) -> pd.DataFrame:
    df = df.copy()
    outlier_mask = detect_outliers(df)
    df["is_outlier"] = outlier_mask.astype(int)
    n = int(outlier_mask.sum())
    if n:
        report["issues"].append(f"Flagged {n} outlier rows (is_outlier=1)")
    return df


def _add_quality_score_column(df: pd.DataFrame) -> pd.DataFrame:
    """Tag each row with its data quality (1 = good, 0 = suspect)."""
    df = df.copy()
    suspect = df[PRICE_COLS + [VOLUME_COL]].isnull().any(axis=1) | (
        df.get("is_outlier", 0) == 1
    )
    df["data_quality"] = (~suspect).astype(int)
    return df


def _compute_quality_score(df: pd.DataFrame, report: dict) -> float:
    """Overall asset quality score (0–100)."""
    n = len(df)
    if n == 0:
        return 0.0
    null_frac = df[PRICE_COLS + [VOLUME_COL]].isnull().any(axis=1).mean()
    outlier_frac = df.get("is_outlier", pd.Series(0)).mean()
    issue_penalty = min(len(report.get("issues", [])) * 2, 20)
    score = 100.0 * (1 - null_frac) * (1 - outlier_frac * 0.5) - issue_penalty
    return max(0.0, min(100.0, round(score, 1)))
