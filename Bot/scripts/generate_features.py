"""
FinNexus — Feature Engineering Script
======================================
Generates `Data/Features/{AssetClass}/{symbol}_features.csv` from
`Data/Cleaned/{AssetClass}/{symbol}_cleaned.csv`.

Features generated per row:
  - OHLCV passthrough
  - Returns: 1d, 3d, 7d, 14d, 30d, log_return_1d
  - Momentum: 7d, 30d
  - Moving averages: SMA 20/50/100/200, EMA 12/26
  - Distance from MAs: dist_from_sma_20/50/100/200
  - Crossovers: golden_cross (SMA50 > SMA200), above_sma_200, above_sma_50
  - Oscillators: RSI 14, overbought/oversold flags
  - MACD: line, signal, histogram, bullish_cross
  - Bollinger Bands: upper, lower, middle, bandwidth, %B
  - ATR: atr_14, natr_14
  - Directional: ADX 14, DI+, DI-, strong_trend flag
  - Stochastic: %K, %D
  - Volume: ma_7d/30d, ratio, spike flag, OBV, VWAP 20d, VPT
  - Volatility: vol_7d/30d/60d, ratio, Parkinson 30d
  - Price ratios: to 6m/1yr high/low, day range%, gap%
  - Targets: forward 3/5/7/10/14 day direction (1=up, 0=down)

Run:
    python -m Bot.scripts.generate_features             # all assets
    python -m Bot.scripts.generate_features --asset-class Crypto
    python -m Bot.scripts.generate_features --symbol BTC
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
try:
    from Bot import config as cfg
    _PROJECT_ROOT = cfg.PROJECT_ROOT
except Exception:
    _PROJECT_ROOT = Path(__file__).parent.parent.parent

_CLEANED_ROOT  = _PROJECT_ROOT / "Data" / "Cleaned"
_FEATURES_ROOT = _PROJECT_ROOT / "Data" / "Features"

# Asset class subdirectory mapping
_ASSET_CLASSES = ["Commodities", "Crypto", "ETFs", "Futures", "Stocks"]


# ---------------------------------------------------------------------------
# Technical indicator helpers
# ---------------------------------------------------------------------------

def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    up   = high.diff()
    down = -low.diff()
    plus_dm  = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    atr_s = _atr(high, low, close, period)
    plus_di  = 100 * plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr_s.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr_s.replace(0, np.nan)
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    adx_s = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return adx_s, plus_di, minus_di


def _obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (direction * volume).cumsum()


def _parkinson_vol(high: pd.Series, low: pd.Series, window: int = 30) -> pd.Series:
    log_hl = np.log(high / low.replace(0, np.nan)) ** 2
    return np.sqrt(log_hl.rolling(window).mean() / (4 * np.log(2)))


# ---------------------------------------------------------------------------
# Core feature builder
# ---------------------------------------------------------------------------

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical features to a cleaned OHLCV DataFrame.
    Input columns required: Date, Open, High, Low, Close, Volume
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # ── Data quality flag ──────────────────────────────────────────────────
    if "is_outlier" not in df.columns:
        df["is_outlier"] = 0
    if "data_quality" not in df.columns:
        df["data_quality"] = 1

    c = df["Close"]
    h = df["High"]
    lo = df["Low"]
    v  = df["Volume"].fillna(0)

    # ── Returns ────────────────────────────────────────────────────────────
    df["return_1d"]  = c.pct_change(1)
    df["return_3d"]  = c.pct_change(3)
    df["return_7d"]  = c.pct_change(7)
    df["return_14d"] = c.pct_change(14)
    df["return_30d"] = c.pct_change(30)
    df["log_return_1d"] = np.log(c / c.shift(1))

    # ── Momentum ──────────────────────────────────────────────────────────
    df["momentum_7d"]  = c - c.shift(7)
    df["momentum_30d"] = c - c.shift(30)

    # ── Moving averages ────────────────────────────────────────────────────
    for period in [20, 50, 100, 200]:
        df[f"sma_{period}"]           = c.rolling(period).mean()
        df[f"dist_from_sma_{period}"] = (c - df[f"sma_{period}"]) / df[f"sma_{period}"].replace(0, np.nan)

    df["ema_12"] = c.ewm(span=12, adjust=False).mean()
    df["ema_26"] = c.ewm(span=26, adjust=False).mean()

    df["golden_cross"] = (df["sma_50"] > df["sma_200"]).astype(int)
    df["above_sma_200"] = (c > df["sma_200"]).astype(int)
    df["above_sma_50"]  = (c > df["sma_50"]).astype(int)

    # ── RSI ────────────────────────────────────────────────────────────────
    df["rsi_14"]        = _rsi(c)
    df["rsi_overbought"] = (df["rsi_14"] > 70).astype(int)
    df["rsi_oversold"]   = (df["rsi_14"] < 30).astype(int)

    # ── MACD ───────────────────────────────────────────────────────────────
    df["macd_line"]       = df["ema_12"] - df["ema_26"]
    df["macd_signal"]     = df["macd_line"].ewm(span=9, adjust=False).mean()
    df["macd_histogram"]  = df["macd_line"] - df["macd_signal"]
    df["macd_bullish_cross"] = (
        (df["macd_line"] > df["macd_signal"]) &
        (df["macd_line"].shift(1) <= df["macd_signal"].shift(1))
    ).astype(int)

    # ── Bollinger Bands ────────────────────────────────────────────────────
    bb_mid = c.rolling(20).mean()
    bb_std = c.rolling(20).std()
    df["bb_upper"]     = bb_mid + 2 * bb_std
    df["bb_lower"]     = bb_mid - 2 * bb_std
    df["bb_middle"]    = bb_mid
    df["bb_bandwidth"] = (df["bb_upper"] - df["bb_lower"]) / bb_mid.replace(0, np.nan)
    df["bb_pct_b"]     = (c - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"]).replace(0, np.nan)

    # ── ATR ────────────────────────────────────────────────────────────────
    df["atr_14"]  = _atr(h, lo, c)
    df["natr_14"] = df["atr_14"] / c.replace(0, np.nan) * 100

    # ── ADX ────────────────────────────────────────────────────────────────
    adx_s, plus_di, minus_di = _adx(h, lo, c)
    df["adx_14"]            = adx_s
    df["di_plus"]           = plus_di
    df["di_minus"]          = minus_di
    df["adx_strong_trend"]  = (adx_s > 25).astype(int)

    # ── Stochastic ─────────────────────────────────────────────────────────
    low_14  = lo.rolling(14).min()
    high_14 = h.rolling(14).max()
    df["stoch_k"] = 100 * (c - low_14) / (high_14 - low_14).replace(0, np.nan)
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()

    # ── Volume ─────────────────────────────────────────────────────────────
    df["volume_ma_7d"]  = v.rolling(7).mean()
    df["volume_ma_30d"] = v.rolling(30).mean()
    df["volume_ratio_7_30"] = df["volume_ma_7d"] / df["volume_ma_30d"].replace(0, np.nan)
    df["volume_spike"]  = (df["volume_ratio_7_30"] > 2.0).astype(int)
    df["obv"]           = _obv(c, v)
    df["vwap_20d"]      = (c * v).rolling(20).sum() / v.rolling(20).sum().replace(0, np.nan)
    df["vpt"]           = (v * df["return_1d"]).cumsum()

    # ── Volatility ─────────────────────────────────────────────────────────
    df["vol_7d"]  = df["log_return_1d"].rolling(7).std()
    df["vol_30d"] = df["log_return_1d"].rolling(30).std()
    df["vol_60d"] = df["log_return_1d"].rolling(60).std()
    df["vol_ratio_30_60"] = df["vol_30d"] / df["vol_60d"].replace(0, np.nan)
    df["parkinson_vol_30d"] = _parkinson_vol(h, lo, 30)

    # ── Price ratios ───────────────────────────────────────────────────────
    df["price_to_high_6mo"]  = c / h.rolling(126).max().replace(0, np.nan)
    df["price_to_low_6mo"]   = c / lo.rolling(126).min().replace(0, np.nan)
    df["price_to_high_1yr"]  = c / h.rolling(252).max().replace(0, np.nan)
    df["price_to_low_1yr"]   = c / lo.rolling(252).min().replace(0, np.nan)
    df["day_range_pct"]      = (h - lo) / c.replace(0, np.nan)
    df["gap_pct"]            = (df["Open"] - c.shift(1)) / c.shift(1)

    # ── Forward targets ────────────────────────────────────────────────────
    for n in [3, 5, 7, 10, 14]:
        df[f"target_{n}d"] = (c.shift(-n) > c).astype(float)
        # Mark last n rows as NaN (no future data)
        df.loc[df.index[-n:], f"target_{n}d"] = np.nan

    return df


# ---------------------------------------------------------------------------
# File processor
# ---------------------------------------------------------------------------

def process_file(
    cleaned_path: Path,
    output_path: Path,
    symbol: str,
) -> bool:
    """Process one cleaned CSV → features CSV. Returns True on success."""
    try:
        df = pd.read_csv(cleaned_path)
        required = {"Date", "Open", "High", "Low", "Close", "Volume"}
        missing = required - set(df.columns)
        if missing:
            logger.warning("process_file: %s missing columns %s — skipping", cleaned_path.name, missing)
            return False

        df = build_features(df)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info("generate_features: %-16s → %s (%d rows, %d cols)",
                    symbol, output_path.name, len(df), len(df.columns))
        return True
    except Exception as exc:
        logger.error("generate_features: failed for %s: %s", symbol, exc)
        return False


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run(
    asset_class_filter: Optional[str] = None,
    symbol_filter: Optional[str] = None,
    cleaned_root: Path = _CLEANED_ROOT,
    features_root: Path = _FEATURES_ROOT,
) -> dict:
    """
    Process all cleaned CSVs and generate feature files.

    Returns a summary dict: {asset_class: {symbol: success_bool}}.
    """
    summary: dict = {}
    total = ok = 0

    for asset_class in _ASSET_CLASSES:
        if asset_class_filter and asset_class.lower() != asset_class_filter.lower():
            continue

        cleaned_dir  = cleaned_root  / asset_class
        features_dir = features_root / asset_class

        if not cleaned_dir.exists():
            logger.debug("generate_features: no cleaned dir for %s, skipping", asset_class)
            continue

        summary[asset_class] = {}

        for cleaned_path in sorted(cleaned_dir.glob("*_cleaned.csv")):
            # Derive symbol from filename e.g. "BTC_cleaned.csv" → "BTC"
            stem = cleaned_path.stem  # "BTC_cleaned"
            symbol = stem.replace("_cleaned", "")

            if symbol_filter and symbol.lower() != symbol_filter.lower():
                continue

            # Output: features_dir/symbol_features.csv
            output_name = f"{symbol}_features.csv"
            output_path = features_dir / output_name

            total += 1
            success = process_file(cleaned_path, output_path, symbol)
            summary[asset_class][symbol] = success
            if success:
                ok += 1

    logger.info("generate_features: %d/%d files processed successfully", ok, total)
    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )
    parser = argparse.ArgumentParser(description="FinNexus feature engineering pipeline")
    parser.add_argument(
        "--asset-class",
        default="",
        help="Filter by asset class: Commodities, Crypto, ETFs, Futures, Stocks",
    )
    parser.add_argument(
        "--symbol",
        default="",
        help="Filter by symbol, e.g. BTC",
    )
    args = parser.parse_args()

    summary = run(
        asset_class_filter=args.asset_class or None,
        symbol_filter=args.symbol or None,
    )

    print("\n=== FEATURE GENERATION SUMMARY ===")
    for asset_class, results in summary.items():
        ok_count = sum(results.values())
        print(f"  {asset_class}: {ok_count}/{len(results)} files OK")
        for symbol, success in results.items():
            status = "✓" if success else "✗"
            print(f"    {status} {symbol}")


if __name__ == "__main__":
    main()
