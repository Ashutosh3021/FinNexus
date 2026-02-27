import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.main as main_mod


def test_app_importable_and_routes():
    app = getattr(main_mod, "app", None)
    assert isinstance(app, FastAPI)

    # Ensure key routers are registered (advisor, education, portfolio)
    paths = [r.path for r in app.router.routes]
    assert any(p.startswith("/advisor") for p in paths), f"advisor route missing: {paths[:10]}"
    assert any("/api/portfolio" in p for p in paths), "portfolio routes missing"


def test_context_summary_endpoint_returns_structure():
    client = TestClient(main_mod.app)
    resp = client.get("/advisor/context-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success", False) is True
    assert "data" in data
    assert "portfolio_summary" in data["data"]
    assert "prediction_stats" in data["data"]
    assert "news_headlines" in data["data"]
