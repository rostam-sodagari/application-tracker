#!/usr/bin/env python
"""Fills the local database with realistic sample applications, a few CV versions, and a custom
weekly goal, so the interface has something to look at without entering data by hand. Only makes
sense in local mode; there is nothing here that touches Appwrite.

Usage:
    python scripts/seed_sample_data.py [email]

If no email is given and exactly one account exists in the local database, that account is used.
Safe to run more than once; it always adds new rows rather than checking for existing ones, so
running it twice against the same account doubles up the sample data.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402
from app.stores import local_store  # noqa: E402


def _date_days_ago(days: int | None) -> str | None:
    if days is None:
        return None
    return (date.today() - timedelta(days=days)).isoformat()


def _follow_up_date(days_from_today: int | None) -> str | None:
    if days_from_today is None:
        return None
    return (date.today() + timedelta(days=days_from_today)).isoformat()


SAMPLE_APPLICATIONS = [
    dict(company="Acme Corp", role="Backend Engineer", source="LinkedIn",
         job_url="https://acme.example.com/careers/backend-engineer",
         status="Interview", days_ago=3, salary_min=55000, salary_max=70000,
         location="London", remote_type="Hybrid",
         notes="Second-round technical interview went well, waiting on take-home feedback.",
         follow_up_in_days=2),
    dict(company="Globex Corporation", role="Senior Python Developer", source="Referral",
         job_url="https://globex.example.com/jobs/1245",
         status="Applied", days_ago=6, salary_min=60000, salary_max=75000,
         location="Manchester", remote_type="Remote",
         notes="Applied through a former colleague's referral.", follow_up_in_days=None),
    dict(company="Initech", role="Full Stack Engineer", source="Company site",
         job_url="https://initech.example.com/careers/fullstack",
         status="Screening", days_ago=10, salary_min=50000, salary_max=65000,
         location="Leeds", remote_type="Onsite",
         notes="Recruiter screening call scheduled.", follow_up_in_days=1),
    dict(company="Umbrella Corp", role="DevOps Engineer", source="Indeed",
         job_url="https://umbrella.example.com/jobs/devops",
         status="Final Round", days_ago=14, salary_min=65000, salary_max=85000,
         location="Bristol", remote_type="Hybrid",
         notes="Final round with the hiring manager and two team leads.", follow_up_in_days=5),
    dict(company="Stark Industries", role="Machine Learning Engineer", source="LinkedIn",
         job_url="https://stark.example.com/careers/ml-engineer",
         status="Offer", days_ago=20, salary_min=80000, salary_max=100000,
         location="London", remote_type="Hybrid",
         notes="Offer received, negotiating start date.", follow_up_in_days=None),
    dict(company="Wayne Enterprises", role="Data Engineer", source="Company site",
         job_url="https://wayne.example.com/jobs/data-engineer",
         status="Rejected", days_ago=25, salary_min=58000, salary_max=72000,
         location="Remote", remote_type="Remote",
         notes="Rejected after the technical screen.", follow_up_in_days=None),
    dict(company="Hooli", role="Site Reliability Engineer", source="Referral",
         job_url="https://hooli.example.com/careers/sre",
         status="Withdrawn", days_ago=28, salary_min=62000, salary_max=78000,
         location="Cambridge", remote_type="Onsite",
         notes="Withdrew after accepting a different offer.", follow_up_in_days=None),
    dict(company="Pied Piper", role="Backend Developer", source="AngelList",
         job_url="https://piedpiper.example.com/jobs/backend",
         status="Draft Ready", days_ago=None, salary_min=45000, salary_max=60000,
         location="Remote", remote_type="Remote",
         notes="CV tailored, ready to submit this week.", follow_up_in_days=None),
    dict(company="Massive Dynamic", role="Platform Engineer", source="LinkedIn",
         job_url="https://massivedynamic.example.com/careers/platform",
         status="Applied", days_ago=1, salary_min=70000, salary_max=90000,
         location="London", remote_type="Hybrid",
         notes="Applied yesterday, no response yet.", follow_up_in_days=None),
    dict(company="Soylent Corp", role="Software Engineer", source="Company site",
         job_url="https://soylent.example.com/jobs/swe",
         status="Unknown", days_ago=None, salary_min=None, salary_max=None,
         location=None, remote_type=None,
         notes="Saw the posting, not sure whether to apply yet.", follow_up_in_days=None),
    dict(company="Wonka Industries", role="Product Engineer", source="Indeed",
         job_url="https://wonka.example.com/careers/product-engineer",
         status="Applied", days_ago=4, salary_min=52000, salary_max=68000,
         location="Birmingham", remote_type="Hybrid",
         notes="Applied via Indeed easy apply.", follow_up_in_days=None),
    dict(company="Cyberdyne Systems", role="Backend Engineer", source="Referral",
         job_url="https://cyberdyne.example.com/jobs/backend-eng",
         status="Screening", days_ago=8, salary_min=60000, salary_max=80000,
         location="Remote", remote_type="Remote",
         notes="Recruiter reached out directly, phone screen booked.", follow_up_in_days=0),
]

# (file_name, company_tag, content, attach_to_company)
SAMPLE_CVS = [
    ("resume-general.pdf", None, b"%PDF-1.4 Sample CV content - general purpose resume.\n", None),
    (
        "resume-stark-industries.pdf", "Stark Industries",
        b"%PDF-1.4 Sample CV content - tailored for Stark Industries.\n", "Stark Industries",
    ),
    (
        "cover-letter-acme.pdf", "Acme Corp",
        b"%PDF-1.4 Sample cover letter content - written for Acme Corp.\n", "Acme Corp",
    ),
]


def _resolve_user_id(email: str | None) -> str:
    with local_store.get_conn() as conn:
        rows = conn.execute("SELECT id, email FROM users").fetchall()

    if not rows:
        sys.exit("no accounts exist yet - register one through the app first")

    if email:
        match = next((r for r in rows if r["email"] == email.strip().lower()), None)
        if not match:
            sys.exit(f"no account found for {email!r}")
        return match["id"]

    if len(rows) > 1:
        emails = ", ".join(r["email"] for r in rows)
        sys.exit(f"more than one account exists ({emails}) - specify which one: seed_sample_data.py <email>")

    return rows[0]["id"]


def main():
    email = sys.argv[1] if len(sys.argv) > 1 else None
    user_id = _resolve_user_id(email)

    file_ids_by_company = {}
    for file_name, tag, content, _ in SAMPLE_CVS:
        file_id = db.upload_cv_file(user_id, file_name, content)
        db.add_cv_version(user_id, file_id, file_name, company=tag)
        # tag is None for the general-purpose resume; that is a real, distinct dict key here,
        # not "no entry", so every file's id must be recorded regardless of its tag's truthiness.
        file_ids_by_company[tag] = file_id
    print(f"added {len(SAMPLE_CVS)} CV version(s)")

    # Only a few applications get a file attached, matching how someone would actually use this:
    # a tailored CV for a company that mattered enough to track it, not every single one.
    general_cv_companies = {"Globex Corporation", "Massive Dynamic", "Wonka Industries"}

    for entry in SAMPLE_APPLICATIONS:
        company = entry["company"]
        if company == "Acme Corp":
            # The Acme-tagged file is a cover letter, not a CV; the CV attached here is the
            # general one instead.
            cv_file_id = file_ids_by_company.get(None)
        else:
            cv_file_id = file_ids_by_company.get(company)
            if cv_file_id is None and company in general_cv_companies:
                cv_file_id = file_ids_by_company.get(None)

        app_id = db.add_application(
            user_id,
            company=company,
            role=entry["role"],
            source=entry["source"],
            job_url=entry["job_url"],
            date_applied=_date_days_ago(entry["days_ago"]),
            status=entry["status"],
            notes=entry["notes"],
            salary_min=entry["salary_min"],
            salary_max=entry["salary_max"],
            location=entry["location"],
            remote_type=entry["remote_type"],
            cv_file_id=cv_file_id,
            cover_letter_file_id=file_ids_by_company.get(company) if company == "Acme Corp" else None,
        )
        follow_up = _follow_up_date(entry["follow_up_in_days"])
        if follow_up:
            db.update_application(user_id, app_id, follow_up_date=follow_up)
    print(f"added {len(SAMPLE_APPLICATIONS)} application(s)")

    db.update_settings(user_id, weekly_goal_low=5, weekly_goal_high=8)
    print("set weekly goal to 5-8")


if __name__ == "__main__":
    main()
