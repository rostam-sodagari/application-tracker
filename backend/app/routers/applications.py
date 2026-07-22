from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import db
from ..auth import require_auth

router = APIRouter(prefix="/api/applications", tags=["applications"])

PAGE_SIZE = 20


class ApplicationCreate(BaseModel):
    company: str
    role: str | None = None
    source: str | None = None
    job_url: str | None = None
    cv_file_id: str | None = None
    cover_letter_file_id: str | None = None
    date_applied: str | None = None
    status: str = "Draft Ready"
    follow_up_date: str | None = None
    notes: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    location: str | None = None
    remote_type: str | None = None


class ApplicationUpdate(BaseModel):
    company: str | None = None
    role: str | None = None
    source: str | None = None
    job_url: str | None = None
    cv_file_id: str | None = None
    cover_letter_file_id: str | None = None
    date_applied: str | None = None
    status: str | None = None
    follow_up_date: str | None = None
    notes: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    location: str | None = None
    remote_type: str | None = None


@router.get("")
def get_applications(
    status: str | None = None,
    keyword: str | None = None,
    page: int = 0,
    user_id: str = Depends(require_auth),
):
    return db.search_applications(user_id, status=status, keyword=keyword, limit=PAGE_SIZE, offset=page * PAGE_SIZE)


@router.post("", status_code=201)
def create_application(payload: ApplicationCreate, user_id: str = Depends(require_auth)):
    follow_up_date = payload.follow_up_date
    fields = payload.model_dump(exclude={"follow_up_date"})
    app_id = db.add_application(user_id, **fields)
    if follow_up_date:
        db.update_application(user_id, app_id, follow_up_date=follow_up_date)
    return _get_or_404(user_id, app_id)


@router.patch("/{app_id}")
def update_application(app_id: str, payload: ApplicationUpdate, user_id: str = Depends(require_auth)):
    _get_or_404(user_id, app_id)
    fields = payload.model_dump(exclude_unset=True)
    try:
        db.update_application(user_id, app_id, **fields)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _get_or_404(user_id, app_id)


@router.delete("/{app_id}", status_code=204)
def delete_application(app_id: str, user_id: str = Depends(require_auth)):
    _get_or_404(user_id, app_id)
    db.delete_application(user_id, app_id)


def _get_or_404(user_id: str, app_id: str):
    row = db.get_application(user_id, app_id)
    if row is None:
        raise HTTPException(status_code=404, detail="application not found")
    return row
