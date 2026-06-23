"""Shared fixtures for Spendly tests.

Each test must get a fresh SQLite database under ``tmp_path`` so it never
touches the gitignored ``expense_tracker.db`` at the repo root.

We redirect ``database.db.DB_PATH`` before ``app`` is imported, and use a
private module attribute rather than mutating the constant on the package
(re-importing ``app`` would re-run ``init_db``/``seed_db`` at import time).
"""
import importlib
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Yield a fresh SQLite path inside tmp_path and point the app at it."""
    target = tmp_path / "expense_tracker.db"

    # Patch the module-level constant BEFORE app.py is (re-)imported.
    # ``database.db`` is already importable at this point because the
    # conftest itself lives under tests/ which triggers ``database/__init__.py``.
    import database.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", target)

    # Now (re-)import app so its top-level init_db()/seed_db() runs against
    # the redirected path. Drop any cached module first.
    sys.modules.pop("app", None)
    app_module = importlib.import_module("app")
    return target, app_module


@pytest.fixture
def client(db_path):
    """Flask test client wired to a freshly seeded in-tmp SQLite file."""
    _, app_module = db_path
    return app_module.app.test_client()


def login(client, email="demo@spendly.com", password="demo123"):
    """Log in via the real POST /login route and return the response."""
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
