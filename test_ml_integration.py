#!/usr/bin/env python3
"""
End-to-end ML integration tests for FinNexus backend.
Run: python test_ml_integration.py
"""
import sys
import traceback

import yfinance as yf
import pandas as pd

from models import ml_loader
from backend.services.feature_engineering import (
    build_direction_features, build_risk_features, build_portfolio_allocations, fetch_and_build_features
)


def test_predict_direction():
    symbol = "AAPL"
    print(f"\nTesting predict_direction for {symbol}")
    df = yf.Ticker(symbol).history(period="100d")
    if df.empty:
        raise RuntimeError("Failed to fetch AAPL data")

    # Normalize columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.rename(columns={
        'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close', 'Volume': 'Volume'
    })

    features = build_direction_features(symbol, df)
    assert features is not None, "Feature builder returned None"

    res = ml_loader.predict_direction(features)
    print("Predict direction:", res)
    assert res.get('direction') in ('up', 'down')
    assert 0.0 <= res.get('confidence', 0.0) <= 1.0


def test_score_portfolio_risk():
    print("\nTesting score_portfolio_risk")
    allocations = {'stocks': 0.4, 'crypto': 0.2, 'gold': 0.2, 'bonds_proxy': 0.1, 'cash': 0.1}
    res = ml_loader.score_portfolio_risk(allocations)
    print("Risk result:", res)
    assert res.get('risk_label') in ("low", "medium", "high")
    assert 1 <= int(res.get('score', 0)) <= 10


def test_classify_portfolio():
    print("\nTesting classify_portfolio")
    allocations = {'stocks':0.4, 'crypto':0.3, 'gold':0.1, 'bonds_proxy':0.1, 'cash':0.1}
    res = ml_loader.classify_portfolio(allocations)
    print("Classify result:", res)
    assert res.get('type') in ("aggressive", "balanced", "conservative", "risky", 'unknown')


def test_analyze_sentiment():
    print("\nTesting analyze_sentiment")
    headlines = [
        "Company announces record profits and beats estimates",  # bullish
        "Major data breach raises concerns for customer security",  # bearish
        "Central bank holds rates steady as inflation moderates"  # neutral
    ]

    for h in headlines:
        res = ml_loader.analyze_sentiment(h)
        print("Headline:", h)
        print("Sentiment:", res)
        assert res.get('sentiment') in ("positive", "negative", "neutral")


def test_full_playground_flow():
    print("\nTesting full playground flow (BTC-USD)")
    symbol = "BTC-USD"
    df = yf.Ticker(symbol).history(period="6mo")
    if df.empty:
        raise RuntimeError("Failed to fetch BTC-USD data")

    features = build_direction_features(symbol, df)
    assert features is not None

    pred = ml_loader.predict_direction(features)
    print("Prediction:", pred)

    # Simulate user chooses opposite
    user_choice = 'down' if pred.get('direction') == 'up' else 'up'

    # Mock Gemini explanation (simple stub)
    explanation = f"Model predicted {pred.get('direction')} with {pred.get('confidence'):.2f}, user chose {user_choice}"
    print("Explanation:", explanation)


def run_all():
    try:
        test_predict_direction()
        test_score_portfolio_risk()
        test_classify_portfolio()
        test_analyze_sentiment()
        test_full_playground_flow()
        print("\n✅ ALL ML INTEGRATION TESTS PASSED")
    except Exception as e:
        print("\n❌ ML INTEGRATION TESTS FAILED:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all()
