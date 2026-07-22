"""Per-request authentication via Appwrite. Account registration, password storage and hashing,
and login rate limiting are all Appwrite's responsibility, not this backend's. The frontend
registers and logs in directly against Appwrite and attaches a short-lived Appwrite token
(`Authorization: Bearer <token>`) to every request; this module's only job is confirming that
token still belongs to a real, currently valid Appwrite session, and returning the account's id so
the storage layer can scope data to it.

No API key is needed here. Scoping the Appwrite client to the caller's own token and asking for
its account is enough: if that call succeeds, the token is valid and belongs to that account; if
Appwrite rejects it (expired, tampered, or the session was revoked), it raises and this returns a
401.

Each token is valid for 15 minutes, Appwrite's fixed expiry, and the frontend refreshes it before
that, so failures here almost always mean the caller is genuinely not logged in, not that the token
is about to expire.

A short in-memory cache avoids asking Appwrite again for every single API call a page fires in
quick succession. This does not extend how long a revoked or expired token is accepted, since the
cache entry's lifetime is far shorter than the token's own.
"""

import time

from appwrite.client import Client
from appwrite.exception import AppwriteException
from appwrite.services.account import Account
from fastapi import Header, HTTPException

from .. import config

_CACHE_TTL_SECONDS = 30
_verified_cache: dict[str, tuple[float, str]] = {}


def _verify_with_appwrite(token: str) -> str:
    client = (
        Client()
        .set_endpoint(config.APPWRITE_ENDPOINT)
        .set_project(config.APPWRITE_PROJECT_ID)
        .set_jwt(token)
    )
    return Account(client).get().id


def require_auth(authorization: str | None = Header(default=None)) -> str:
    """FastAPI dependency returning the calling account's id."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="missing bearer token")

    cached = _verified_cache.get(token)
    if cached and time.time() - cached[0] < _CACHE_TTL_SECONDS:
        return cached[1]

    try:
        user_id = _verify_with_appwrite(token)
    except AppwriteException as exc:
        raise HTTPException(status_code=401, detail=f"session invalid or expired: {exc}")

    _verified_cache[token] = (time.time(), user_id)
    if len(_verified_cache) > 1000:
        oldest = sorted(_verified_cache.items(), key=lambda kv: kv[1][0])[:500]
        for stale_token, _ in oldest:
            _verified_cache.pop(stale_token, None)
    return user_id
