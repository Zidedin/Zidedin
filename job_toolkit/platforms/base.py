"""Base class for platform automation."""

import csv
import os
import random
import time
from datetime import datetime


TRACKER_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "job_applications.csv")

FIELDS = [
    "id", "company", "position", "status", "priority", "applied_date",
    "source", "salary_range", "location", "remote", "job_url", "contact",
    "notes", "follow_up_date", "interview_date", "created_at", "updated_at",
]


class BasePlatformAutomation:
    name = "base"
    base_url = ""

    def __init__(self, config=None):
        self.config = config or {}
        self.config.setdefault("min_delay", 2)
        self.config.setdefault("max_delay", 6)
        self.config.setdefault("max_applications", 10)
        self.applied_count = 0
        self.skipped_count = 0
        self.errors = []

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] [{self.name}] {msg}")

    def human_delay(self, lo=None, hi=None):
        lo = lo or self.config["min_delay"]
        hi = hi or self.config["max_delay"]
        time.sleep(random.uniform(lo, hi))

    def save_application(self, company, position, url, location="", salary="", remote=""):
        file_exists = os.path.exists(TRACKER_FILE)
        existing_ids = []
        if file_exists:
            with open(TRACKER_FILE, "r") as f:
                existing_ids = [int(r["id"]) for r in csv.DictReader(f)]

        next_id = max(existing_ids) + 1 if existing_ids else 1
        now = datetime.now().isoformat(timespec="seconds")

        with open(TRACKER_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "id": next_id,
                "company": company,
                "position": position,
                "status": "Applied",
                "priority": "Medium",
                "applied_date": now[:10],
                "source": self.name,
                "salary_range": salary,
                "location": location,
                "remote": remote,
                "job_url": url,
                "contact": "",
                "notes": f"Auto-applied via {self.name} automation",
                "follow_up_date": "",
                "interview_date": "",
                "created_at": now,
                "updated_at": now,
            })

    def print_summary(self):
        print()
        self.log(f"Session complete!")
        self.log(f"  Applied: {self.applied_count}")
        self.log(f"  Skipped: {self.skipped_count}")
        self.log(f"  Errors:  {len(self.errors)}")
        if self.errors:
            for e in self.errors[:5]:
                self.log(f"    - {e}")

    def should_skip_title(self, title):
        title_lower = title.lower()
        excluded = self.config.get("excluded_keywords", ["intern", "internship", "pasante", "practica"])
        for kw in excluded:
            if kw.lower() in title_lower:
                return True
        required = self.config.get("required_keywords", [])
        if required and not any(kw.lower() in title_lower for kw in required):
            return True
        return False

    def connect_browser(self, playwright):
        try:
            browser = playwright.chromium.connect_over_cdp("http://localhost:9222")
            self.log("Connected to Chrome.")
            return browser
        except Exception:
            self.log("ERROR: Could not connect to Chrome.")
            self.log("Start Chrome with: google-chrome --remote-debugging-port=9222")
            return None

    def run(self, **kwargs):
        raise NotImplementedError
