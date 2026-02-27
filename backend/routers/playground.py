"""
Playground Router - Stock prediction and battle endpoints.
Integrates ML direction prediction with Gemini explanations.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException

from ..schemas import (
    PredictRequest, PredictionResponse, 
    BattleRequest, BattleResponse,
    APIResponse
)
from ..services import market_service
from ..services import ml_service
from ..services.feature_engineering import build_direction_features, fetch_and_build_features

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/playground", tags=["playground"])


@router.post("/predict", response_model=APIResponse)
async def predict_stock_direction(request: PredictRequest) -> APIResponse:
    """Predict stock direction using ML model."""
    try:
        symbol = request.symbol.upper()
        ohlcv_data = request.ohlcv_data
        
        if not ohlcv_data or len(ohlcv_data) < 50:
            raise HTTPException(
                status_code=400,
                detail="Need at least 50 days of OHLCV data for prediction"
            )
        
        df = pd.DataFrame([{
            'Date': item.date,
            'Open': item.open,
            'High': item.high,
            'Low': item.low,
            'Close': item.close,
            'Volume': item.volume
        } for item in ohlcv_data])
        
        features_df = build_direction_features(symbol, df)
        
        if features_df is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to build features from OHLCV data"
            )
        
        prediction = ml_service.predict_stock_direction(features_df)
        
        response_data = {
            "symbol": symbol,
            "direction": prediction.get("direction", "unknown"),
            "confidence": prediction.get("confidence", 0.0),
            "prob_up": prediction.get("prob_up", 0.0),
            "prob_down": prediction.get("prob_down", 0.0)
        }
        
        return APIResponse(success=True, data=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return APIResponse(success=False, error=str(e))


@router.get("/predict/{symbol}", response_model=APIResponse)
async def predict_symbol_direction(symbol: str, period: str = "6mo") -> APIResponse:
    """Predict stock direction by fetching data automatically."""
    try:
        symbol = symbol.upper()
        
        features_df = fetch_and_build_features(symbol, period)
        
        if features_df is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch or build features for {symbol}"
            )
        
        prediction = ml_service.predict_stock_direction(features_df)
        
        response_data = {
            "symbol": symbol,
            "direction": prediction.get("direction", "unknown"),
            "confidence": prediction.get("confidence", 0.0),
            "prob_up": prediction.get("prob_up", 0.0),
            "prob_down": prediction.get("prob_down", 0.0),
            "period": period
        }
        
        return APIResponse(success=True, data=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed for {symbol}: {e}")
        return APIResponse(success=False, error=str(e))


@router.post("/battle", response_model=APIResponse)
async def battle_prediction(request: BattleRequest) -> APIResponse:
    """Battle endpoint - user predicts and compares with ML model."""
    try:
        symbol = request.symbol.upper()
        user_prediction = request.user_prediction.lower()
        ohlcv_data = request.ohlcv_data
        
        if not ohlcv_data or len(ohlcv_data) < 50:
            raise HTTPException(
                status_code=400,
                detail="Need at least 50 days of OHLCV data"
            )
        
        df = pd.DataFrame([{
            'Date': item.date,
            'Open': item.open,
            'High': item.high,
            'Low': item.low,
            'Close': item.close,
            'Volume': item.volume
        } for item in ohlcv_data])
        
        features_df = build_direction_features(symbol, df)
        
        if features_df is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to build features"
            )
        
        ml_prediction = ml_service.predict_stock_direction(features_df)
        ml_direction = ml_prediction.get("direction", "unknown")
        
        last_price = ohlcv_data[-1].close
        first_price = ohlcv_data[0].open
        
        actual_direction = "up" if last_price > first_price else "down"
        
        user_won = user_prediction == actual_direction
        ml_won = ml_direction == actual_direction
        
        if user_won and ml_won:
            result = "both_correct"
            pnl = 100
        elif user_won and not ml_won:
            result = "user_wins"
            pnl = 150
        elif not user_won and ml_won:
            result = "ml_wins"
            pnl = -50
        else:
            result = "both_wrong"
            pnl = -100
        
        explanation = _generate_explanation(
            symbol, user_prediction, ml_direction, actual_direction,
            ohlcv_data, ml_prediction
        )
        
        response_data = {
            "result": result,
            "actual_direction": actual_direction,
            "pnl": pnl,
            "ml_prediction": ml_direction,
            "ml_confidence": ml_prediction.get("confidence", 0.0),
            "explanation": explanation
        }
        
        return APIResponse(success=True, data=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Battle failed: {e}")
        return APIResponse(success=False, error=str(e))


def _generate_explanation(
    symbol: str, 
    user_pred: str, 
    ml_pred: str, 
    actual: str,
    ohlcv_data: List,
    ml_result: Dict[str, Any]
) -> str:
    """Generate explanation for battle result."""
    confidence = ml_result.get("confidence", 0.0)
    
    explanation = f"""Battle Results for {symbol}:

