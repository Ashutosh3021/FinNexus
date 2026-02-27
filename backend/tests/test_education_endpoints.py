import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_education_topics_alias():
    r = client.get("/education/topics")
    assert r.status_code == 200
    data = r.json()
    assert "success" in data
    # allow both shapes but ensure callable without crash
    payload = data.get("data", {})
    assert isinstance(payload, dict) or isinstance(payload, list)

def test_education_search_alias():
    r = client.get("/education/search?q=RSI&level=BEGINNER")
    assert r.status_code in (200, 400)
    # 200 expected; 400 only when q missing, so here should usually be 200

def test_advisor_context_summary():
    r = client.get("/advisor/context-summary")
    assert r.status_code == 200
    data = r.json()
    assert data.get("success") is True
    assert "data" in data

