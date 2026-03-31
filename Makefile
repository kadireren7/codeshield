PYTHON ?= python

.PHONY: run test lint format

run:
	$(PYTHON) -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m black --check .

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m black .
