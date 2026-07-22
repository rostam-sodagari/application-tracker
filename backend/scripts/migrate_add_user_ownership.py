#!/usr/bin/env python
"""One-time: tags every existing applications and cv_versions row, created before multi-user
support existed, with the given account's user id, so that account continues to see everything
it created.

Usage:
    python scripts/migrate_add_user_ownership.py <ACCOUNT_USER_ID>

Find <ACCOUNT_USER_ID> in the Appwrite console under Auth, then Users, then the account itself;
its User ID is shown there. Safe to run again; rows that already have a user_id are left alone.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from appwrite.client import Client  # noqa: E402
from appwrite.permission import Permission  # noqa: E402
from appwrite.query import Query  # noqa: E402
from appwrite.role import Role  # noqa: E402
from appwrite.services.tables_db import TablesDB  # noqa: E402

DATABASE_ID = "main"


def get_tables_db() -> TablesDB:
    client = Client()
    client.set_endpoint(config.APPWRITE_ENDPOINT)
    client.set_project(config.APPWRITE_PROJECT_ID)
    client.set_key(config.APPWRITE_API_KEY)
    return TablesDB(client)


def owner_permissions(user_id: str) -> list[str]:
    return [
        Permission.read(Role.user(user_id)),
        Permission.update(Role.user(user_id)),
        Permission.delete(Role.user(user_id)),
    ]


def backfill_table(tables_db: TablesDB, table_id: str, user_id: str) -> int:
    rows = tables_db.list_rows(database_id=DATABASE_ID, table_id=table_id, queries=[Query.limit(500)]).rows
    updated = 0
    for row in rows:
        if row.data.get("user_id"):
            continue
        tables_db.update_row(
            database_id=DATABASE_ID, table_id=table_id, row_id=row.id,
            data={"user_id": user_id}, permissions=owner_permissions(user_id),
        )
        updated += 1
    return updated


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/migrate_add_user_ownership.py <ACCOUNT_USER_ID>")
    user_id = sys.argv[1]
    tables_db = get_tables_db()
    for table_id in ("applications", "cv_versions"):
        count = backfill_table(tables_db, table_id, user_id)
        print(f"{table_id}: tagged {count} row(s) with user_id {user_id}")


if __name__ == "__main__":
    main()
