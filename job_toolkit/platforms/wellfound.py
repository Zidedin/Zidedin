"""
Wellfound (formerly AngelList Talent) job application automation.

Great for startup Data Engineer roles.

USAGE:
    1. Start Chrome: google-chrome --remote-debugging-port=9222
    2. Log into Wellfound manually
    3. Run:
       python -m job_toolkit.platforms.wellfound \\
           --role "Data Engineer" --max-applications 5
"""

import argparse
import sys
import urllib.parse

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

from .base import BasePlatformAutomation


class WellfoundAutomation(BasePlatformAutomation):
    name = "Wellfound"
    base_url = "https://wellfound.com"

    def _build_search_url(self, role="data-engineer", remote=True):
        url = f"{self.base_url}/role/{role}"
        if remote:
            url += "?remote=true"
        return url

    def run(self, role="data-engineer", remote=True, max_applications=5, dry_run=False):
        max_applications = min(max_applications, self.config["max_applications"])

        self.log(f"Starting Wellfound automation")
        self.log(f"  Role: {role}")
        self.log(f"  Remote: {remote}")
        self.log(f"  Max applications: {max_applications}")
        self.log(f"  Dry run: {dry_run}")
        print()

        with sync_playwright() as p:
            browser = self.connect_browser(p)
            if not browser:
                return

            context = browser.contexts[0]
            page = context.new_page()

            search_url = self._build_search_url(role, remote)
            self.log(f"Searching: {search_url}")
            page.goto(search_url, wait_until="domcontentloaded")
            self.human_delay(3, 5)

            if "login" in page.url or "sign" in page.url:
                self.log("ERROR: Not logged in. Log into Wellfound first.")
                page.close()
                return

            job_cards = page.query_selector_all(
                "[data-test='StartupResult'], "
                ".styles_component__startup, "
                "[class*='StartupResult'], "
                ".browse-table-row"
            )

            self.log(f"Found {len(job_cards)} companies with openings.\n")

            for i, card in enumerate(job_cards):
                if self.applied_count >= max_applications:
                    self.log(f"Reached max applications ({max_applications}).")
                    break

                try:
                    company_el = card.query_selector(
                        "h2, [class*='companyName'], "
                        "[data-test='StartupName'], "
                        "a[class*='company']"
                    )
                    company = company_el.inner_text().strip() if company_el else f"Company #{i+1}"

                    job_listings = card.query_selector_all(
                        "[data-test='JobListing'], "
                        "[class*='JobListing'], "
                        ".job-listing"
                    )

                    if not job_listings:
                        card.click()
                        self.human_delay(1, 2)
                        job_listings = card.query_selector_all(
                            "[data-test='JobListing'], "
                            "[class*='JobListing'], "
                            ".job-listing"
                        )

                    for listing in job_listings:
                        if self.applied_count >= max_applications:
                            break

                        title_el = listing.query_selector(
                            "[data-test='JobListingName'], "
                            "[class*='jobTitle'], "
                            "a, span"
                        )
                        title = title_el.inner_text().strip() if title_el else "Unknown Role"

                        self.log(f"[{i+1}] {title} @ {company}")

                        if self.should_skip_title(title):
                            self.log(f"  Skipping (filtered).")
                            self.skipped_count += 1
                            continue

                        apply_btn = listing.query_selector(
                            "button:has-text('Apply'), "
                            "a:has-text('Apply'), "
                            "[data-test='ApplyButton']"
                        )

                        if not apply_btn:
                            self.log(f"  No apply button. Skipping.")
                            self.skipped_count += 1
                            continue

                        if dry_run:
                            self.log(f"  [DRY RUN] Would apply: {title} @ {company}")
                            self.applied_count += 1
                            continue

                        apply_btn.click()
                        self.human_delay(2, 4)

                        modal = page.query_selector(
                            "[role='dialog'], "
                            ".modal, "
                            "[class*='Modal']"
                        )

                        if modal:
                            note_field = modal.query_selector("textarea")
                            if note_field and note_field.is_visible():
                                from ..cover_letter import generate_email_body
                                msg = generate_email_body(company=company, position=title)
                                note_field.fill(msg)
                                self.human_delay(1, 2)

                            submit = modal.query_selector(
                                "button:has-text('Apply'), "
                                "button:has-text('Submit'), "
                                "button[type='submit']"
                            )
                            if submit:
                                submit.click()
                                self.human_delay(2, 4)
                                self.log(f"  Applied!")
                                self.applied_count += 1
                                self.save_application(company, title, page.url)
                            else:
                                self.log(f"  No submit in modal. Skipping.")
                                self.skipped_count += 1
                                close = modal.query_selector("button[aria-label='Close'], button:has-text('Cancel')")
                                if close:
                                    close.click()
                        else:
                            self.log(f"  Modal didn't open. Skipping.")
                            self.skipped_count += 1

                except PlaywrightTimeout:
                    self.log(f"  Timeout. Skipping.")
                    self.skipped_count += 1
                except Exception as e:
                    self.log(f"  Error: {e}")
                    self.skipped_count += 1
                    self.errors.append(str(e))

                self.human_delay()

            page.close()

        self.print_summary()


def main():
    parser = argparse.ArgumentParser(description="Wellfound job application automation")
    parser.add_argument("--role", default="data-engineer",
                        help="Role slug (data-engineer, backend-engineer, etc.)")
    parser.add_argument("--no-remote", action="store_true")
    parser.add_argument("--max-applications", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-delay", type=float, default=3)
    parser.add_argument("--max-delay", type=float, default=7)
    args = parser.parse_args()

    bot = WellfoundAutomation(config={
        "min_delay": args.min_delay,
        "max_delay": args.max_delay,
        "max_applications": args.max_applications,
    })

    print("=" * 60)
    print("  Wellfound Job Application Automation")
    print("=" * 60)
    print()

    if not args.dry_run:
        resp = input("Continue? (yes/no): ").strip().lower()
        if resp != "yes":
            print("Aborted.")
            return

    bot.run(
        role=args.role,
        remote=not args.no_remote,
        max_applications=args.max_applications,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
