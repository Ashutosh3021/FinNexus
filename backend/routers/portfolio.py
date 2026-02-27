"""
Portfolio Router - Portfolio analysis and management endpoints.
Integrates ML risk scoring and portfolio classification.
"""
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException

from ..schemas import (
    PortfolioAnalyzeRequest, RiskResponse,
    PortfolioTypeResponse, RebalanceRequest,
    APIResponse
)
from ..services import ml_service
from ..services.feature_engineering import build_portfolio_allocations
from ..services.market_service import get_current_prices

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.post("/analyze", response_model=APIResponse)
async def analyze_portfolio(request: PortfolioAnalyzeRequest) -> APIResponse:
    """
    Analyze portfolio risk using ML model.
    
    Takes list of holdings, builds allocation dict, and returns risk analysis.
    """
    try:
        holdings = request.holdings
        
        if not holdings:
            raise HTTPException(status_code=400, detail="No holdings provided")
        
        allocations = build_portfolio_allocations([
            {
                'symbol': h.symbol,
                'qty': h.qty,
                'currentPrice': h.current_price,
                'assetType': h.asset
            }
            for h in holdings
        ])
        
        risk_result = ml_service.score_portfolio_risk(allocations)
        
        type_result = ml_service.classify_portfolio_type(allocations)
        
        response_data = {
            "risk": {
                "risk_label": risk_result.get("risk_label", "medium"),
                "score": risk_result.get("score", 5),
                "volatility": risk_result.get("volatility", 0.0),
                "expected_return": risk_result.get("expected_return", 0.0),
                "sharpe_ratio": risk_result.get("sharpe_ratio", 0.0)
            },
            "portfolio_type": {
                "type": type_result.get("type", "unknown"),
                "suggestions": type_result.get("suggestions", [])
            }
        }
        
        return APIResponse(success=True, data=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio analysis failed: {e}")
        return APIResponse(success=False, error=str(e))


@router.post("/risk", response_model=APIResponse)
async def score_portfolio_risk(request: RebalanceRequest) -> APIResponse:
    """
    Score portfolio risk level using ML model.
    
    Takes allocation dict with keys: stocks, crypto, gold, bonds_proxy, cash
    """
    try:
        allocations = request.current_allocations
        
        required_keys = {'stocks', 'crypto', 'gold', 'bonds_proxy', 'cash'}
        if not all(k in allocations for k in required_keys):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required keys. Need: {required_keys}"
            )
        
        risk_result = ml_service.score_portfolio_risk(allocations)
        
        response_data = {
            "risk_label": risk_result.get("risk_label", "medium"),
            "score": risk_result.get("score", 5),
            "volatility": risk_result.get("volatility", 0.0),
            "expected_return": risk_result.get("expected_return", 0.0),
            "sharpe_ratio": risk_result.get("sharpe_ratio", 0.0)
        }
        
        return APIResponse(success=True, data=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk scoring failed: {e}")
        return APIResponse(success=False, error=str(e))


@router.post("/classify", response_model=APIResponse)
async def classify_portfolio_type(request: RebalanceRequest) -> APIResponse:
    """
    Classify portfolio type using ML model.
    
    Returns portfolio type (aggressive, balanced, conservative, risky) and suggestions.
    """
    try:
        allocations = request.current_allocations
        
        required_keys = {'stocks', 'crypto', 'gold', 'bonds_proxy', 'cash'}
        if not all(k in allocations for k in required_keys):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required keys. Need: {required_keys}"
            )
        
        result = ml_service.classify_portfolio_type(allocations)
        
        response_data = {
            "portfolio_type": result.get("type", "unknown"),
            "suggestions": result.get("suggestions", [])
        }
        
        return APIResponse(success=True, data=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio classification failed: {e}")
        return APIResponse(success=False, error=str(e))


@router.post("/rebalance", response_model=APIResponse)
async def rebalance_portfolio(request: RebalanceRequest) -> APIResponse:
    """
    Suggest portfolio rebalancing based on ML analysis.
    """
    try:
        allocations = request.current_allocations
        
        risk_result = ml_service.score_portfolio_risk(allocations)
        type_result = ml_service.classify_portfolio_type(allocations)
        
        risk_label = risk_result.get("risk_label", "medium")
        
        suggestions = []
        
        if risk_label == "high":
            suggestions.append("Consider reducing high-risk assets (crypto) allocation")
            suggestions.append("Increase bonds_proxy or cash allocation for stability")
        elif risk_label == "low":
            suggestions.append("Portfolio is very conservative")
            suggestions.append("Consider modest increase in growth assets")
        
        suggestions.extend(type_result.get("suggestions", []))
        
        response_data = {
            "current_risk": risk_label,
            "current_type": type_result.get("type", "unknown"),
            "suggestions": suggestions[:5],
            "actions": [
                {"type": "reduce_crypto" if risk_label == "high" else "maintain"},
                {"type": "rebalance_annually"}
            ]
        }
        
        return APIResponse(success=True, data=response_data)
        
    except Exception as e:
        logger.error(f"Rebalance failed: {e}")
        return APIResponse(success=False, error=str(e))
