"""
Feature Engineering Module — FinNexus
Adds technical indicators, volatility, volume, momentum, and target variable.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

TRADING_DAYS_PER_YEAR = 252
MIN_ROWS_FOR_FEATURE = 30  # minimum rows needed before we start computing


# ─── Public API ───────────────────────────────────────────────────────────────

def create_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all technical indicators to the OHLCV dataframe.
    Input must have: Date, Open, High, Low, Close, Volume
    """
    df = df.copy().sort_values("Date").reset_index(drop=True)

    df = _add_return_features(df)
    df = _add_moving_averages(df)
    df = _add_rsi(df)
    df = _add_macd(df)
    df = _add_bollinger_bands(df)
    df = _add_atr(df)
    df = _add_adx(df)
    df = _add_stochastic(df)
    df = _add_volume_features(df)
    df = _add_volatility_features(df)
    df = _add_price_level_features(df)

    return df


def create_target(df: pd.DataFrame, horizon: int = 7) -> pd.DataFrame:
    """
    Binary classification target: 1 if close price is higher `horizon` days ahead.

    Adds columns:
      future_price_{horizon}d
      target_{horizon}d
    """
    df = df.copy()
    col = f"target_{horizon}d"
    future_col = f"future_price_{horizon}d"
    df[future_col] = df["Close"].shift(-horizon)
    df[col] = (df[future_col] > df["Close"]).astype(float)
    df.loc[df[future_col].isnull(), col] = np.nan
    return df


def create_all_targets(df: pd.DataFrame, horizons: list = None) -> pd.DataFrame:
    """Create targets for multiple horizons."""
    if horizons is None:
        horizons = [3, 5, 7, 10, 14]
    for h in horizons:
        df = create_target(df, horizon=h)
    return df


def create_context_features(
    df: pd.DataFrame,
    market_df: pd.DataFrame,
    market_label: str = "market",
    rolling_window: int = 30,
) -> pd.DataFrame:
    """
    Merge market-level context features into the asset dataframe.

    Parameters
    ----------
    df           : Asset OHLCV + features dataframe (must have Date column)
    market_df    : Market reference dataframe (BTC for crypto, NIFTY for stocks)
    market_label : Prefix for added columns, e.g. 'btc' or 'nifty'
    rolling_window : Window for rolling correlation
    """
    df = df.copy()
    mkt = market_df.copy()[["Date", "Close"]].rename(
        columns={"Close": f"{market_label}_close"}
    )
    # Compute market return_1d if not present
    mkt[f"{market_label}_return_1d"] = mkt[f"{market_label}_close"].pct_change()
    mkt[f"{market_label}_return_7d"] = mkt[f"{market_label}_close"].pct_change(7)
    mkt[f"{market_label}_vol_30d"] = (
        mkt[f"{market_label}_return_1d"]
        .rolling(30)
        .std()
        * np.sqrt(TRADING_DAYS_PER_YEAR)
    )
    mkt["Date"] = pd.to_datetime(mkt["Date"]).dt.normalize()
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()

    df = df.merge(mkt, on="Date", how="left")

    # Rolling correlation with market
    asset_ret = df["return_1d"] if "return_1d" in df.columns else df["Close"].pct_change()
    mkt_ret = df[f"{market_label}_return_1d"]
    df[f"corr_{market_label}_{rolling_window}d"] = (
        asset_ret.rolling(rolling_window)
        .corr(mkt_ret)
        .round(4)
    )

    # Beta (slope of regression of asset returns on market returns)
    def _rolling_beta(asset_r, mkt_r, w):
        cov = asset_r.rolling(w).cov(mkt_r)
        var = mkt_r.rolling(w).var()
        return (cov / var).replace([np.inf, -np.inf], np.nan)

    df[f"beta_{market_label}_{rolling_window}d"] = _rolling_beta(
        asset_ret, mkt_ret, rolling_window
    )

    return df


def prepare_features(
    df: pd.DataFrame,
    target_col: str = "target_7d",
    drop_future_cols: bool = True,
) -> pd.DataFrame:
    """
    Final step: drop rows with NaN in target or critical features,
    drop future-price leakage columns.
    """
    df = df.copy()
    if drop_future_cols:
        future_cols = [c for c in df.columns if c.startswith("future_price_")]
        df = df.drop(columns=future_cols, errors="ignore")

    if target_col in df.columns:
        df = df.dropna(subset=[target_col])

    # Drop rows where ALL price features are NaN (head of dataframe warm-up)
    critical = ["Close", "return_1d", "sma_20"]
    existing_critical = [c for c in critical if c in df.columns]
    if existing_critical:
        df = df.dropna(subset=existing_critical)

    return df.reset_index(drop=True)


# ─── Internal Feature Builders ────────────────────────────────────────────────

def _add_return_features(df: pd.DataFrame) -> pd.DataFrame:
    c = df["Close"]
    df["return_1d"] = c.pct_change(1)
    df["return_3d"] = c.pct_change(3)
    df["return_7d"] = c.pct_change(7)
    df["return_14d"] = c.pct_change(14)
    df["return_30d"] = c.pct_change(30)
    df["log_return_1d"] = np.log(c / c.shift(1))

    # Momentum: signed percentile of return_Xd over past 90 days
    for w in [7, 30]:
        col = f"return_{w}d"
        df[f"momentum_{w}d"] = (
            df[col]
            .rolling(90)
            .apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False)
        )
    return df


def _add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    c = df["Close"]
    for w in [20, 50, 100, 200]:
        df[f"sma_{w}"] = c.rolling(w).mean()
        df[f"dist_from_sma_{w}"] = (c - df[f"sma_{w}"]) / df[f"sma_{w}"]

    for w in [12, 26]:
        df[f"ema_{w}"] = c.ewm(span=w, adjust=False).mean()

    # Golden/Death cross signals
    df["golden_cross"] = (df["sma_50"] > df["sma_200"]).astype(int)
    df["above_sma_200"] = (c > df["sma_200"]).astype(int)
    df["above_sma_50"] = (c > df["sma_50"]).astype(int)
    return df


