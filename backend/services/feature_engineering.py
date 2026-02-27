"""
Feature Engineering Bridge - Convert raw yfinance data to ML model features.
Provides functions to build features for all 4 trained models.
"""
import json
import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd
import pandas_ta as ta
import yfinance as yf

logger = logging.getLogger(__name__)

FEATURE_COLUMNS_PATH = "models/direction_predictor/feature_columns.json"

DIRECTION_FEATURES = [
    "daily_return", "log_return", "price_vs_20MA", "price_vs_50MA",
    "high_low_range", "RSI", "MACD", "MACD_signal", "MACD_hist",
    "BB_position", "EMA12", "EMA26", "ATR", "OBV", "Stoch_K", "Stoch_D", "ADX"
]


def _load_feature_columns() -> list:
    """Load feature column names from JSON."""
    try:
        with open(FEATURE_COLUMNS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load feature columns, using defaults: {e}")
        return DIRECTION_FEATURES


def build_direction_features(symbol: str, ohlcv_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Build features for direction prediction model from raw OHLCV data.
    
    Args:
        symbol: Stock/crypto symbol
        ohlcv_df: DataFrame with columns [Date, Open, High, Low, Close, Volume]
                  or [date, open, high, low, close, volume]
    
    Returns:
        DataFrame with all 17 features ready for predict_direction()
        Returns None if calculation fails
    """
    try:
        df = ohlcv_df.copy()
        
        if df.empty or len(df) < 50:
            logger.error(f"Insufficient data for {symbol}: need at least 50 rows")
            return None
        
        close_col = 'Close' if 'Close' in df.columns else 'close'
        open_col = 'Open' if 'Open' in df.columns else 'open'
        high_col = 'High' if 'High' in df.columns else 'high'
        low_col = 'Low' if 'Low' in df.columns else 'low'
        volume_col = 'Volume' if 'Volume' in df.columns else 'volume'
        
        if not all(col in df.columns for col in [close_col, open_col, high_col, low_col, volume_col]):
            logger.error(f"Missing required columns in OHLCV data")
            return None
        
        df = df.sort_values(close_col)
        
        df['prev_close'] = df[close_col].shift(1)
        df['daily_return'] = (df[close_col] - df['prev_close']) / df['prev_close']
        df['log_return'] = np.log(df[close_col] / df['prev_close'])
        
        df['SMA20'] = ta.sma(df[close_col], length=20)
        df['SMA50'] = ta.sma(df[close_col], length=50)
        df['price_vs_20MA'] = (df[close_col] - df['SMA20']) / df['SMA20']
        df['price_vs_50MA'] = (df[close_col] - df['SMA50']) / df['SMA50']
        
        df['high_low_range'] = (df[high_col] - df[low_col]) / df[close_col]
        
        df['RSI'] = ta.rsi(df[close_col], length=14)
        
        macd = ta.macd(df[close_col], fast=12, slow=26, signal=9)
        if macd is not None:
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_signal'] = macd['MACDs_12_26_9']
            df['MACD_hist'] = macd['MACDh_12_26_9']
        else:
            df['MACD'] = 0
            df['MACD_signal'] = 0
            df['MACD_hist'] = 0
        
        bbands = ta.bbands(df[close_col], length=20, std=2)
        if bbands is not None:
            bb_upper = bbands['BBU_20_2.0']
            bb_lower = bbands['BBL_20_2.0']
            df['BB_position'] = (df[close_col] - bb_lower) / (bb_upper - bb_lower)
        else:
            df['BB_position'] = 0.5
        
        df['EMA12'] = ta.ema(df[close_col], length=12)
        df['EMA26'] = ta.ema(df[close_col], length=26)
        
        df['ATR'] = ta.atr(df[high_col], df[low_col], df[close_col], length=14)
        
        df['OBV'] = ta.obv(df[close_col], df[volume_col])
        
        stoch = ta.stoch(df[high_col], df[low_col], df[close_col], k=14, d=3)
        if stoch is not None:
            df['Stoch_K'] = stoch['STOCHk_14_3_3']
            df['Stoch_D'] = stoch['STOCHd_14_3_3']
        else:
            df['Stoch_K'] = 50
            df['Stoch_D'] = 50
        
        adx_result = ta.adx(df[high_col], df[low_col], df[close_col], length=14)
        if adx_result is not None:
            df['ADX'] = adx_result['ADX_14']
        else:
            df['ADX'] = 25
        
        feature_cols = _load_feature_columns()
        
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0
        
        result_df = df[feature_cols].fillna(0)
        
        logger.info(f"Built {len(feature_cols)} features for {symbol}")
        return result_df
        
    except Exception as e:
        logger.error(f"Feature engineering failed for {symbol}: {e}")
        return None


def build_risk_features(symbol: str, ohlcv_df: pd.DataFrame, 
                       sp500_df: Optional[pd.DataFrame] = None) -> Optional[Dict[str, float]]:
    """
    Build risk features from OHLCV data.
    
    Args:
        symbol: Stock/crypto symbol
        ohlcv_df: DataFrame with OHLCV data
        sp500_df: Optional S&P 500 data for beta calculation
    
    Returns:
        Dict with volatility, max_drawdown, sharpe_ratio, beta
        Returns None if calculation fails
    """
    try:
        df = ohlcv_df.copy()
        
        if df.empty or len(df) < 30:
            logger.error(f"Insufficient data for {symbol}: need at least 30 rows")
            return None
        
        close_col = 'Close' if 'Close' in df.columns else 'close'
        
        returns = df[close_col].pct_change().dropna()
        
        volatility = float(returns.std())
        
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = float(drawdown.min())
        
        risk_free_rate = 0.065
        mean_return = returns.mean() * 252
        sharpe_ratio = (mean_return - risk_free_rate) / (volatility * np.sqrt(252)) if volatility > 0 else 0
        
        beta = 1.0
        if sp500_df is not None and len(sp500_df) >= 30:
            try:
                sp500_close = 'Close' if 'Close' in sp500_df.columns else 'close'
                sp500_returns = sp500_df[sp500_close].pct_change().dropna()
                
                if len(returns) == len(sp500_returns):
                    covariance = np.cov(returns, sp500_returns)[0][1]
                    sp500_variance = np.var(sp500_returns)
                    beta = float(covariance / sp500_variance) if sp500_variance > 0 else 1.0
            except Exception as e:
                logger.warning(f"Could not calculate beta: {e}")
        
        result = {
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'beta': beta
        }
        
        logger.info(f"Built risk features for {symbol}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Risk feature calculation failed for {symbol}: {e}")
        return None


def build_portfolio_allocations(holdings: list) -> Dict[str, float]:
    """
    Build normalized allocation dict from holdings list.
    
    Args:
        holdings: List of holdings with keys: symbol, qty, currentPrice, assetType
                 assetType should be one of: stock, crypto, gold, bond, cash
    
    Returns:
        Normalized dict with keys: stocks, crypto, gold, bonds_proxy, cash
        All values sum to 1.0
    """
    total_value = 0
    allocations = {
        'stocks': 0.0,
        'crypto': 0.0,
        'gold': 0.0,
        'bonds_proxy': 0.0,
        'cash': 0.0
    }
    
    asset_type_map = {
        'stock': 'stocks',
        'etf': 'stocks',
        'index': 'stocks',
        'crypto': 'crypto',
        'commodity': 'gold',
        'gold': 'gold',
        'bond': 'bonds_proxy',
        'bonds': 'bonds_proxy',
        'cash': 'cash',
        'money': 'cash'
    }
    
    for holding in holdings:
        try:
            value = float(holding.get('qty', 0)) * float(holding.get('currentPrice', 0))
            total_value += value
            
            asset_type = holding.get('assetType', 'stock').lower()
            mapped_type = asset_type_map.get(asset_type, 'stocks')
            allocations[mapped_type] += value
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not process holding: {e}")
            continue
    
    if total_value > 0:
        for key in allocations:
            allocations[key] = allocations[key] / total_value
    
    total = sum(allocations.values())
    if total > 0 and abs(total - 1.0) > 0.01:
        logger.warning(f"Allocations don't sum to 1.0: {total}, normalizing")
        for key in allocations:
            allocations[key] = allocations[key] / total
    
    logger.info(f"Built portfolio allocations: {allocations}")
    return allocations


def fetch_and_build_features(symbol: str, period: str = "6mo") -> Optional[pd.DataFrame]:
    """
    Fetch data from yfinance and build features in one step.
    
    Args:
        symbol: Stock/crypto symbol
        period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)
    
    Returns:
        DataFrame with features ready for predict_direction()
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            logger.error(f"No data fetched for {symbol}")
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        return build_direction_features(symbol, df)
        
    except Exception as e:
        logger.error(f"Failed to fetch and build features for {symbol}: {e}")
        return None
