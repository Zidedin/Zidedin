#!/usr/bin/env python3
"""
LinkedIn job application automation using Playwright.

WARNING: Automating LinkedIn violates their Terms of Service.
         Your account may be suspended or permanently banned.
         Use at your own risk and with conservative settings.

REQUIREMENTS:
    pip install playwright
    playwright install chromium

USAGE:
    This script connects to YOUR local Chrome browser session.
    You must start Chrome with remote debugging enabled:

    # macOS:
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --remote-debugging-port=9222

    # Linux:
    google-chrome --remote-debugging-port=9222

    # Windows:
    chrome.exe --remote-debugging-port=9222

    Then log into LinkedIn manually in that browser window.
    After that, run this script:

    python -m job_toolkit.browser_automation \
        --keywords "Data Engineer" \
        --location "Remote" \
        --max-applications 5
"""

import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


TRACKER_FILE = os.path.join(os.path.dirname(__file__), "..", "job_applications.csv")

DEFAULT_CONFIG = {
    "min_delay_seconds": 3,
    "max_delay_seconds": 8,
    "max_applications_per_session": 10,
    "easy_apply_only": True,
    "skip_if_questions": True,
    "excluded_companies": [],
    "required_keywords_in_title": [],
    "excluded_keywords_in_title": ["intern", "internship", "junior"],
}


def _human_delay(min_s=None, max_s=None, config=None):
    config = config or DEFAULT_CONFIG
    lo = min_s or config["min_delay_seconds"]
    hi = max_s or config["max_delay_seconds"]
    time.sleep(random.uniform(lo, hi))


def _log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def _save_application(company, position, url):
    """Append applied job to the CSV tracker."""
    fields = [
        "id", "company", "position", "status", "priority", "applied_date",
        "source", "salary_range", "location", "remote", "job_url", "contact",
        "notes", "follow_up_date", "interview_date", "created_at", "updated_at",
    ]
    file_exists = os.path.exists(TRACKER_FILE)
    existing_ids = []
    if file_exists:
        with open(TRACKER_FILE, "r") as f:
            reader = csv.DictReader(f)
            existing_ids = [int(r["id"]) for r in reader]

    next_id = max(existing_ids) + 1 if existing_ids else 1
    now = datetime.now().isoformat(timespec="seconds")

    with open(TRACKER_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "id": next_id,
            "company": company,
            "position": position,
            "status": "Applied",
            "priority": "Medium",
            "applied_date": now[:10],
            "source": "LinkedIn",
            "salary_range": "",
            "location": "",
            "remote": "",
            "job_url": url,
            "contact": "",
            "notes": "Auto-applied via browser automation",
            "follow_up_date": "",
            "interview_date": "",
            "created_at": now,
            "updated_at": now,
        })


def _should_skip_job(title, company, config):
    title_lower = title.lower()
    for excluded in config.get("excluded_keywords_in_title", []):
        if excluded.lower() in title_lower:
            _log(f"  Skipping (excluded keyword '{excluded}'): {title}")
            return True
    required = config.get("required_keywords_in_title", [])
    if required and not any(kw.lower() in title_lower for kw in required):
        _log(f"  Skipping (missing required keyword): {title}")
        return True
    if company in config.get("excluded_companies", []):
        _log(f"  Skipping (excluded company): {company}")
        return True
    return False


