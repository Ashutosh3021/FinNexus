"""
FastAPI Integration Helper for ML Models
=========================================
This module loads all trained ML models and provides prediction functions
for the FinNexus FastAPI application.

Usage:
    from lib.ml_loader import predict_direction, score_portfolio_risk, 
                             classify_portfolio, analyze_sentiment
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd
import joblib
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model paths
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')

# Global model variables (loaded on startup)
direction_model = None
direction_scaler = None
direction_feature_columns = None

risk_model = None
risk_scaler = None

portfolio_model = None
portfolio_scaler = None

finbert_tokenizer = None
finbert_model = None

# Models loaded flag
models_loaded = False


def load_all_models():
    """
    Load all trained models into memory on FastAPI startup.
    Call this function during application startup.
    """
    global direction_model, direction_scaler, direction_feature_columns
    global risk_model, risk_scaler, portfolio_model, portfolio_scaler
    global finbert_tokenizer, finbert_model, models_loaded
    
    try:
        # Load Direction Predictor
        direction_model = joblib.load(os.path.join(MODELS_DIR, 'direction_predictor', 'best_direction_model.joblib'))
        direction_scaler = joblib.load(os.path.join(MODELS_DIR, 'direction_predictor', 'direction_scaler.joblib'))
        
        with open(os.path.join(MODELS_DIR, 'direction_predictor', 'feature_columns.json'), 'r') as f:
            direction_feature_columns = json.load(f)
        
        logger.info("✅ Direction Predictor loaded")
        
        # Load Risk Scorer
        risk_model = joblib.load(os.path.join(MODELS_DIR, 'risk_scorer', 'risk_scorer_model.joblib'))
        risk_scaler = joblib.load(os.path.join(MODELS_DIR, 'risk_scorer', 'risk_scaler.joblib'))
        
        logger.info("✅ Risk Scorer loaded")
        
        # Load Portfolio Classifier
        portfolio_model = joblib.load(os.path.join(MODELS_DIR, 'portfolio_classifier', 'portfolio_classifier.joblib'))
        portfolio_scaler = joblib.load(os.path.join(MODELS_DIR, 'portfolio_classifier', 'portfolio_scaler.joblib'))
        
        logger.info("✅ Portfolio Classifier loaded")
        
        # Load FinBERT (will be loaded lazily when first needed)
        logger.info("✅ FinBERT will be loaded lazily on first use")
        
        models_loaded = True
        logger.info("🎉 All ML models loaded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error loading models: {e}")
        raise


def _ensure_models_loaded():
    """Ensure models are loaded before making predictions"""
    if not models_loaded:
        load_all_models()


def _load_finbert():
    """Lazy load FinBERT model"""
    global finbert_tokenizer, finbert_model
    
    if finbert_model is None:
        try:
            from transformers import BertTokenizer, BertForSequenceClassification
            finbert_tokenizer = BertTokenizer.from_pretrained('ProsusAI/finbert')
            finbert_model = BertForSequenceClassification.from_pretrained('ProsusAI/finbert')
            finbert_model.eval()
            logger.info("✅ FinBERT loaded successfully")
        except Exception as e:
            logger.error(f"❌ Error loading FinBERT: {e}")
            raise
    
    return finbert_tokenizer, finbert_model


def predict_direction(ohlcv_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Predict stock direction (up/down) based on OHLCV data.
    
    Args:
        ohlcv_df: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
    
    Returns:
        Dict with 'direction' ('up' or 'down'), 'confidence' (float)
    """
    _ensure_models_loaded()
    
    try:
        # Create features from OHLCV
        features = _create_direction_features(ohlcv_df)
        
        # Handle missing features
        for col in direction_feature_columns:
            if col not in features.columns:
                features[col] = 0
        
        # Select and order features
        X = features[direction_feature_columns].fillna(0)
        
        # Scale features
        X_scaled = direction_scaler.transform(X)
        
        # Predict
        prediction = direction_model.predict(X_scaled)[0]
        probability = direction_model.predict_proba(X_scaled)[0]
        
        result = {
            'direction': 'up' if prediction == 1 else 'down',
            'confidence': float(max(probability)),
            'prob_up': float(probability[1]),
            'prob_down': float(probability[0])
        }
        
        logger.info(f"[{datetime.now().isoformat()}] Direction prediction: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Direction prediction failed: {e}")
        return {
            'direction': 'unknown',
            'confidence': 0.0,
            'error': str(e)
        }


