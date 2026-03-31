from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_analyze_accepts_valid_request() -> None:
    payload = {
        "code": "def add(a, b):\n    return a + b",
        "language": "python",
    }
    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert isinstance(body["request_id"], str)
    assert "Result retrieval is not implemented" in body["message"]


def test_analyze_rejects_short_code() -> None:
    payload = {
        "code": "short",
        "language": "python",
    }
    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"


def test_analyze_rejects_unknown_language() -> None:
    payload = {
        "code": "def add(a, b):\n    return a + b",
        "language": "brainfuck",
    }
    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"


def test_healthz() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_meta() -> None:
    response = client.get("/api/v1/meta")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "experimental-mvp"
    assert body["capabilities"] == ["request_intake"]
