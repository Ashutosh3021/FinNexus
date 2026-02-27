"""
Market data service using yfinance for historical and real-time data.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd
import numpy as np

from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

# Asset symbols for playground
AVAILABLE_ASSETS = {
    "AAPL": {"name": "Apple Inc.", "type": "stock", "exchange": "NASDAQ"},
    "GOOGL": {"name": "Alphabet Inc.", "type": "stock", "exchange": "NASDAQ"},
    "MSFT": {"name": "Microsoft Corp", "type": "stock", "exchange": "NASDAQ"},
    "AMZN": {"name": "Amazon.com Inc.", "type": "stock", "exchange": "NASDAQ"},
    "TSLA": {"name": "Tesla Inc.", "type": "stock", "exchange": "NASDAQ"},
    "NVDA": {"name": "NVIDIA Corp", "type": "stock", "exchange": "NASDAQ"},
    "META": {"name": "Meta Platforms", "type": "stock", "exchange": "NASDAQ"},
    "BTC-USD": {"name": "Bitcoin", "type": "crypto", "exchange": "CRYPTO"},
    "ETH-USD": {"name": "Ethereum", "type": "crypto", "exchange": "CRYPTO"},
    "SOL-USD": {"name": "Solana", "type": "crypto", "exchange": "CRYPTO"},
    "BNB-USD": {"name": "BNB", "type": "crypto", "exchange": "CRYPTO"},
    "GOLD": {"name": "Gold", "type": "commodity", "exchange": "COMEX"},
    "CL=F": {"name": "Crude Oil", "type": "commodity", "exchange": "NYMEX"},
    "SPY": {"name": "S&P 500 ETF", "type": "etf", "exchange": "NYSE"},
    "^NSEI": {"name": "Nifty 50", "type": "index", "exchange": "NSE"},
    "^GSPC": {"name": "S&P 500", "type": "index", "exchange": "SPX"},
    "^IXIC": {"name": "NASDAQ Composite", "type": "index", "exchange": "NASDAQ"},
}


def get_available_assets(query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get list of available assets for trading.
    
    Args:
        query: Optional search query to filter assets
        
    Returns:
        List of asset dictionaries
    """
    assets = []
    for symbol, info in AVAILABLE_ASSETS.items():
        if query and query.lower() not in symbol.lower() and query.lower() not in info["name"].lower():
            continue
        
        # Get current price
        cached_price = cache_service.get(f"price_{symbol}")
        if cached_price:
            price = cached_price
        else:
            try:
                ticker = yf.Ticker(symbol)
                info_data = ticker.info
                price = info_data.get("currentPrice") or info_data.get("previousClose", 0.0)
                if price:
                    cache_service.set(f"price_{symbol}", price, ttl=60)
            except Exception as e:
                logger.warning(f"Failed to get price for {symbol}: {e}")
                price = 0.0
        
        assets.append({
            "symbol": symbol,
            "name": info["name"],
            "type": info["type"],
            "exchange": info["exchange"],
            "price": round(float(price), 2) if price else 0.0
        })
    
    return assets


