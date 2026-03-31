# MVP Scope

This project is intentionally small for public release.

## Included

- FastAPI service entrypoint in `backend/main.py`
- Request validation for:
  - `code` length (`10..100000`)
  - supported languages enum
- Request intake endpoint:
  - `POST /api/v1/analyze`
- Utility endpoints:
  - `GET /healthz`
  - `GET /api/v1/meta`
- Basic API tests in `tests/test_api.py`

## Excluded

- Real code analysis execution
- Result polling endpoint
- Database persistence
- Queue/worker orchestration
- Frontend application
- Production deployment workflow

## Why This Scope

Previous repository content mixed runnable code with non-runnable demos and roadmap material.  
This cleanup keeps only what can run and be verified today.
