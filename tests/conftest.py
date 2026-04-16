import os

import pytest


@pytest.fixture(autouse=True)
def _codeshield_db_path(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "codeshield_test.db"
    monkeypatch.setenv("CODESHIELD_DB_PATH", str(db_path))