Your prediction: {user_pred.upper()}
ML prediction: {ml_pred.upper()} (confidence: {confidence:.1%})
Actual outcome: {actual.upper()}

"""
    
    if user_pred == actual:
        explanation += f"You correctly predicted {actual.upper()}!"
    else:
        explanation += f"Your prediction of {user_pred.upper()} was incorrect."
    
    if ml_pred == actual:
        explanation += f"\nML correctly predicted {actual.upper()}."
    else:
        explanation += f"\nML incorrectly predicted {ml_pred.upper()}."
    
    explanation += f"\n\nTechnical Context: The ML model used 17 technical indicators including RSI, MACD, Bollinger Bands, and Stochastic oscillators to make this prediction."
    
    return explanation.strip()


@router.get("/assets")
async def get_available_assets(q: str = None):
    """Get list of available assets for trading."""
    try:
        assets = market_service.get_available_assets(query=q)
        return APIResponse(success=True, data={"assets": assets, "count": len(assets)})
    except Exception as e:
        logger.error(f"Failed to get assets: {e}")
        return APIResponse(success=False, error=str(e))


@router.get("/history/{symbol}")
async def get_symbol_history(symbol: str, period: str = "6mo", interval: str = "1d"):
    """Get historical OHLCV data for a symbol."""
    try:
        symbol = symbol.upper()
        data = market_service.get_historical_data(symbol, period, interval)
        
        if data is None:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        return APIResponse(success=True, data=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get history for {symbol}: {e}")
        return APIResponse(success=False, error=str(e))


@router.get("/insights/{symbol}")
async def get_symbol_insights(symbol: str):
    """Get technical insights for a symbol."""
    try:
        symbol = symbol.upper()
        insights = market_service.get_asset_insights(symbol)
        
        if "error" in insights:
            raise HTTPException(status_code=404, detail=insights["error"])
        
        return APIResponse(success=True, data=insights)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get insights for {symbol}: {e}")
        return APIResponse(success=False, error=str(e))


@router.post("/reveal", response_model=APIResponse)
async def reveal_answer(request: PredictRequest) -> APIResponse:
    """Reveal the ML prediction with Gemini explanation context."""
    try:
        symbol = request.symbol.upper()
        ohlcv_data = request.ohlcv_data
        
        if not ohlcv_data or len(ohlcv_data) < 50:
            raise HTTPException(
                status_code=400,
                detail="Need at least 50 days of OHLCV data"
            )
        
        df = pd.DataFrame([{
            'Date': item.date,
            'Open': item.open,
            'High': item.high,
            'Low': item.low,
            'Close': item.close,
            'Volume': item.volume
        } for item in ohlcv_data])
        
        features_df = build_direction_features(symbol, df)
        
        if features_df is None:
            raise HTTPException(status_code=500, detail="Failed to build features")
        
        prediction = ml_service.predict_stock_direction(features_df)
        
        response_data = {
            "symbol": symbol,
            "direction": prediction.get("direction", "unknown"),
            "confidence": prediction.get("confidence", 0.0),
            "prob_up": prediction.get("prob_up", 0.0),
            "prob_down": prediction.get("prob_down", 0.0),
            "gemini_context": {
                "prediction": prediction.get("direction"),
                "confidence": prediction.get("confidence"),
                "indicators": "RSI, MACD, Bollinger Bands, Stochastic, ADX"
            }
        }
        
        return APIResponse(success=True, data=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reveal failed: {e}")
        return APIResponse(success=False, error=str(e))
