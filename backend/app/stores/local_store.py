"""Local storage backend: a single SQLite file plus CV files on local disk. No external account
of any kind is needed to use this backend.

Every row that belongs to a user (applications, cv_versions, settings) carries a user_id column,
and every function that reads, updates, or deletes a specific row confirms it belongs to the
calling user before doing so, returning None (translated to a 404 by the router) rather than
revealing that a row belonging to someone else exists.
"""

import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .. import constants
from ..config import LOCAL_CV_STORAGE_DIR, LOCAL_DB_PATH

APPLICATION_STATUSES = constants.APPLICATION_STATUSES
APPLICATION_EDITABLE_FIELDS = constants.APPLICATION_EDITABLE_FIELDS

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email_verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    company TEXT NOT NULL,
    role TEXT,
    source TEXT,
    job_url TEXT,
    cv_file_id TEXT,
    cover_letter_file_id TEXT,
    date_applied TEXT,
    status TEXT NOT NULL DEFAULT 'Draft Ready',
    follow_up_date TEXT,
    notes TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    location TEXT,
    remote_type TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);

CREATE TABLE IF NOT EXISTS cv_versions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    file_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    company TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cv_versions_user ON cv_versions(user_id);

CREATE TABLE IF NOT EXISTS settings (
    user_id TEXT PRIMARY KEY,
    weekly_goal_low INTEGER NOT NULL,
    weekly_goal_high INTEGER NOT NULL
);
"""


def _new_id() -> str:
    return secrets.token_hex(12)


@contextmanager
def get_conn():
    LOCAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # Added after the users table already existed in earlier installs; CREATE TABLE IF NOT
        # EXISTS above does not retrofit a new column onto a table that is already there.
        existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
        if "email_verified" not in existing_columns:
            conn.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0")


# --- users --------------------------------------------------------------------

def create_user(email: str, password_hash: str, email_verified: bool = False) -> str:
    user_id = _new_id()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (id, email, password_hash, email_verified) VALUES (?, ?, ?, ?)",
            (user_id, email.strip().lower(), password_hash, int(email_verified)),
        )
    return user_id


def get_user_by_email(email: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def mark_user_verified(user_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (user_id,))


# --- applications -------------------------------------------------------------------

def add_application(
    user_id, company, role=None, source=None, job_url=None, cv_file_id=None,
    cover_letter_file_id=None, date_applied=None, status="Draft Ready", notes=None,
    salary_min=None, salary_max=None, location=None, remote_type=None,
):
    app_id = _new_id()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO applications (
                id, user_id, company, role, source, job_url, cv_file_id, cover_letter_file_id,
                date_applied, status, notes, salary_min, salary_max, location, remote_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (app_id, user_id, company, role, source, job_url, cv_file_id, cover_letter_file_id,
             date_applied, status, notes, salary_min, salary_max, location, remote_type),
        )
    return app_id


def get_application(user_id, app_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ? AND user_id = ?", (app_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def list_applications(user_id, status=None):
    query = "SELECT * FROM applications WHERE user_id = ?"
    params = [user_id]
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(query, params).fetchall()]


def search_applications(user_id, status=None, keyword=None, limit=20, offset=0):
    query = "SELECT * FROM applications WHERE user_id = ?"
    count_query = "SELECT COUNT(*) FROM applications WHERE user_id = ?"
    params = [user_id]
    if status:
        query += " AND status = ?"
        count_query += " AND status = ?"
        params.append(status)
    if keyword:
        query += " AND (company LIKE ? OR role LIKE ?)"
        count_query += " AND (company LIKE ? OR role LIKE ?)"
        like = f"%{keyword}%"
        params.extend([like, like])
    with get_conn() as conn:
        total = conn.execute(count_query, params).fetchone()[0]
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        rows = conn.execute(query, [*params, limit, offset]).fetchall()
    return {"items": [dict(r) for r in rows], "total": total}


def update_application(user_id, app_id, **fields):
    if not fields:
        return
    unknown = set(fields) - APPLICATION_EDITABLE_FIELDS
    if unknown:
        raise ValueError(f"cannot update fields: {unknown}")
    if "status" in fields and fields["status"] not in APPLICATION_STATUSES:
        raise ValueError(f"invalid application status: {fields['status']}")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    with get_conn() as conn:
        conn.execute(
            f"UPDATE applications SET {set_clause}, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
            (*fields.values(), app_id, user_id),
        )


def delete_application(user_id, app_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM applications WHERE id = ? AND user_id = ?", (app_id, user_id))


# --- cv_versions + local cv storage -------------------------------------------------------------------

def add_cv_version(user_id, file_id, file_name, company=None):
    cv_id = _new_id()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cv_versions (id, user_id, file_id, file_name, company) VALUES (?, ?, ?, ?, ?)",
            (cv_id, user_id, file_id, file_name, company),
        )
    return cv_id


def get_cv_version(user_id, cv_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM cv_versions WHERE id = ? AND user_id = ?", (cv_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def list_cv_versions(user_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM cv_versions WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def update_cv_version(user_id, cv_id, company=None):
    with get_conn() as conn:
        conn.execute(
            "UPDATE cv_versions SET company = ? WHERE id = ? AND user_id = ?", (company, cv_id, user_id)
        )


def delete_cv_version(user_id, cv_id):
    cv = get_cv_version(user_id, cv_id)
    if cv:
        path = LOCAL_CV_STORAGE_DIR / user_id / cv["file_id"]
        if path.is_file():
            path.unlink()
    with get_conn() as conn:
        conn.execute("DELETE FROM cv_versions WHERE id = ? AND user_id = ?", (cv_id, user_id))


def upload_cv_file(user_id: str, filename: str, content: bytes) -> str:
    """Writes bytes under a per-user subdirectory, returns the bare filename as the file_id."""
    user_dir = LOCAL_CV_STORAGE_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in filename if c.isalnum() or c in " ._-") or "upload"
    file_id = f"{_new_id()}-{safe_name}"
    (user_dir / file_id).write_bytes(content)
    return file_id


def download_cv_file(user_id: str, file_id: str) -> bytes:
    user_dir = (LOCAL_CV_STORAGE_DIR / user_id).resolve()
    resolved = (user_dir / file_id).resolve()
    if user_dir not in resolved.parents or not resolved.is_file():
        raise FileNotFoundError(file_id)
    return resolved.read_bytes()


# --- settings -------------------------------------------------------------------

_DEFAULT_WEEKLY_GOAL_LOW = 5
_DEFAULT_WEEKLY_GOAL_HIGH = 10


def get_settings(user_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM settings WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return dict(row)
        conn.execute(
            "INSERT INTO settings (user_id, weekly_goal_low, weekly_goal_high) VALUES (?, ?, ?)",
            (user_id, _DEFAULT_WEEKLY_GOAL_LOW, _DEFAULT_WEEKLY_GOAL_HIGH),
        )
        return {
            "user_id": user_id,
            "weekly_goal_low": _DEFAULT_WEEKLY_GOAL_LOW,
            "weekly_goal_high": _DEFAULT_WEEKLY_GOAL_HIGH,
        }


def update_settings(user_id, weekly_goal_low=None, weekly_goal_high=None):
    get_settings(user_id)  # ensure the row exists first
    fields = {}
    if weekly_goal_low is not None:
        fields["weekly_goal_low"] = weekly_goal_low
    if weekly_goal_high is not None:
        fields["weekly_goal_high"] = weekly_goal_high
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    with get_conn() as conn:
        conn.execute(f"UPDATE settings SET {set_clause} WHERE user_id = ?", (*fields.values(), user_id))
