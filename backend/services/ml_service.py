"""
ML Service - Wrapper for ML model predictions.
Provides unified interface for all ML operations.
"""
import logging
from typing import Dict, List, Any, Optional

import pandas as pd

from models.ml_loader import (
    predict_direction as ml_predict_direction,
    score_portfolio_risk as ml_score_portfolio_risk,
    classify_portfolio as ml_classify_portfolio,
    analyze_sentiment as ml_analyze_sentiment,
    load_all_models
)

logger = logging.getLogger(__name__)

_models_loaded = False


def initialize_ml_models():
    """Load all ML models on startup."""
    global _models_loaded
    try:
        load_all_models()
        _models_loaded = True
        logger.info("ML models initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ML models: {e}")
        return False


def predict_stock_direction(ohlcv_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Predict stock direction using the trained direction model.
    
    Args:
        ohlcv_df: DataFrame with OHLCV data and calculated features
        
    Returns:
        Dict with direction, confidence, prob_up, prob_down
    """
    if not _models_loaded:
        initialize_ml_models()
    
    try:
        result = ml_predict_direction(ohlcv_df)
        logger.info(f"Direction prediction: {result.get('direction')} ({result.get('confidence')})")
        return result
    except Exception as e:
        logger.error(f"Direction prediction failed: {e}")
        return {
            'direction': 'unknown',
            'confidence': 0.0,
            'prob_up': 0.0,
            'prob_down': 0.0,
            'error': str(e)
        }


def score_portfolio_risk(portfolio_dict: Dict[str, float]) -> Dict[str, Any]:
    """
    Score portfolio risk using the trained risk model.
    
    Args:
        portfolio_dict: Dict with asset allocations
            Keys: stocks, crypto, gold, bonds_proxy, cash
            Values: float (0.0 to 1.0)
            
    Returns:
        Dict with risk_label, score, volatility, expected_return, sharpe_ratio
    """
    if not _models_loaded:
        initialize_ml_models()
    
    try:
        result = ml_score_portfolio_risk(portfolio_dict)
        logger.info(f"Portfolio risk: {result.get('risk_label')} (score: {result.get('score')})")
        return result
    except Exception as e:
        logger.error(f"Risk scoring failed: {e}")
        return {
            'risk_label': 'medium',
            'score': 5,
            'volatility': 0.0,
            'expected_return': 0.0,
            'sharpe_ratio': 0.0,
            'error': str(e)
        }


def classify_portfolio_type(allocations_dict: Dict[str, float]) -> Dict[str, Any]:
    """
    Classify portfolio type using the trained classifier.
    
    Args:
        allocations_dict: Dict with asset allocations
            Keys: stocks, crypto, gold, bonds_proxy, cash
            Values: float (0.0 to 1.0)
            
    Returns:
        Dict with type and suggestions
    """
    if not _models_loaded:
        initialize_ml_models()
    
    try:
        result = ml_classify_portfolio(allocations_dict)
        logger.info(f"Portfolio classification: {result.get('type')}")
        return result
    except Exception as e:
        logger.error(f"Portfolio classification failed: {e}")
        return {
            'type': 'unknown',
            'suggestions': ['Unable to classify portfolio'],
            'error': str(e)
        }


def analyze_news_sentiment(headline: str) -> Dict[str, Any]:
    """
    Analyze sentiment of financial headline using FinBERT.
    
    Args:
        headline: Financial news headline
        
    Returns:
        Dict with sentiment, confidence, impact_score
    """
    if not _models_loaded:
        initialize_ml_models()
    
    try:
        result = ml_analyze_sentiment(headline)
        logger.info(f"Sentiment analysis: {result.get('sentiment')} ({result.get('confidence')})")
        return result
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {
            'sentiment': 'neutral',
            'confidence': 0.0,
            'impact_score': 5,
            'error': str(e)
        }


def analyze_multiple_headlines(headlines: List[str]) -> List[Dict[str, Any]]:
    """
    Analyze sentiment for multiple headlines.
    
    Args:
        headlines: List of financial news headlines
        
    Returns:
        List of sentiment analysis results
    """
    results = []
    for headline in headlines:
        result = analyze_news_sentiment(headline)
        results.append(result)
    return results
