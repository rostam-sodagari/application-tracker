import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_ROOT = BACKEND_ROOT.parent
FRONTEND_DIST = DASHBOARD_ROOT / "frontend" / "dist"

load_dotenv(BACKEND_ROOT / ".env")

# --- backend mode -------------------------------------------------------------
# Chooses which storage and authentication implementation app/db.py and app/auth.py dispatch to.
# "local" needs no external account and is the default for a fresh install. "appwrite" uses an
# Appwrite Cloud project for both login and data.
BACKEND_MODE = os.environ.get("BACKEND_MODE", "local").strip().lower()
if BACKEND_MODE not in ("local", "appwrite"):
    raise ValueError(f"BACKEND_MODE must be 'local' or 'appwrite', got {BACKEND_MODE!r}")

# --- local mode ----------------------------------------------------------------
LOCAL_DB_PATH = BACKEND_ROOT / "data" / "app.db"
LOCAL_CV_STORAGE_DIR = BACKEND_ROOT / "data" / "cv_storage"
# Signs local-mode session tokens. Must be set to a real secret before using local mode for
# anything but a quick try; without it, restarting the process invalidates every session.
LOCAL_SESSION_SECRET = os.environ.get("LOCAL_SESSION_SECRET")

# The origin the frontend is served from, used to build the link inside the verification email.
# Defaults to a typical local run; set this to the real origin in any other deployment.
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000").rstrip("/")

# Outgoing mail for local-mode email verification. Entirely optional: if SMTP_HOST is left unset,
# newly registered accounts are marked verified immediately instead of being sent a link, since a
# self-hosted install with no mail server configured has no way to ever complete one. Setting
# SMTP_HOST turns verification back on and requires an actual link to be followed.
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").strip().lower() != "false"
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", SMTP_USERNAME or "no-reply@localhost")

# --- appwrite mode ---------------------------------------------------------------
# Used both for login verification (app/auth.py) and for all application data (app/db.py). None
# of the three is meaningful outside Appwrite mode.
APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
# A genuine secret, unlike the two values above. Used only server-side for all application data
# access (TablesDB + Storage). Login verification itself needs no API key; see auth.py.
APPWRITE_API_KEY = os.environ.get("APPWRITE_API_KEY")
