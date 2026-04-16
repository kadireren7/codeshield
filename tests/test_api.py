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
    caps = body["capabilities"]
    assert "request_intake" in caps
    assert "local_path_analyzer" in caps
    assert "async_path_jobs" in caps


def test_analyze_path_valid_small_project(tmp_path) -> None:
    project_dir = tmp_path / "demo_project"
    project_dir.mkdir()
    (project_dir / "app.py").write_text(
        "items = [1, 2, 3]\nfor i in items:\n    print(i)\n",
        encoding="utf-8",
    )

    response = client.post("/api/v1/analyze/path", json={"path": str(project_dir)})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["summary"]["files_scanned"] == 1
    assert isinstance(body["summary"]["risk_score"], int)
    assert "heuristic" in body["limitations"][0].lower()


def test_analyze_path_missing_path_field() -> None:
    response = client.post("/api/v1/analyze/path", json={})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"


def test_analyze_path_rejects_file_path(tmp_path) -> None:
    file_path = tmp_path / "single.py"
    file_path.write_text("print('hello')\n", encoding="utf-8")

    response = client.post("/api/v1/analyze/path", json={"path": str(file_path)})

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "invalid_request"
    assert "directory" in body["message"].lower()


def test_analyze_path_skips_ignored_directories(tmp_path) -> None:
    project_dir = tmp_path / "scan_test"
    src_dir = project_dir / "src"
    ignored_dir = project_dir / "node_modules"
    src_dir.mkdir(parents=True)
    ignored_dir.mkdir(parents=True)

    (src_dir / "good.py").write_text("for x in [1,2]:\n    print(x)\n", encoding="utf-8")
    (ignored_dir / "bad.js").write_text("while(true){ db.query('x') }\n", encoding="utf-8")

    response = client.post("/api/v1/analyze/path", json={"path": str(project_dir)})

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["files_scanned"] == 1


def test_analyze_path_finds_deliberate_risks(tmp_path) -> None:
    project_dir = tmp_path / "risk_project"
    project_dir.mkdir()
    (project_dir / "backend.py").write_text(
        (
            "import requests\n\n"
            "results = []\n"
            "for user_id in user_ids:\n"
            "    item = db.query('select * from users where id = ?', user_id)\n"
            "    results.append(item)\n\n"
            "for a in rows:\n"
            "    for b in rows:\n"
            "        pass\n\n"
            "response = requests.get('https://example.com')\n"
            "except:\n"
            "    pass\n"
        ),
        encoding="utf-8",
    )

    response = client.post("/api/v1/analyze/path", json={"path": str(project_dir)})

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["issues_found"] > 0
    finding_types = {item["type"] for item in body["findings"]}
    assert "Potential N+1 Query" in finding_types
    assert "Potential Memory Growth" in finding_types
    assert "Potential Performance Bottleneck" in finding_types
    assert "Missing Timeout" in finding_types


def test_analyze_path_async_completes(tmp_path) -> None:
    project_dir = tmp_path / "async_proj"
    project_dir.mkdir()
    (project_dir / "a.py").write_text("x = 1\n", encoding="utf-8")

    response = client.post("/api/v1/analyze/path/async", json={"path": str(project_dir)})
    assert response.status_code == 202
    job_id = response.json()["request_id"]

    poll = client.get(f"/api/v1/analysis/{job_id}")
    assert poll.status_code == 200
    body = poll.json()
    assert body["status"] == "completed"
    assert body["summary"]["files_scanned"] == 1


def test_sarif_for_completed_async_job(tmp_path) -> None:
    project_dir = tmp_path / "sarif_proj"
    project_dir.mkdir()
    (project_dir / "a.py").write_text("print(1)\n", encoding="utf-8")

    response = client.post("/api/v1/analyze/path/async", json={"path": str(project_dir)})
    job_id = response.json()["request_id"]

    sarif = client.get(f"/api/v1/analysis/{job_id}/sarif")
    assert sarif.status_code == 200
    payload = sarif.json()
    assert payload["version"] == "2.1.0"
    assert payload["runs"][0]["tool"]["driver"]["name"] == "CodeShield"
