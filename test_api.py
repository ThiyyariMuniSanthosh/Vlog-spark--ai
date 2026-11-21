from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "gemini_configured" in data


def test_validation_rejects_short_title():
    res = client.post("/api/generate-content", json={"title": "ab"})
    assert res.status_code == 422


def test_missing_api_key_returns_503(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    res = client.post(
        "/api/generate-content",
        json={
            "title": "Why students should learn Artificial Intelligence",
            "platform": "YouTube Shorts",
            "language": "Telugu",
        },
    )
    assert res.status_code == 503
    assert "GEMINI_API_KEY" in res.json()["detail"]
