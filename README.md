# CodeShield AI

Minimal FastAPI backend with a **local experimental codebase risk scanner**: rule-based heuristics for many languages, plus **AST-assisted checks for Python** when the file parses.

## Why this exists

Most projects in this space start with big promises and unclear runtime behavior.
This one starts with a small contract that you can run and inspect in minutes.

The goal is to build a real code-analysis backend in public, one verifiable step at a time.

## What it does today

- Accepts analysis intake requests via `POST /api/v1/analyze` (stub intake; no result polling yet)
- **Synchronous** local project scan: `POST /api/v1/analyze/path`
- **Asynchronous** scan (SQLite-backed job, same machine): `POST /api/v1/analyze/path/async` → poll `GET /api/v1/analysis/{request_id}`
- **CLI** using the same engine: `python -m backend.cli scan <ABS_PATH>`
- Optional **YAML rules** file to enable/disable rules or override severities (`rules_config_path` in JSON, or `--rules` on CLI)
- **SARIF 2.1.0** export for completed async jobs: `GET /api/v1/analysis/{request_id}/sarif`
- **HTML report** for completed async jobs: `GET /api/v1/analysis/{request_id}/report.html`
- Health and API metadata: `GET /healthz`, `GET /api/v1/meta`

## Local-only warning (important)

Path analysis endpoints are for **local developer use only**.

- They read filesystem paths on the same machine where this API runs.
- They are **not safe for public internet exposure**.
- Do not deploy them publicly without strict access controls and sandboxing.

## Demo

### 1) Submit code for analysis (intake stub)

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d "{\"code\":\"def get_total(items):\n    total = 0\n    for item in items:\n        total += item['price']\n    return total\",\"language\":\"python\"}"
```

### 2) Analyze a local project path (synchronous)

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/path" \
  -H "Content-Type: application/json" \
  -d "{\"path\":\"C:/Users/kadir/Desktop/autoforge\"}"
```

Example response:

```json
{
  "request_id": "9f0d9d4a-7a9a-4e49-8fb7-8d4c2c8ab3f1",
  "status": "completed",
  "summary": {
    "files_scanned": 12,
    "issues_found": 5,
    "risk_score": 68
  },
  "findings": [
    {
      "type": "Potential N+1 Query",
      "severity": "HIGH",
      "file": "backend/users.py",
      "line": 42,
      "message": "Database-like call appears inside a loop.",
      "impact": "This may increase latency significantly as data volume grows.",
      "suggestion": "Batch queries, prefetch related data, or move data access outside the loop."
    }
  ],
  "limitations": [
    "This is a heuristic rule-based analysis; Python also uses AST-assisted checks where syntax is valid.",
    "Results may include false positives.",
    "The analyzer does not execute code or build a full semantic model for non-Python languages."
  ]
}
```

### 3) Async job + SARIF / HTML (large or slow scans)

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/path/async" \
  -H "Content-Type: application/json" \
  -d "{\"path\":\"C:/Users/kadir/Desktop/autoforge\"}"
```

Poll until `status` is `completed` or `failed`:

```bash
curl "http://localhost:8000/api/v1/analysis/<REQUEST_ID>"
```

SARIF (completed jobs only):

```bash
curl "http://localhost:8000/api/v1/analysis/<REQUEST_ID>/sarif"
```

HTML report:

```bash
curl "http://localhost:8000/api/v1/analysis/<REQUEST_ID>/report.html" -o report.html
```

### 4) CLI (no HTTP server)

```bash
python -m backend.cli scan C:/Users/kadir/Desktop/CodeShield --json
python -m backend.cli scan C:/Users/kadir/Desktop/CodeShield --sarif out.sarif.json --html report.html
```

### 5) Rule overrides (YAML)

Copy `backend/config/default_rules.yaml`, edit `enabled` / optional `severity`, then pass the absolute path:

```json
{
  "path": "C:/Users/kadir/Desktop/autoforge",
  "rules_config_path": "C:/Users/kadir/Desktop/CodeShield/my_rules.yaml"
}
```

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000/docs`.

### Job database location

Async jobs are stored in SQLite. Default file: `data/codeshield.db` under the current working directory. Override with:

`CODESHIELD_DB_PATH=/path/to/codeshield.db`

## API contract (current)

### `POST /api/v1/analyze`

Request body: `code` (10..100000 chars), `language` enum.

Response `202` with `pending` (intake only; no retrieval yet).

### `POST /api/v1/analyze/path`

Request body:

```json
{
  "path": "C:/Users/kadir/Desktop/autoforge",
  "max_files": 300,
  "max_file_size_kb": 512,
  "rules_config_path": null
}
```

Response `200` with `completed` and findings.

### `POST /api/v1/analyze/path/async`

Same body as above. Response `202` with `request_id` and `pending`. Poll `GET /api/v1/analysis/{request_id}`.

### `GET /api/v1/analysis/{request_id}`

Returns `pending`, `completed` (summary + findings + limitations), or `failed` (error message).

## Limitations

- Rule-based and heuristic; **not** a full semantic or runtime analyzer for all languages
- Python: AST helps when syntax is valid; invalid files fall back to line heuristics only
- Can produce false positives and false negatives
- Does not execute project code
- Path endpoints must not be internet-exposed

## CI

GitHub Actions workflow (`.github/workflows/codeshield.yml`) installs dependencies and runs `pytest`.

## Why this might be worth starring

If you like small, runnable backends with explicit scope and no fake demo layers, this repository is meant to be a clean base to follow, fork, or extend.

## Repository structure

```text
.
├── backend/
│   ├── analysis_service.py
│   ├── analyzer.py
│   ├── cli.py
│   ├── config/
│   │   └── default_rules.yaml
│   ├── db.py
│   ├── heuristic_analyzer.py
│   ├── html_report.py
│   ├── job_runner.py
│   ├── jobs.py
│   ├── main.py
│   ├── models.py
│   ├── python_ast_analyzer.py
│   ├── rules_config.py
│   ├── sarif_export.py
│   └── scanner.py
├── docs/
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
│       └── codeshield.yml
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```
