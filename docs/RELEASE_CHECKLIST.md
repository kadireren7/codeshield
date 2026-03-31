# Release Checklist

## Repository

- [ ] Repository name is final and consistent *(GitHub setting)*
- [ ] Repository description is short, clear, and honest *(GitHub setting)*
- [x] Only one product name is used across all files
- [x] No unnecessary or misleading files remain

## Documentation

- [x] README matches the actual implementation
- [x] README includes a working example request
- [x] README includes a real example response
- [x] Limitations are clearly documented
- [x] Roadmap is realistic
- [x] MVP scope is documented

## Backend

- [x] `backend.main:app` starts correctly
- [x] `GET /healthz` works
- [x] `GET /api/v1/meta` works
- [x] `POST /api/v1/analyze` works
- [x] Validation errors return structured responses
- [x] No broken imports remain

## Quality

- [x] Tests pass locally
- [x] `python -m compileall backend tests` passes
- [x] Linting/formatting config exists
- [x] No fake or placeholder tests remain

## Security

- [x] `.env.example` contains no unsafe default secrets
- [x] Raw submitted code is not logged by default
- [x] README warns users not to submit private code
- [x] Experimental / non-production-safe status is clearly stated

## Open Source Readiness

- [x] LICENSE is included
- [x] CONTRIBUTING.md is included
- [x] Issue templates are included
- [x] `.gitignore` is present and correct

## Final Manual Check

- [x] Repo is understandable within 15 seconds
- [x] A developer can run it by following the README
- [x] No fake claims remain
- [x] The repo feels small, honest, and intentional

## Release Decision

- [x] I would be comfortable sharing this publicly today

## Remaining Manual Steps

1. Set final GitHub repository name.
2. Set GitHub About/description text.
