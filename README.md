# CodeShield AI

Minimal FastAPI backend for code-analysis request intake.

## Why this exists

Most projects in this space start with big promises and unclear runtime behavior.
This one starts with a small contract that you can run and inspect in minutes.

The goal is to build a real code-analysis backend in public, one verifiable step at a time.

## What it does today

- Accepts analysis intake requests via `POST /api/v1/analyze`
- Validates payload shape and supported language values
- Returns a generated `request_id` with `pending` status
- Exposes health and API metadata endpoints:
  - `GET /healthz`
  - `GET /api/v1/meta`

## What's planned (not implemented yet)

- Result retrieval endpoint (`GET /api/v1/analysis/{request_id}`)
- Persistence for request lifecycle
- Real analysis execution behind intake
- Basic auth and rate limiting

## Demo

This MVP currently supports request intake only.

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

### 3) Next step (not implemented yet)

The next planned endpoint is `GET /api/v1/analysis/{request_id}` to fetch completed results.
It does not exist in this version.

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

## Limitations

- No completed analysis retrieval yet
- No persistence
- No authentication or rate limits
- Not production-ready for sensitive/private code

## Why this might be worth starring

If you like small, runnable backends with explicit scope and no fake demo layers, this repository is meant to be a clean base to follow, fork, or extend.

## Repository structure

```text
.
├── backend/
│   └── main.py
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
