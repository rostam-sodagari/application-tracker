"""Appwrite storage backend: TablesDB for applications, cv_versions, and settings, and Storage for
CV files. All access uses an administrator-scoped API key that never reaches the browser.

Every row carries a user_id column. Listing and searching filter by it; creating a row sets it and
also sets Appwrite row permissions scoped to that user as a second layer of protection; reading,
updating, or deleting a specific row confirms the row's user_id matches the caller first, returning
None (translated to a 404 by the router) rather than revealing that a row belonging to someone
else exists. Because this module always authenticates to Appwrite with the administrator API key,
Appwrite's own permission check is not the primary enforcement boundary here, the ownership check
in this module is; the Appwrite-side permissions are kept as defense in depth in case a future
change ever lets the browser reach Appwrite's data services directly.
"""

from appwrite.client import Client
from appwrite.exception import AppwriteException
from appwrite.id import ID
from appwrite.input_file import InputFile
from appwrite.permission import Permission
from appwrite.query import Query
from appwrite.role import Role
from appwrite.services.storage import Storage
from appwrite.services.tables_db import TablesDB

from .. import constants
from ..config import APPWRITE_API_KEY, APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID

APPLICATION_STATUSES = constants.APPLICATION_STATUSES
APPLICATION_EDITABLE_FIELDS = constants.APPLICATION_EDITABLE_FIELDS

DATABASE_ID = "main"
BUCKET_ID = "cv-storage"

_DEFAULT_WEEKLY_GOAL_LOW = 5
_DEFAULT_WEEKLY_GOAL_HIGH = 10


def _client() -> Client:
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    client.set_key(APPWRITE_API_KEY)
    return client


def _tables_db() -> TablesDB:
    return TablesDB(_client())


def _storage() -> Storage:
    return Storage(_client())


def _owner_permissions(user_id: str) -> list[str]:
    return [
        Permission.read(Role.user(user_id)),
        Permission.update(Role.user(user_id)),
        Permission.delete(Role.user(user_id)),
    ]


def init_db():
    """Schema creation is handled once by scripts/init_appwrite_schema.py, not here. Kept so
    call sites written against the shared db.py interface do not need to change."""


def _row_to_application(row) -> dict:
    d = row.data
    return {
        "id": row.id,
        "company": d.get("company"),
        "role": d.get("role"),
        "source": d.get("source"),
        "job_url": d.get("job_url"),
        "cv_file_id": d.get("cv_file_id"),
        "cover_letter_file_id": d.get("cover_letter_file_id"),
        "date_applied": d.get("date_applied"),
        "status": d.get("status"),
        "follow_up_date": d.get("follow_up_date"),
        "notes": d.get("notes"),
        "salary_min": d.get("salary_min"),
        "salary_max": d.get("salary_max"),
        "location": d.get("location"),
        "remote_type": d.get("remote_type"),
        "created_at": row.createdat,
        "updated_at": row.updatedat,
    }


def _row_to_cv_version(row) -> dict:
    d = row.data
    return {
        "id": row.id,
        "file_id": d.get("file_id"),
        "file_name": d.get("file_name"),
        "company": d.get("company"),
        "created_at": row.createdat,
    }


def _get_owned_row(user_id, table_id, row_id):
    """Returns the raw Appwrite row only if it exists and belongs to user_id, else None."""
    try:
        row = _tables_db().get_row(database_id=DATABASE_ID, table_id=table_id, row_id=row_id)
    except AppwriteException as exc:
        if getattr(exc, "code", None) == 404:
            return None
        raise
    if row.data.get("user_id") != user_id:
        return None
    return row


# --- applications -------------------------------------------------------------------

def add_application(
    user_id, company, role=None, source=None, job_url=None, cv_file_id=None,
    cover_letter_file_id=None, date_applied=None, status="Draft Ready", notes=None,
    salary_min=None, salary_max=None, location=None, remote_type=None,
):
    row = _tables_db().create_row(
        database_id=DATABASE_ID,
        table_id="applications",
        row_id=ID.unique(),
        data={
            "user_id": user_id, "company": company, "role": role, "source": source, "job_url": job_url,
            "cv_file_id": cv_file_id, "cover_letter_file_id": cover_letter_file_id,
            "date_applied": date_applied, "status": status, "notes": notes,
            "salary_min": salary_min, "salary_max": salary_max, "location": location,
            "remote_type": remote_type,
        },
        permissions=_owner_permissions(user_id),
    )
    return row.id


def get_application(user_id, app_id):
    row = _get_owned_row(user_id, "applications", app_id)
    return _row_to_application(row) if row else None


def list_applications(user_id, status=None):
    queries = [Query.equal("user_id", user_id), Query.order_desc("$createdAt")]
    if status:
        queries.append(Query.equal("status", status))
    rows = _tables_db().list_rows(database_id=DATABASE_ID, table_id="applications", queries=queries).rows
    return [_row_to_application(r) for r in rows]