def _add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))
    df["rsi_overbought"] = (df["rsi_14"] > 70).astype(int)
    df["rsi_oversold"] = (df["rsi_14"] < 30).astype(int)
    return df


def _add_macd(df: pd.DataFrame) -> pd.DataFrame:
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["macd_line"] = ema12 - ema26
    df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()
    df["macd_histogram"] = df["macd_line"] - df["macd_signal"]
    df["macd_bullish_cross"] = (
        (df["macd_line"] > df["macd_signal"])
        & (df["macd_line"].shift(1) <= df["macd_signal"].shift(1))
    ).astype(int)
    return df


def _add_bollinger_bands(df: pd.DataFrame, period: int = 20, n_std: float = 2.0) -> pd.DataFrame:
    mid = df["Close"].rolling(period).mean()
    std = df["Close"].rolling(period).std()
    upper = mid + n_std * std
    lower = mid - n_std * std
    df["bb_upper"] = upper
    df["bb_lower"] = lower
    df["bb_middle"] = mid
    df["bb_bandwidth"] = (upper - lower) / mid.replace(0, np.nan)
    df["bb_pct_b"] = (df["Close"] - lower) / (upper - lower).replace(0, np.nan)
    return df


def _add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - prev_close).abs(),
            (df["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr_14"] = tr.ewm(com=period - 1, adjust=False).mean()
    # Normalised ATR
    df["natr_14"] = df["atr_14"] / df["Close"].replace(0, np.nan)
    return df


def _add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Average Directional Index."""
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)

    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    dm_pos = ((high - prev_high) > (prev_low - low)).astype(float) * (high - prev_high).clip(lower=0)
    dm_neg = ((prev_low - low) > (high - prev_high)).astype(float) * (prev_low - low).clip(lower=0)

    tr_smooth = tr.ewm(com=period - 1, adjust=False).mean()
    dp_smooth = dm_pos.ewm(com=period - 1, adjust=False).mean()
    dn_smooth = dm_neg.ewm(com=period - 1, adjust=False).mean()

    di_pos = 100 * dp_smooth / tr_smooth.replace(0, np.nan)
    di_neg = 100 * dn_smooth / tr_smooth.replace(0, np.nan)

    dx = 100 * (di_pos - di_neg).abs() / (di_pos + di_neg).replace(0, np.nan)
    df["adx_14"] = dx.ewm(com=period - 1, adjust=False).mean()
    df["di_plus"] = di_pos
    df["di_minus"] = di_neg
    df["adx_strong_trend"] = (df["adx_14"] > 25).astype(int)
    return df


def _add_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    low_min = df["Low"].rolling(k_period).min()
    high_max = df["High"].rolling(k_period).max()
    denom = (high_max - low_min).replace(0, np.nan)
    df["stoch_k"] = 100 * (df["Close"] - low_min) / denom
    df["stoch_d"] = df["stoch_k"].rolling(d_period).mean()
    return df


def _add_volume_features(df: pd.DataFrame) -> pd.DataFrame:
    vol = df["Volume"].replace(0, np.nan)

    df["volume_ma_7d"] = vol.rolling(7).mean()
    df["volume_ma_30d"] = vol.rolling(30).mean()
    df["volume_ratio_7_30"] = df["volume_ma_7d"] / df["volume_ma_30d"].replace(0, np.nan)
    df["volume_spike"] = (vol > df["volume_ma_30d"] * 2).astype(int)

    # On-Balance Volume
    price_dir = np.sign(df["Close"].diff())
    df["obv"] = (price_dir * vol.fillna(0)).cumsum()

    # VWAP (rolling 20-day approximation)
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    df["vwap_20d"] = (typical_price * vol.fillna(0)).rolling(20).sum() / vol.fillna(0).rolling(20).sum()

    # Volume-price trend
    df["vpt"] = (vol * df["Close"].pct_change()).cumsum()
    return df


def _add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    log_ret = np.log(df["Close"] / df["Close"].shift(1))

    df["vol_7d"] = log_ret.rolling(7).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    df["vol_30d"] = log_ret.rolling(30).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    df["vol_60d"] = log_ret.rolling(60).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    df["vol_ratio_30_60"] = df["vol_30d"] / df["vol_60d"].replace(0, np.nan)

    # Parkinson volatility (uses High/Low, more efficient estimator)
    hl_ratio = np.log(df["High"] / df["Low"].replace(0, np.nan))
    df["parkinson_vol_30d"] = (
        hl_ratio.pow(2).rolling(30).mean() / (4 * np.log(2))
    ).apply(np.sqrt) * np.sqrt(TRADING_DAYS_PER_YEAR)

    return df


def _add_price_level_features(df: pd.DataFrame) -> pd.DataFrame:
    c = df["Close"]

    # 52-week / 6-month highs & lows
    for w in [126, 252]:  # ~6mo, ~1yr
        label = "6mo" if w == 126 else "1yr"
        rolling_high = df["High"].rolling(w).max()
        rolling_low = df["Low"].rolling(w).min()
        df[f"price_to_high_{label}"] = c / rolling_high.replace(0, np.nan)
        df[f"price_to_low_{label}"] = c / rolling_low.replace(0, np.nan)

    # Day range as fraction of close
    df["day_range_pct"] = (df["High"] - df["Low"]) / c.replace(0, np.nan)

    # Gap (open vs prev close)
    df["gap_pct"] = (df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1).replace(0, np.nan)

    return df
