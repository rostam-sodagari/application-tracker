"""Dispatches to whichever authentication backend BACKEND_MODE selects. Both providers expose a
require_auth FastAPI dependency with the same signature, returning the calling user's id, so
nothing that depends on it needs to know which backend is active.
"""

from . import config

if config.BACKEND_MODE == "appwrite":
    from .auth_providers.appwrite_auth import require_auth
else:
    from .auth_providers.local_auth import require_auth

__all__ = ["require_auth"]
