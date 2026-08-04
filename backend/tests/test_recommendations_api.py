from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.intent import IntentProfile
from app.schemas.recommendation import RecommendationResponse


async def _fake_db():
    yield None


def test_recommendations_endpoint(monkeypatch):
    async def fake_run_pipeline(session, text):
        return RecommendationResponse(
            query=text,
            intent=IntentProfile(area="Alfalfa"),
            recommendations=[],
            search_radius_m=1500,
            message="ok",
        )

    monkeypatch.setattr("app.api.recommendations.run_pipeline", fake_run_pipeline)
    app.dependency_overrides[get_db] = _fake_db
    try:
        client = TestClient(app)
        response = client.post("/api/recommendations", json={"text": "cafe en Alfalfa"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "cafe en Alfalfa"
    assert body["search_radius_m"] == 1500
    assert body["message"] == "ok"
    assert body["nearby"] == []


def test_recommendations_requiere_text():
    client = TestClient(app)
    response = client.post("/api/recommendations", json={})
    assert response.status_code == 422


def test_recommendations_rate_limited(monkeypatch):
    """El endpoint que dispara el LLM corta con 429 al superar el limite (salvaguarda de coste)."""
    from app.config import settings

    monkeypatch.setattr(settings, "rate_limit", "2/minute")

    async def fake_run_pipeline(session, text):
        return RecommendationResponse(
            query=text, intent=IntentProfile(), recommendations=[]
        )

    monkeypatch.setattr("app.api.recommendations.run_pipeline", fake_run_pipeline)
    app.dependency_overrides[get_db] = _fake_db
    try:
        client = TestClient(app)
        codes = [
            client.post("/api/recommendations", json={"text": "cafe"}).status_code
            for _ in range(3)
        ]
    finally:
        app.dependency_overrides.clear()

    assert codes[:2] == [200, 200]
    assert codes[2] == 429