def run_easy_apply(
    keywords="Data Engineer",
    location="Remote",
    max_applications=5,
    config=None,
    dry_run=False,
):
    config = {**DEFAULT_CONFIG, **(config or {})}
    max_applications = min(max_applications, config["max_applications_per_session"])

    _log(f"Starting LinkedIn Easy Apply automation")
    _log(f"  Keywords: {keywords}")
    _log(f"  Location: {location}")
    _log(f"  Max applications: {max_applications}")
    _log(f"  Dry run: {dry_run}")
    print()

    applied_count = 0
    skipped_count = 0

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception:
            _log("ERROR: Could not connect to Chrome.")
            _log("Make sure Chrome is running with: --remote-debugging-port=9222")
            _log("And that you are logged into LinkedIn in that browser.")
            return

        context = browser.contexts[0]
        page = context.new_page()

        search_url = (
            "https://www.linkedin.com/jobs/search/?"
            f"keywords={keywords.replace(' ', '%20')}"
            f"&location={location.replace(' ', '%20')}"
            "&f_AL=true"  # Easy Apply filter
            "&f_WT=2"     # Remote filter
            "&sortBy=DD"  # Most recent
        )

        _log(f"Navigating to LinkedIn Jobs...")
        page.goto(search_url, wait_until="domcontentloaded")
        _human_delay(3, 5, config)

        if "login" in page.url or "authwall" in page.url:
            _log("ERROR: Not logged in. Please log into LinkedIn in the Chrome window first.")
            page.close()
            return

        _log("Logged in. Scanning job listings...\n")
        _human_delay(2, 4, config)

        job_cards = page.query_selector_all(".job-card-container, .jobs-search-results__list-item")
        _log(f"Found {len(job_cards)} job cards on this page.\n")

        for i, card in enumerate(job_cards):
            if applied_count >= max_applications:
                _log(f"\nReached max applications ({max_applications}). Stopping.")
                break

            try:
                card.scroll_into_view_if_needed()
                _human_delay(1, 2, config)
                card.click()
                _human_delay(2, 4, config)

                title_el = page.query_selector(".job-details-jobs-unified-top-card__job-title, .jobs-unified-top-card__job-title")
                company_el = page.query_selector(".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name")

                title = title_el.inner_text().strip() if title_el else f"Job #{i+1}"
                company = company_el.inner_text().strip() if company_el else "Unknown"

                _log(f"[{i+1}/{len(job_cards)}] {title} @ {company}")

                if _should_skip_job(title, company, config):
                    skipped_count += 1
                    continue

                easy_apply_btn = page.query_selector(
                    "button.jobs-apply-button, "
                    "button[aria-label*='Easy Apply'], "
                    "button:has-text('Easy Apply')"
                )

                if not easy_apply_btn:
                    _log(f"  No Easy Apply button found. Skipping.")
                    skipped_count += 1
                    continue

                if dry_run:
                    _log(f"  [DRY RUN] Would apply to: {title} @ {company}")
                    applied_count += 1
                    continue

                easy_apply_btn.click()
                _human_delay(2, 4, config)

                modal = page.query_selector(
                    ".jobs-easy-apply-modal, "
                    "[role='dialog'][aria-label*='apply'], "
                    ".artdeco-modal"
                )

                if not modal:
                    _log(f"  Application modal didn't open. Skipping.")
                    skipped_count += 1
                    continue

                max_steps = 5
                for step in range(max_steps):
                    if config["skip_if_questions"]:
                        additional_questions = modal.query_selector_all(
                            "input:not([type='hidden']):not([type='submit']):not([aria-label*='Phone']):not([aria-label*='phone']),"
                            "select,"
                            "textarea"
                        )
                        visible_questions = [q for q in additional_questions if q.is_visible()]
                        if len(visible_questions) > 2:
                            _log(f"  Has {len(visible_questions)} additional questions. Skipping.")
                            dismiss = modal.query_selector(
                                "button[aria-label='Dismiss'], "
                                "button:has-text('Discard'), "
                                "button[aria-label='Close']"
                            )
                            if dismiss:
                                dismiss.click()
                                _human_delay(1, 2, config)
                                confirm_discard = page.query_selector("button:has-text('Discard')")
                                if confirm_discard:
                                    confirm_discard.click()
                                    _human_delay(1, 2, config)
                            skipped_count += 1
                            break

                    submit_btn = modal.query_selector(
                        "button:has-text('Submit application'), "
                        "button[aria-label='Submit application']"
                    )

                    if submit_btn and submit_btn.is_visible():
                        submit_btn.click()
                        _human_delay(2, 4, config)
                        _log(f"  ✅ Applied successfully!")
                        applied_count += 1
                        _save_application(company, title, page.url)

                        close_btn = page.query_selector(
                            "button[aria-label='Dismiss'], "
                            "button:has-text('Done')"
                        )
                        if close_btn:
                            close_btn.click()
                            _human_delay(1, 2, config)
                        break

                    next_btn = modal.query_selector(
                        "button:has-text('Next'), "
                        "button:has-text('Continue'), "
                        "button:has-text('Review'), "
                        "button[aria-label='Continue to next step']"
                    )

                    if next_btn and next_btn.is_visible():
                        next_btn.click()
                        _human_delay(2, 3, config)
                    else:
                        _log(f"  Could not find next/submit button at step {step+1}. Skipping.")
                        dismiss = modal.query_selector("button[aria-label='Dismiss'], button:has-text('Discard')")
                        if dismiss:
                            dismiss.click()
                            _human_delay(1, 2, config)
                            confirm = page.query_selector("button:has-text('Discard')")
                            if confirm:
                                confirm.click()
                        skipped_count += 1
                        break

            except PlaywrightTimeout:
                _log(f"  Timeout on job #{i+1}. Moving on.")
                skipped_count += 1
            except Exception as e:
                _log(f"  Error on job #{i+1}: {e}")
                skipped_count += 1

            _human_delay(config=config)

        page.close()

    print()
    _log(f"Session complete!")
    _log(f"  Applied: {applied_count}")
    _log(f"  Skipped: {skipped_count}")
    _log(f"  Applications saved to: {os.path.abspath(TRACKER_FILE)}")


def main():
    parser = argparse.ArgumentParser(
        description="LinkedIn Easy Apply automation (run on YOUR machine)",
        epilog="WARNING: This violates LinkedIn ToS. Your account may be banned.",
    )
    parser.add_argument("--keywords", default="Data Engineer", help="Job search keywords")
    parser.add_argument("--location", default="Remote", help="Location filter")
    parser.add_argument("--max-applications", type=int, default=5, help="Max applications per session (max 10)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without actually applying")
    parser.add_argument("--include-questions", action="store_true", help="Don't skip jobs with additional questions")
    parser.add_argument("--min-delay", type=float, default=3, help="Min delay between actions (seconds)")
    parser.add_argument("--max-delay", type=float, default=8, help="Max delay between actions (seconds)")
    parser.add_argument("--exclude-companies", nargs="*", default=[], help="Companies to skip")
    parser.add_argument("--require-title-keyword", nargs="*", default=[], help="Required keywords in job title")
    parser.add_argument("--config-file", help="Path to JSON config file")

    args = parser.parse_args()

    config = dict(DEFAULT_CONFIG)
    if args.config_file:
        with open(args.config_file) as f:
            config.update(json.load(f))

    config["min_delay_seconds"] = args.min_delay
    config["max_delay_seconds"] = args.max_delay
    config["skip_if_questions"] = not args.include_questions
    if args.exclude_companies:
        config["excluded_companies"] = args.exclude_companies
    if args.require_title_keyword:
        config["required_keywords_in_title"] = args.require_title_keyword

    print("=" * 60)
    print("  LinkedIn Easy Apply Automation")
    print("  ⚠️  This violates LinkedIn Terms of Service")
    print("  ⚠️  Your account may be suspended or banned")
    print("=" * 60)
    print()

    if not args.dry_run:
        response = input("Continue? (yes/no): ").strip().lower()
        if response != "yes":
            print("Aborted.")
            return

    run_easy_apply(
        keywords=args.keywords,
        location=args.location,
        max_applications=args.max_applications,
        config=config,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
