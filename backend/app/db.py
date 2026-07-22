"""Dispatches to whichever storage backend BACKEND_MODE selects. Both implementations expose the
same function names, taking the calling user's id as their first argument, so nothing that calls
this module needs to know which backend is active.
"""

from . import config
from .constants import APPLICATION_EDITABLE_FIELDS, APPLICATION_STATUSES

if config.BACKEND_MODE == "appwrite":
    from .stores.appwrite_store import (  # noqa: F401
        add_application,
        add_cv_version,
        delete_application,
        delete_cv_version,
        download_cv_file,
        get_application,
        get_cv_version,
        get_settings,
        init_db,
        list_applications,
        list_cv_versions,
        search_applications,
        update_application,
        update_cv_version,
        update_settings,
        upload_cv_file,
    )
else:
    from .stores.local_store import (  # noqa: F401
        add_application,
        add_cv_version,
        delete_application,
        delete_cv_version,
        download_cv_file,
        get_application,
        get_cv_version,
        get_settings,
        init_db,
        list_applications,
        list_cv_versions,
        search_applications,
        update_application,
        update_cv_version,
        update_settings,
        upload_cv_file,
    )

__all__ = [
    "APPLICATION_STATUSES",
    "APPLICATION_EDITABLE_FIELDS",
    "add_application",
    "add_cv_version",
    "delete_application",
    "delete_cv_version",
    "download_cv_file",
    "get_application",
    "get_cv_version",
    "get_settings",
    "init_db",
    "list_applications",
    "list_cv_versions",
    "search_applications",
    "update_application",
    "update_cv_version",
    "update_settings",
    "upload_cv_file",
]
