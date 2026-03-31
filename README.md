# CodeShield AI

Minimal FastAPI backend with a local rule-based project path analyzer.

## Why this exists

Most projects in this space start with big promises and unclear runtime behavior.
This one starts with a small contract that you can run and inspect in minutes.

The goal is to build a real code-analysis backend in public, one verifiable step at a time.

## What it does today

- Accepts analysis intake requests via `POST /api/v1/analyze`
- Supports local project scanning via `POST /api/v1/analyze/path`
- Scans local source files and returns likely production risk findings
- Exposes health and API metadata endpoints:
  - `GET /healthz`
  - `GET /api/v1/meta`

## Local-only warning (important)

`POST /api/v1/analyze/path` is for **local developer use only**.

- It reads filesystem paths on the same machine where this API runs.
- It is **not safe for public internet exposure**.
- Do not deploy this endpoint publicly without strict access controls and sandboxing.

## Demo

This MVP supports intake and local path analysis.

### 1) Submit code for analysis

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d "{\"code\":\"def get_total(items):\n    total = 0\n    for item in items:\n        total += item['price']\n    return total\",\"language\":\"python\"}"
```

### 2) Current response (real)

```json
{
  "request_id": "9f0d9d4a-7a9a-4e49-8fb7-8d4c2c8ab3f1",
  "status": "pending",
  "message": "Analysis request accepted. Result retrieval is not implemented in this MVP."
}
```

### 3) Analyze a local project path

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
    "This is a heuristic rule-based analysis.",
    "Results may include false positives.",
    "The analyzer does not execute code or build a full AST-based semantic model."
  ]
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

Open:
- `http://localhost:8000/docs`

## API contract (current)

### `POST /api/v1/analyze`

Request body:

```json
{
  "code": "string, 10..100000 chars",
  "language": "python | javascript | typescript | go | rust | java | cpp | csharp"
}
```

Response (`202`):

```json
{
  "request_id": "uuid",
  "status": "pending",
  "message": "Analysis request accepted. Result retrieval is not implemented in this MVP."
}
```

Validation errors return `422` with a structured error payload.

### `POST /api/v1/analyze/path`

Request body:

```json
{
  "path": "C:/Users/kadir/Desktop/autoforge",
  "max_files": 300,
  "max_file_size_kb": 512
}
```

Behavior:
- Accepts absolute local directory paths only
- Recursively scans supported source files: `.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.go`, `.rs`, `.java`
- Ignores common junk directories (`.git`, `node_modules`, `dist`, `build`, etc.)
- Skips oversized and non-UTF8 files
- Returns heuristic findings and a capped risk score

## Limitations

- Heuristic scanner; not a full semantic or runtime analyzer
- Can produce false positives and false negatives
- Does not execute code
- Local-only endpoint should not be internet-exposed

## Why this might be worth starring

If you like small, runnable backends with explicit scope and no fake demo layers, this repository is meant to be a clean base to follow, fork, or extend.

## Repository structure

```text
.
├── backend/
│   ├── analyzer.py
│   ├── main.py
│   ├── models.py
│   └── scanner.py
├── docs/
│   └── MVP_SCOPE.md
├── tests/
│   └── test_api.py
├── .github/
│   └── ISSUE_TEMPLATE/
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```
