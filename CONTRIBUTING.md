# Contributing

Thanks for considering a contribution.

## Scope

This repository is intentionally small. Please keep pull requests aligned with MVP scope:

- FastAPI request intake
- Validation and API contract quality
- Tests and docs clarity
- Tooling quality (lint/test/dev ergonomics)

Out of scope for now:

- Fake demos or mock "analysis results"
- Large architecture rewrites
- Enterprise-only features

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Before opening a PR

```bash
make lint
make test
```

## PR expectations

- Keep changes small and focused.
- Update tests for behavior changes.
- Update README/docs for contract changes.
