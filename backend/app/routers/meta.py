from fastapi import APIRouter

from .. import db

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("")
def get_meta():
    return {"application_statuses": db.APPLICATION_STATUSES}
