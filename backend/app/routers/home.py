from datetime import date, timedelta

from fastapi import APIRouter, Depends

from .. import db
from ..auth import require_auth
from ..constants import APPLICATION_INTERVIEW_STATUSES, APPLICATION_RESPONSE_STATUSES, APPLICATION_SENT_STATUSES

router = APIRouter(prefix="/api/home", tags=["home"])


def _rate(count: int, total: int) -> float | None:
    return round(count / total, 4) if total else None


@router.get("")
def get_home_stats(user_id: str = Depends(require_auth)):
    applications = db.list_applications(user_id)
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    applied_this_week = [
        a for a in applications
        if a["status"] != "Draft Ready" and a["date_applied"] and a["date_applied"] >= week_ago
    ]
    funnel = {status: 0 for status in db.APPLICATION_STATUSES}
    for a in applications:
        funnel[a["status"]] = funnel.get(a["status"], 0) + 1
    today = date.today().isoformat()
    due_follow_ups = [a for a in applications if a["follow_up_date"] and a["follow_up_date"] <= today]

    total_applications = len(applications)
    total_applied = sum(funnel[s] for s in APPLICATION_SENT_STATUSES)
    responded = sum(funnel[s] for s in APPLICATION_RESPONSE_STATUSES)
    interviewed = sum(funnel[s] for s in APPLICATION_INTERVIEW_STATUSES)
    offered = funnel.get("Offer", 0)

    settings = db.get_settings(user_id)

    return {
        "applied_this_week": len(applied_this_week),
        "weekly_goal_low": settings["weekly_goal_low"],
        "weekly_goal_high": settings["weekly_goal_high"],
        "funnel": funnel,
        "due_follow_ups": due_follow_ups,
        "total_applications": total_applications,
        "total_applied": total_applied,
        "response_rate": _rate(responded, total_applied),
        "interview_rate": _rate(interviewed, total_applied),
        "offer_rate": _rate(offered, total_applied),
    }
