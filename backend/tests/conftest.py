"""Shared pytest fixtures for the backend test suite. Every test runs against local mode, since
it needs no external account or network access; app/stores/appwrite_store.py is covered by the
network-free unit tests in test_appwrite_store_unit.py instead of a live Appwrite project.
"""

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Set before any app module is imported. config.py's load_dotenv() does not override an
# already-set environment variable, so this keeps a real developer's backend/.env out of the
# test run entirely, even if one exists on this machine.
os.environ.setdefault("BACKEND_MODE", "local")
os.environ.setdefault("LOCAL_SESSION_SECRET", "test-only-secret-do-not-use-in-production")

_session_tmp_dir = Path(tempfile.mkdtemp(prefix="apptracker_test_session_"))

from app import config  # noqa: E402

# Redirected before app.stores.local_store is ever imported (its `from ..config import
# LOCAL_DB_PATH` binds this value once, at import time), so importing the application under test
# never touches a real developer's database or CV storage directory.
config.LOCAL_DB_PATH = _session_tmp_dir / "session.db"
config.LOCAL_CV_STORAGE_DIR = _session_tmp_dir / "cv_storage"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.auth_providers import local_auth  # noqa: E402
from app.main import app  # noqa: E402
from app.stores import local_store  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A TestClient backed by a fresh, empty local-mode database, isolated to this test."""
    monkeypatch.setattr(local_store, "LOCAL_DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(local_store, "LOCAL_CV_STORAGE_DIR", tmp_path / "cv_storage")
    local_store.init_db()
    local_auth._login_attempts.clear()
    return TestClient(app)


@pytest.fixture
def register_user(client):
    """Registers an account against the test client and returns (auth_headers, email)."""

    def _register(email: str = "user@example.com", password: str = "password123"):
        resp = client.post("/api/auth/register", json={"email": email, "password": password})
        assert resp.status_code == 200, resp.text
        token = resp.json()["token"]
        return {"Authorization": f"Bearer {token}"}, email

    return _register