def _create_direction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create technical indicator features from OHLCV data"""
    df = df.copy()
    
    # Price features
    df['prev_close'] = df['Close'].shift(1)
    df['daily_return'] = (df['Close'] - df['prev_close']) / df['prev_close']
    df['log_return'] = np.log(df['Close'] / df['prev_close'])
    
    # SMA
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['price_vs_20MA'] = (df['Close'] - df['SMA20']) / df['SMA20']
    df['price_vs_50MA'] = (df['Close'] - df['SMA50']) / df['SMA50']
    
    df['high_low_range'] = (df['High'] - df['Low']) / df['Close']
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    
    # Bollinger Bands
    sma20 = df['Close'].rolling(window=20).mean()
    std20 = df['Close'].rolling(window=20).std()
    df['BB_upper'] = sma20 + (std20 * 2)
    df['BB_lower'] = sma20 - (std20 * 2)
    df['BB_position'] = (df['Close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
    df['BB_position'] = df['BB_position'].clip(0, 1)
    
    # EMA
    df['EMA12'] = df['Close'].ewm(span=12).mean()
    df['EMA26'] = df['Close'].ewm(span=26).mean()
    
    # ATR
    tr1 = df['High'] - df['Low']
    tr2 = abs(df['High'] - df['prev_close'])
    tr3 = abs(df['Low'] - df['prev_close'])
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    # OBV
    obv = (df['Volume'] * ((df['Close'] - df['prev_close']).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0)))).cumsum()
    df['OBV'] = obv
    
    # Stochastic
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['Stoch_K'] = 100 * (df['Close'] - low_14) / (high_14 - low_14)
    df['Stoch_K'] = df['Stoch_K'].clip(0, 100)
    df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
    
    # ADX
    df['ADX'] = 25
    
    return df


def score_portfolio_risk(portfolio_dict: Dict[str, float]) -> Dict[str, Any]:
    """
    Score portfolio risk based on asset allocations.
    
    Args:
        portfolio_dict: Dict with asset names as keys and allocations as values
                       e.g., {'stocks': 0.4, 'crypto': 0.2, 'gold': 0.2, 'bonds_proxy': 0.1, 'cash': 0.1}
    
    Returns:
        Dict with 'risk_label' ('low', 'medium', 'high'), 'score' (1-10)
    """
    _ensure_models_loaded()
    
    try:
        # If caller provided precomputed risk metrics (volatility, max_drawdown, sharpe_ratio, beta)
        if all(k in portfolio_dict for k in ['volatility', 'max_drawdown', 'sharpe_ratio', 'beta']):
            volatility = float(portfolio_dict.get('volatility', 0.0))
            max_drawdown = float(portfolio_dict.get('max_drawdown', 0.0))
            sharpe_ratio = float(portfolio_dict.get('sharpe_ratio', 0.0))
            beta = float(portfolio_dict.get('beta', 1.0))
        else:
            # Calculate risk metrics from allocations
            typical_volatility = {
                'stocks': 0.20,
                'crypto': 0.60,
                'gold': 0.15,
                'bonds_proxy': 0.05,
                'cash': 0.01
            }

            # Weighted average volatility
            volatility = sum(portfolio_dict.get(k, 0) * typical_volatility.get(k, 0.2)
                             for k in typical_volatility)

            # Max drawdown estimate
            max_drawdown = -0.3 * volatility

            # Sharpe ratio estimate
            expected_return = sum(portfolio_dict.get(k, 0) * {'stocks': 0.10, 'crypto': 0.25,
                                                               'gold': 0.05, 'bonds_proxy': 0.03,
                                                               'cash': 0.02}.get(k, 0)
                                 for k in portfolio_dict)
            sharpe_ratio = (expected_return - 0.065) / max(volatility, 0.01)

            # Beta estimate
            beta = portfolio_dict.get('stocks', 0) * 1.0 + portfolio_dict.get('crypto', 0) * 1.5

        # Create feature vector for model
        features = np.array([[volatility, max_drawdown, sharpe_ratio, beta]])
        features_scaled = risk_scaler.transform(features)

        # Predict
        prediction = risk_model.predict(features_scaled)[0]

        # Map to labels
        risk_labels = {0: 'low', 1: 'medium', 2: 'high'}
        risk_label = risk_labels.get(prediction, 'medium')

        # Calculate score (1-10)
        score = int(1 + (1 - min(volatility, 1.0)) * 9)

        result = {
            'risk_label': risk_label,
            'score': score,
            'volatility': float(volatility),
            'expected_return': float(expected_return) if 'expected_return' in locals() else 0.0,
            'sharpe_ratio': float(sharpe_ratio)
        }

        logger.info(f"[{datetime.now().isoformat()}] Portfolio risk: {result}")
        return result

    except Exception as e:
        logger.error(f"❌ Risk scoring failed: {e}")
        return {
            'risk_label': 'medium',
            'score': 5,
            'error': str(e)
        }


def classify_portfolio(allocations_dict: Dict[str, float]) -> Dict[str, Any]:
    """
    Classify portfolio type based on asset allocations.
    
    Args:
        allocations_dict: Dict with asset class percentages
                         e.g., {'stocks': 0.5, 'crypto': 0.3, 'gold': 0.1, 'bonds_proxy': 0.05, 'cash': 0.05}
    
    Returns:
        Dict with 'type' and 'suggestions'
    """
    _ensure_models_loaded()
    
    try:
        # Prepare features
        asset_classes = ['stocks', 'crypto', 'gold', 'bonds_proxy', 'cash']
        
        # Expected return (typical)
        typical_returns = {'stocks': 0.10, 'crypto': 0.25, 'gold': 0.05, 'bonds_proxy': 0.03, 'cash': 0.02}
        expected_return = sum(allocations_dict.get(k, 0) * typical_returns.get(k, 0) for k in asset_classes)
        
        # Volatility
        typical_vol = {'stocks': 0.20, 'crypto': 0.60, 'gold': 0.15, 'bonds_proxy': 0.05, 'cash': 0.01}
        volatility = sum(allocations_dict.get(k, 0) * typical_vol.get(k, 0.2) for k in asset_classes)
        
        # Sharpe ratio
        sharpe_ratio = (expected_return - 0.065) / max(volatility, 0.01)
        
        # Diversification score (1 - HHI)
        hhi = sum(allocations_dict.get(k, 0)**2 for k in asset_classes)
        diversification_score = 1 - hhi
        
        # Create feature vector
        features = np.array([[
            allocations_dict.get('stocks', 0),
            allocations_dict.get('crypto', 0),
            allocations_dict.get('gold', 0),
            allocations_dict.get('bonds_proxy', 0),
            allocations_dict.get('cash', 0),
            expected_return,
            volatility,
            sharpe_ratio,
            diversification_score
        ]])
        
        features_scaled = portfolio_scaler.transform(features)
        
        # Predict
        prediction = portfolio_model.predict(features_scaled)[0]
        
        # Generate suggestions
        suggestions = _generate_suggestions(allocations_dict, prediction)
        
        result = {
            'type': prediction,
            'suggestions': suggestions
        }
        
        logger.info(f"[{datetime.now().isoformat()}] Portfolio classification: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Portfolio classification failed: {e}")
        return {
            'type': 'unknown',
            'suggestions': ['Unable to classify portfolio'],
            'error': str(e)
        }


def _generate_suggestions(allocations: Dict[str, float], portfolio_type: str) -> List[str]:
    """Generate portfolio improvement suggestions"""
    suggestions = []
    
    if portfolio_type == 'aggressive':
        suggestions.append("Consider reducing crypto allocation for more stability")
        suggestions.append("High volatility - ensure long investment horizon")
    
    elif portfolio_type == 'conservative':
        suggestions.append("Portfolio is well-diversified for stability")
        suggestions.append("Consider small growth allocation for better returns")
    
    elif portfolio_type == 'balanced':
        suggestions.append("Good risk-return balance maintained")
        suggestions.append("Rebalance annually to maintain allocation")
    
    elif portfolio_type == 'risky':
        if allocations.get('crypto', 0) > 0.20:
            suggestions.append("Reduce crypto exposure to lower risk")
        if allocations.get('stocks', 0) > 0.70:
            suggestions.append("Add diversification with gold or bonds")
    
    if not suggestions:
        suggestions.append("Review and rebalance portfolio periodically")
    
    return suggestions


def analyze_sentiment(headline: str) -> Dict[str, Any]:
    """
    Analyze sentiment of a financial headline using FinBERT.
    
    Args:
        headline: Financial news headline string
    
    Returns:
        Dict with 'sentiment', 'confidence', 'impact_score'
    """
    try:
        tokenizer, model = _load_finbert()
        
        # Tokenize
        inputs = tokenizer(headline, return_tensors='pt', truncation=True, max_length=512)
        
        # Predict
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=1)
            pred = torch.argmax(probs, dim=1).item()
            confidence = probs[0][pred].item()
        
        # Map to labels
        labels = ['negative', 'neutral', 'positive']
        sentiment = labels[pred]
        
        # Impact score (1-10)
        impact_score = int(1 + confidence * 9)
        
        result = {
            'sentiment': sentiment,
            'confidence': float(confidence),
            'impact_score': impact_score
        }
        
        logger.info(f"[{datetime.now().isoformat()}] Sentiment analysis: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Sentiment analysis failed: {e}")
        return {
            'sentiment': 'neutral',
            'confidence': 0.0,
            'impact_score': 5,
            'error': str(e)
        }


# Import torch for FinBERT
import torch


# Example usage when run directly
if __name__ == "__main__":
    print("Loading models...")
    load_all_models()
    
    print("\n📊 Testing predictions...")
    
    # Test direction prediction (requires valid OHLCV data)
    # sample_df = pd.DataFrame({...})
    # print(predict_direction(sample_df))
    
    # Test portfolio risk scoring
    sample_portfolio = {'stocks': 0.4, 'crypto': 0.2, 'gold': 0.2, 'bonds_proxy': 0.1, 'cash': 0.1}
    print(f"\nPortfolio Risk: {score_portfolio_risk(sample_portfolio)}")
    
    # Test portfolio classification
    print(f"Portfolio Type: {classify_portfolio(sample_portfolio)}")
    
    # Test sentiment analysis
    sample_headline = "Federal Reserve raises interest rates amid inflation concerns"
    print(f"Sentiment: {analyze_sentiment(sample_headline)}")
