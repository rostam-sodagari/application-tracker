"""Unauthenticated by design: the frontend needs to know which backend mode is active before a
user has logged in at all, so it knows whether to show an Appwrite-flavoured or a local login and
registration form. Nothing here is sensitive; BACKEND_MODE is not a secret.
"""

from fastapi import APIRouter

from .. import config

router = APIRouter(prefix="/api/public-config", tags=["public-config"])


@router.get("")
def get_public_config():
    return {"backend_mode": config.BACKEND_MODE}
