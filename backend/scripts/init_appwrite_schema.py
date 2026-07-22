#!/usr/bin/env python
"""One-time, idempotent creation of the Appwrite database, tables, columns, indexes, and storage
bucket this backend needs when running in Appwrite mode. Safe to run again after a schema change;
every create call is wrapped to skip if the resource already exists.

Requires APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, and APPWRITE_API_KEY in dashboard/backend/.env.
The API key needs the scopes listed in docs/SETUP.md.

All access to these tables and the bucket goes through this backend using that API key, never
directly from the browser. Row-level security is enabled on every table so that the per-row
permissions app/stores/appwrite_store.py sets actually take effect, even though the primary
enforcement of who can see which row happens in application code, not in Appwrite's own permission
system, since this backend always authenticates with the administrator key.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from appwrite.client import Client  # noqa: E402
from appwrite.enums.tables_db_index_type import TablesDBIndexType  # noqa: E402
from appwrite.exception import AppwriteException  # noqa: E402
from appwrite.services.storage import Storage  # noqa: E402
from appwrite.services.tables_db import TablesDB  # noqa: E402

DATABASE_ID = "main"
BUCKET_ID = "cv-storage"


def get_client() -> Client:
    if not config.APPWRITE_API_KEY:
        sys.exit("error: APPWRITE_API_KEY is not set, see .env.example")
    client = Client()
    client.set_endpoint(config.APPWRITE_ENDPOINT)
    client.set_project(config.APPWRITE_PROJECT_ID)
    client.set_key(config.APPWRITE_API_KEY)
    return client


def _ignore_already_exists(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except AppwriteException as exc:
        if getattr(exc, "code", None) == 409 or "already exists" in str(exc).lower():
            return
        raise


def _wait_for_column(tables_db: TablesDB, table_id: str, key: str, attempts: int = 20):
    """Column creation is asynchronous on Appwrite's side; an index referencing a column fails
    while it is still processing. This polls briefly rather than guessing a fixed delay.

    list_columns is used instead of get_column: at least one column type in this SDK version
    fails to parse the single-column response into a model, while the list response parses fine.
    """
    for _ in range(attempts):
        columns = tables_db.list_columns(database_id=DATABASE_ID, table_id=table_id).columns
        match = next((c for c in columns if c.key == key), None)
        if match and getattr(match, "status", None) == "available":
            return
        time.sleep(1)


def create_applications_table(tables_db: TablesDB):
    _ignore_already_exists(
        tables_db.create_table, database_id=DATABASE_ID, table_id="applications", name="applications",
        row_security=True,
    )
    columns = [
        ("create_varchar_column", dict(key="user_id", size=64, required=True)),
        ("create_varchar_column", dict(key="company", size=256, required=True)),
        ("create_varchar_column", dict(key="role", size=256, required=False)),
        ("create_varchar_column", dict(key="source", size=128, required=False)),
        # job_url and notes are unsized mediumtext rather than varchar. A handful of large varchar
        # columns on one table reaches MariaDB's roughly 65KB maximum row size quickly.
        ("create_mediumtext_column", dict(key="job_url", required=False)),
        ("create_varchar_column", dict(key="cv_file_id", size=64, required=False)),
        ("create_varchar_column", dict(key="cover_letter_file_id", size=64, required=False)),
        ("create_datetime_column", dict(key="date_applied", required=False)),
        ("create_enum_column", dict(key="status", elements=[
            "Unknown", "Draft Ready", "Applied", "Screening", "Interview",
            "Final Round", "Offer", "Rejected", "Withdrawn",
        ], required=True)),
        ("create_datetime_column", dict(key="follow_up_date", required=False)),
        ("create_mediumtext_column", dict(key="notes", required=False)),
        ("create_integer_column", dict(key="salary_min", required=False)),
        ("create_integer_column", dict(key="salary_max", required=False)),
        ("create_varchar_column", dict(key="location", size=128, required=False)),
        ("create_varchar_column", dict(key="remote_type", size=64, required=False)),
    ]
    for method_name, kwargs in columns:
        _ignore_already_exists(getattr(tables_db, method_name), database_id=DATABASE_ID, table_id="applications", **kwargs)
    _wait_for_column(tables_db, "applications", "user_id")
    _wait_for_column(tables_db, "applications", "company")
    _wait_for_column(tables_db, "applications", "role")
    _ignore_already_exists(
        tables_db.create_index, database_id=DATABASE_ID, table_id="applications",
        key="user_id_index", type=TablesDBIndexType.KEY, columns=["user_id"],
    )
    _ignore_already_exists(
        tables_db.create_index, database_id=DATABASE_ID, table_id="applications",
        key="fulltext_company", type=TablesDBIndexType.FULLTEXT, columns=["company"],
    )
    _ignore_already_exists(
        tables_db.create_index, database_id=DATABASE_ID, table_id="applications",
        key="fulltext_role", type=TablesDBIndexType.FULLTEXT, columns=["role"],
    )


def create_cv_versions_table(tables_db: TablesDB):
    _ignore_already_exists(
        tables_db.create_table, database_id=DATABASE_ID, table_id="cv_versions", name="cv_versions",
        row_security=True,
    )
    columns = [
        ("create_varchar_column", dict(key="user_id", size=64, required=True)),
        ("create_varchar_column", dict(key="file_id", size=64, required=True)),
        ("create_varchar_column", dict(key="file_name", size=256, required=True)),
        ("create_varchar_column", dict(key="company", size=256, required=False)),
    ]
    for method_name, kwargs in columns:
        _ignore_already_exists(getattr(tables_db, method_name), database_id=DATABASE_ID, table_id="cv_versions", **kwargs)
    _wait_for_column(tables_db, "cv_versions", "user_id")
    _ignore_already_exists(
        tables_db.create_index, database_id=DATABASE_ID, table_id="cv_versions",
        key="user_id_index", type=TablesDBIndexType.KEY, columns=["user_id"],
    )


def create_settings_table(tables_db: TablesDB):
    _ignore_already_exists(
        tables_db.create_table, database_id=DATABASE_ID, table_id="settings", name="settings",
        row_security=True,
    )
    columns = [
        # required with no default: Appwrite does not allow a required column to also carry a
        # schema-level default, so app/stores/appwrite_store.py supplies the default values of
        # five and ten explicitly the first time a user's settings row is read.
        ("create_integer_column", dict(key="weekly_goal_low", required=True)),
        ("create_integer_column", dict(key="weekly_goal_high", required=True)),
    ]
    for method_name, kwargs in columns:
        _ignore_already_exists(getattr(tables_db, method_name), database_id=DATABASE_ID, table_id="settings", **kwargs)


def main():
    client = get_client()
    tables_db = TablesDB(client)
    storage = Storage(client)

    print("Creating database...")
    _ignore_already_exists(tables_db.create, database_id=DATABASE_ID, name="main")

    print("Creating applications table...")
    create_applications_table(tables_db)
    print("Creating cv_versions table...")
    create_cv_versions_table(tables_db)
    print("Creating settings table...")
    create_settings_table(tables_db)

    print("Creating cv-storage bucket...")
    _ignore_already_exists(
        storage.create_bucket,
        bucket_id=BUCKET_ID, name=BUCKET_ID, file_security=True,
        maximum_file_size=10 * 1024 * 1024,
        allowed_file_extensions=["pdf", "md", "docx"],
    )

    print("Done.")


if __name__ == "__main__":
    main()
