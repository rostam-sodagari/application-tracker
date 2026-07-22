from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .. import db
from ..auth import require_auth

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    weekly_goal_low: int | None = None
    weekly_goal_high: int | None = None


@router.get("")
def get_settings(user_id: str = Depends(require_auth)):
    return db.get_settings(user_id)


@router.patch("")
def update_settings(payload: SettingsUpdate, user_id: str = Depends(require_auth)):
    db.update_settings(user_id, weekly_goal_low=payload.weekly_goal_low, weekly_goal_high=payload.weekly_goal_high)
    return db.get_settings(user_id)
