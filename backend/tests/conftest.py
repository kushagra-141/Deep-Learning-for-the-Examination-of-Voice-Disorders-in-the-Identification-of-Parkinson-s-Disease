"""Shared test fixtures.

Sets up a file-based SQLite test database, creates the schema from the ORM
metadata at session start (using a sync engine — async engine pools complicate
multi-loop teardown), and yields a `TestClient` that runs the FastAPI lifespan
to load the ModelManager.
"""
from __future__ import annotations

import os
import pathlib
import tempfile
from collections.abc import Iterator

# Configure environment BEFORE any `app.*` imports so Settings picks it up.
_TEST_DB_PATH = pathlib.Path(tempfile.gettempdir()) / "parkinsons_test.db"
if _TEST_DB_PATH.exists():
    _TEST_DB_PATH.unlink()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH.as_posix()}"
os.environ.setdefault("ENV", "test")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402

from app.db.base import Base  # noqa: E402
import app.db.models  # noqa: E402, F401 — register all ORM models
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_database() -> Iterator[None]:
    sync_url = f"sqlite:///{_TEST_DB_PATH.as_posix()}"
    engine = create_engine(sync_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    engine.dispose()
    yield


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