def search_applications(user_id, status=None, keyword=None, limit=20, offset=0):
    queries = [Query.equal("user_id", user_id), Query.order_desc("$createdAt"), Query.limit(limit), Query.offset(offset)]
    if status:
        queries.append(Query.equal("status", status))
    if keyword:
        queries.append(Query.or_queries([Query.search("company", keyword), Query.search("role", keyword)]))
    result = _tables_db().list_rows(database_id=DATABASE_ID, table_id="applications", queries=queries)
    return {"items": [_row_to_application(r) for r in result.rows], "total": result.total}


def update_application(user_id, app_id, **fields):
    if not fields:
        return
    unknown = set(fields) - APPLICATION_EDITABLE_FIELDS
    if unknown:
        raise ValueError(f"cannot update fields: {unknown}")
    if "status" in fields and fields["status"] not in APPLICATION_STATUSES:
        raise ValueError(f"invalid application status: {fields['status']}")
    if not _get_owned_row(user_id, "applications", app_id):
        return
    _tables_db().update_row(database_id=DATABASE_ID, table_id="applications", row_id=app_id, data=fields)


def delete_application(user_id, app_id):
    if not _get_owned_row(user_id, "applications", app_id):
        return
    _tables_db().delete_row(database_id=DATABASE_ID, table_id="applications", row_id=app_id)


# --- cv_versions + cv-storage bucket -------------------------------------------------------------------

def add_cv_version(user_id, file_id, file_name, company=None):
    row = _tables_db().create_row(
        database_id=DATABASE_ID,
        table_id="cv_versions",
        row_id=ID.unique(),
        data={"user_id": user_id, "file_id": file_id, "file_name": file_name, "company": company},
        permissions=_owner_permissions(user_id),
    )
    return row.id


def get_cv_version(user_id, cv_id):
    row = _get_owned_row(user_id, "cv_versions", cv_id)
    return _row_to_cv_version(row) if row else None


def list_cv_versions(user_id):
    queries = [Query.equal("user_id", user_id), Query.order_desc("$createdAt")]
    rows = _tables_db().list_rows(database_id=DATABASE_ID, table_id="cv_versions", queries=queries).rows
    return [_row_to_cv_version(r) for r in rows]


def update_cv_version(user_id, cv_id, company=None):
    if not _get_owned_row(user_id, "cv_versions", cv_id):
        return
    _tables_db().update_row(database_id=DATABASE_ID, table_id="cv_versions", row_id=cv_id, data={"company": company})


def delete_cv_version(user_id, cv_id):
    row = _get_owned_row(user_id, "cv_versions", cv_id)
    if not row:
        return
    file_id = row.data.get("file_id")
    if file_id:
        try:
            _storage().delete_file(bucket_id=BUCKET_ID, file_id=file_id)
        except AppwriteException as exc:
            if getattr(exc, "code", None) != 404:
                raise
    _tables_db().delete_row(database_id=DATABASE_ID, table_id="cv_versions", row_id=cv_id)


def upload_cv_file(user_id: str, filename: str, content: bytes) -> str:
    """Uploads bytes to the cv-storage bucket, returns the new Storage file_id."""
    uploaded = _storage().create_file(
        bucket_id=BUCKET_ID, file_id=ID.unique(), file=InputFile.from_bytes(content, filename),
        permissions=_owner_permissions(user_id),
    )
    return uploaded.id


def download_cv_file(user_id: str, file_id: str) -> bytes:
    # user_id is accepted for signature parity with the local backend, where it selects the
    # per-user directory a file lives under. The router already confirms ownership via
    # get_cv_version before calling this, and Appwrite Storage is addressed by file_id alone.
    return _storage().get_file_view(bucket_id=BUCKET_ID, file_id=file_id)


# --- settings -------------------------------------------------------------------
# The settings row's own id is the user's id, so no query is needed to find it.

def get_settings(user_id):
    try:
        row = _tables_db().get_row(database_id=DATABASE_ID, table_id="settings", row_id=user_id)
        return {
            "user_id": user_id,
            "weekly_goal_low": row.data.get("weekly_goal_low", _DEFAULT_WEEKLY_GOAL_LOW),
            "weekly_goal_high": row.data.get("weekly_goal_high", _DEFAULT_WEEKLY_GOAL_HIGH),
        }
    except AppwriteException as exc:
        if getattr(exc, "code", None) != 404:
            raise
    _tables_db().create_row(
        database_id=DATABASE_ID,
        table_id="settings",
        row_id=user_id,
        data={"weekly_goal_low": _DEFAULT_WEEKLY_GOAL_LOW, "weekly_goal_high": _DEFAULT_WEEKLY_GOAL_HIGH},
        permissions=_owner_permissions(user_id),
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
    _tables_db().update_row(database_id=DATABASE_ID, table_id="settings", row_id=user_id, data=fields)
