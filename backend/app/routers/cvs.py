import mimetypes
import re

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from .. import db
from ..auth import require_auth

router = APIRouter(tags=["cvs"])

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9 ._-]")


class CvUpdate(BaseModel):
    company: str | None = None


@router.get("/api/cvs")
def get_cvs(user_id: str = Depends(require_auth)):
    return db.list_cv_versions(user_id)


@router.post("/api/cvs", status_code=201)
async def upload_cv(
    file: UploadFile = File(...), company: str | None = Form(None), user_id: str = Depends(require_auth)
):
    safe_name = SAFE_FILENAME_RE.sub("_", file.filename or "upload")
    contents = await file.read()
    file_id = db.upload_cv_file(user_id, safe_name, contents)
    cv_id = db.add_cv_version(user_id, file_id, safe_name, company=company)
    return db.get_cv_version(user_id, cv_id)


@router.patch("/api/cvs/{cv_id}")
def update_cv(cv_id: str, payload: CvUpdate, user_id: str = Depends(require_auth)):
    if db.get_cv_version(user_id, cv_id) is None:
        raise HTTPException(status_code=404, detail="cv not found")
    db.update_cv_version(user_id, cv_id, company=payload.company)
    return db.get_cv_version(user_id, cv_id)


@router.delete("/api/cvs/{cv_id}", status_code=204)
def delete_cv(cv_id: str, user_id: str = Depends(require_auth)):
    if db.get_cv_version(user_id, cv_id) is None:
        raise HTTPException(status_code=404, detail="cv not found")
    db.delete_cv_version(user_id, cv_id)


@router.get("/cvs/open/{file_id}")
def open_cv(file_id: str, user_id: str = Depends(require_auth)):
    cv = next((c for c in db.list_cv_versions(user_id) if c["file_id"] == file_id), None)
    if cv is None:
        raise HTTPException(status_code=404, detail="file not found")
    content = db.download_cv_file(user_id, file_id)
    content_type, _ = mimetypes.guess_type(cv["file_name"])
    return Response(
        content=content,
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{cv["file_name"]}"'},
    )