def get_historical_data(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d"
) -> Optional[Dict[str, Any]]:
    """
    Get historical OHLCV data for a symbol.
    
    Args:
        symbol: Stock/crypto symbol
        period: Period string (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 1wk, 1mo)
        
    Returns:
        Dictionary with OHLCV data or None on failure
    """
    cache_key = f"history_{symbol}_{period}_{interval}"
    cached = cache_service.get(cache_key)
    if cached:
        return cached
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            logger.warning(f"No data returned for {symbol}")
            return None
        
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Convert to list of dicts
        ohlcv_list = []
        for idx, row in df.iterrows():
            ohlcv_list.append({
                "date": idx.isoformat() if isinstance(idx, datetime) else str(idx),
                "open": round(float(row.get("Open", 0)), 2),
                "high": round(float(row.get("High", 0)), 2),
                "low": round(float(row.get("Low", 0)), 2),
                "close": round(float(row.get("Close", 0)), 2),
                "volume": int(row.get("Volume", 0))
            })
        
        result = {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data": ohlcv_list,
            "count": len(ohlcv_list),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        cache_service.set(cache_key, result, ttl=300)
        return result
        
    except Exception as e:
        logger.error(f"Failed to get historical data for {symbol}: {e}")
        return None


def get_technical_indicators(symbol: str, period: str = "6mo") -> Dict[str, Any]:
    """
    Calculate technical indicators for a symbol.
    
    Args:
        symbol: Stock/crypto symbol
        period: Period string
        
    Returns:
        Dictionary with technical indicators
    """
    hist = get_historical_data(symbol, period)
    if not hist or not hist.get("data"):
        return {}
    
    try:
        df = pd.DataFrame(hist["data"])
        df["Close"] = df["close"]
        df["Open"] = df["open"]
        df["High"] = df["high"]
        df["Low"] = df["low"]
        df["Volume"] = df["volume"]
        
        # Calculate indicators
        df["SMA20"] = df["Close"].rolling(window=20).mean()
        df["SMA50"] = df["Close"].rolling(window=50).mean()
        
        # RSI
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = df["Close"].ewm(span=12).mean()
        ema26 = df["Close"].ewm(span=26).mean()
        df["MACD"] = ema12 - ema26
        df["MACD_signal"] = df["MACD"].ewm(span=9).mean()
        
        latest = df.iloc[-1]
        
        return {
            "symbol": symbol,
            "sma_20": round(float(latest["SMA20"]), 2) if pd.notna(latest["SMA20"]) else None,
            "sma_50": round(float(latest["SMA50"]), 2) if pd.notna(latest["SMA50"]) else None,
            "rsi": round(float(latest["RSI"]), 2) if pd.notna(latest["RSI"]) else None,
            "macd": round(float(latest["MACD"]), 4) if pd.notna(latest.get("MACD")) else None,
            "macd_signal": round(float(latest["MACD_signal"]), 4) if pd.notna(latest.get("MACD_signal")) else None,
            "current_price": latest["Close"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate indicators for {symbol}: {e}")
        return {}


def get_asset_insights(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive asset insights including analysis.
    
    Args:
        symbol: Stock/crypto symbol
        
    Returns:
        Dictionary with insights
    """
    hist = get_historical_data(symbol, period="3mo")
    if not hist or not hist.get("data"):
        return {"error": "No data available"}
    
    try:
        df = pd.DataFrame(hist["data"])
        closes = df["close"].values
        
        # Basic calculations
        current_price = closes[-1]
        sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else current_price
        
        # Calculate returns
        returns = [0]
        for i in range(1, len(closes)):
            returns.append((closes[i] - closes[i-1]) / closes[i-1])
        
        volatility = float(pd.Series(returns).std())
        
        # Trend determination
        if current_price > sma_20 > sma_50:
            trend = "uptrend"
        elif current_price < sma_20 < sma_50:
            trend = "downtrend"
        else:
            trend = "sideways"
        
        # RSI
        rsi_period = 14
        if len(closes) > rsi_period:
            gains = []
            losses = []
            for i in range(len(closes) - rsi_period, len(closes)):
                change = closes[i] - closes[i - 1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / rsi_period
            avg_loss = sum(losses) / rsi_period
            rs = avg_gain / avg_loss if avg_loss > 0 else 100
            rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 50
        
        # Resistance/Support
        high = max(closes[-20:])
        low = min(closes[-20:])
        
        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "resistance": round(high * 1.02, 2),
            "support": round(low * 0.98, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2),
            "rsi": round(rsi, 2),
            "trend": trend,
            "volatility": round(volatility, 4),
            "recommendation": "Hold" if rsi < 70 else "Sell" if rsi > 80 else "Buy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get insights for {symbol}: {e}")
        return {"error": str(e)}


def get_current_prices(symbols: List[str]) -> Dict[str, float]:
    """
    Get current prices for multiple symbols.
    
    Args:
        symbols: List of stock/crypto symbols
        
    Returns:
        Dictionary mapping symbol to current price
    """
    prices = {}
    for symbol in symbols:
        cache_key = f"price_{symbol}"
        cached = cache_service.get(cache_key)
        if cached:
            prices[symbol] = cached
            continue
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get("currentPrice") or info.get("previousClose", 0.0)
            if price:
                prices[symbol] = round(float(price), 2)
                cache_service.set(cache_key, prices[symbol], ttl=60)
        except Exception as e:
            logger.warning(f"Failed to get price for {symbol}: {e}")
            prices[symbol] = 0.0
    
    return prices
