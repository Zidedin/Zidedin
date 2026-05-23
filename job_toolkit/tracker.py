"""Local job application tracker using CSV storage."""

import csv
import os
from datetime import datetime

TRACKER_FILE = os.path.join(os.path.dirname(__file__), "..", "job_applications.csv")

FIELDS = [
    "id",
    "company",
    "position",
    "status",
    "priority",
    "applied_date",
    "source",
    "salary_range",
    "location",
    "remote",
    "job_url",
    "contact",
    "notes",
    "follow_up_date",
    "interview_date",
    "created_at",
    "updated_at",
]

VALID_STATUSES = [
    "To Apply",
    "Applied",
    "Interview Scheduled",
    "Technical Interview",
    "Offer",
    "Rejected",
    "Withdrawn",
]

VALID_PRIORITIES = ["High", "Medium", "Low"]
VALID_SOURCES = ["LinkedIn", "Indeed", "Glassdoor", "Referral", "Company Website", "Other"]
VALID_REMOTE = ["Remote", "Hybrid", "On-site"]


def _ensure_file():
    if not os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()


def _read_all():
    _ensure_file()
    with open(TRACKER_FILE, "r", newline="") as f:
        return list(csv.DictReader(f))


def _write_all(rows):
    with open(TRACKER_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _next_id(rows):
    if not rows:
        return 1
    return max(int(r["id"]) for r in rows) + 1


def add_application(
    company,
    position,
    status="To Apply",
    priority="Medium",
    source="LinkedIn",
    salary_range="",
    location="",
    remote="Remote",
    job_url="",
    contact="",
    notes="",
    follow_up_date="",
    interview_date="",
):
    rows = _read_all()
    now = datetime.now().isoformat(timespec="seconds")
    row = {
        "id": _next_id(rows),
        "company": company,
        "position": position,
        "status": status,
        "priority": priority,
        "applied_date": now[:10] if status == "Applied" else "",
        "source": source,
        "salary_range": salary_range,
        "location": location,
        "remote": remote,
        "job_url": job_url,
        "contact": contact,
        "notes": notes,
        "follow_up_date": follow_up_date,
        "interview_date": interview_date,
        "created_at": now,
        "updated_at": now,
    }
    rows.append(row)
    _write_all(rows)
    return row


def update_status(app_id, new_status):
    rows = _read_all()
    for r in rows:
        if int(r["id"]) == int(app_id):
            r["status"] = new_status
            r["updated_at"] = datetime.now().isoformat(timespec="seconds")
            if new_status == "Applied" and not r["applied_date"]:
                r["applied_date"] = datetime.now().strftime("%Y-%m-%d")
            _write_all(rows)
            return r
    return None


def update_application(app_id, **kwargs):
    rows = _read_all()
    for r in rows:
        if int(r["id"]) == int(app_id):
            for k, v in kwargs.items():
                if k in FIELDS and k not in ("id", "created_at"):
                    r[k] = v
            r["updated_at"] = datetime.now().isoformat(timespec="seconds")
            _write_all(rows)
            return r
    return None


def list_applications(status=None, priority=None):
    rows = _read_all()
    if status:
        rows = [r for r in rows if r["status"] == status]
    if priority:
        rows = [r for r in rows if r["priority"] == priority]
    return rows


def get_stats():
    rows = _read_all()
    stats = {"total": len(rows)}
    for s in VALID_STATUSES:
        stats[s] = sum(1 for r in rows if r["status"] == s)
    return stats


def delete_application(app_id):
    rows = _read_all()
    new_rows = [r for r in rows if int(r["id"]) != int(app_id)]
    if len(new_rows) == len(rows):
        return False
    _write_all(new_rows)
    return True
