"""Shared business rules that do not belong to either storage backend specifically."""

APPLICATION_STATUSES = (
    "Unknown",
    "Draft Ready",
    "Applied",
    "Screening",
    "Interview",
    "Final Round",
    "Offer",
    "Rejected",
    "Withdrawn",
)

APPLICATION_EDITABLE_FIELDS = {
    "company", "role", "source", "job_url", "cv_file_id", "cover_letter_file_id",
    "date_applied", "status", "follow_up_date", "notes",
    "salary_min", "salary_max", "location", "remote_type",
}

# Statuses beyond these two count as "actually sent" for the home page's rate statistics.
APPLICATION_SENT_STATUSES = tuple(s for s in APPLICATION_STATUSES if s not in ("Unknown", "Draft Ready"))
APPLICATION_RESPONSE_STATUSES = ("Screening", "Interview", "Final Round", "Offer", "Rejected")
APPLICATION_INTERVIEW_STATUSES = ("Interview", "Final Round", "Offer")
