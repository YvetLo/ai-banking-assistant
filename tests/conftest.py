"""
Shared pytest fixtures — Sprint 8.

BANKING_DB_PATH must be set BEFORE `backend.src.database` (and therefore
`backend.main`) is first imported, since DB_PATH is resolved once at
import time. That's why the env var is set at module load here, above
the `from backend.main import app` import — conftest.py is always
loaded before any test module in the same directory, so this guarantees
tests never touch the real demo data/banking.db.
"""

import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).parent / "test.db"
os.environ["BANKING_DB_PATH"] = str(TEST_DB_PATH)

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_db():
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="session")
def client():
    # `with` triggers the real FastAPI startup event once for the whole
    # session: init_db() against test.db, RAG retrievers loaded, agent
    # graph built — same code path as production, just pointed at test.db.
    with TestClient(app) as c:
        yield c
