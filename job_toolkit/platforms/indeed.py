"""
Indeed job application automation.

Indeed has "Easy Apply" / "Apply on Indeed" similar to LinkedIn.

USAGE:
    1. Start Chrome: google-chrome --remote-debugging-port=9222
    2. Log into Indeed manually
    3. Run:
       python -m job_toolkit.platforms.indeed \\
           --keywords "Data Engineer" --location "Remote" --max-applications 5
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


class IndeedAutomation(BasePlatformAutomation):
    name = "Indeed"
    base_url = "https://www.indeed.com"

    def _build_search_url(self, keywords="Data Engineer", location="Remote",
                          job_type="", age="14", remote_only=False):
        params = {
            "q": keywords,
            "l": location,
            "fromage": age,
            "sort": "date",
        }
        if remote_only:
            params["remotejob"] = "032b3046-06a3-4876-8dfd-474eb5e7ed11"
        type_map = {"fulltime": "fulltime", "parttime": "parttime", "contract": "contract"}
        if job_type in type_map:
            params["jt"] = type_map[job_type]
        return f"{self.base_url}/jobs?" + urllib.parse.urlencode(params)

    def run(self, keywords="Data Engineer", location="Remote", remote_only=True,
            job_type="", age="14", max_applications=5, dry_run=False):
        max_applications = min(max_applications, self.config["max_applications"])

        self.log(f"Starting Indeed automation")
        self.log(f"  Keywords: {keywords}")
        self.log(f"  Location: {location}")
        self.log(f"  Max applications: {max_applications}")
        self.log(f"  Dry run: {dry_run}")
        print()

        with sync_playwright() as p:
            browser = self.connect_browser(p)
            if not browser:
                return

            context = browser.contexts[0]
            page = context.new_page()

            search_url = self._build_search_url(keywords, location, job_type, age, remote_only)
            self.log(f"Searching: {search_url}")
            page.goto(search_url, wait_until="domcontentloaded")
            self.human_delay(3, 5)

            job_cards = page.query_selector_all(
                ".job_seen_beacon, "
                ".jobsearch-ResultsList > li, "
                "div[data-jk], "
                ".result"
            )

            self.log(f"Found {len(job_cards)} job cards.\n")

            for i, card in enumerate(job_cards):
                if self.applied_count >= max_applications:
                    self.log(f"Reached max applications ({max_applications}).")
                    break

                try:
                    title_el = card.query_selector("h2 a, .jobTitle a, a[data-jk]")
                    company_el = card.query_selector("[data-testid='company-name'], .company, .companyName")
                    location_el = card.query_selector("[data-testid='text-location'], .companyLocation, .location")

                    title = title_el.inner_text().strip() if title_el else f"Job #{i+1}"
                    company = company_el.inner_text().strip() if company_el else "Unknown"
                    loc = location_el.inner_text().strip() if location_el else ""

                    self.log(f"[{i+1}/{len(job_cards)}] {title} @ {company} ({loc})")

                    if self.should_skip_title(title):
                        self.log(f"  Skipping (filtered).")
                        self.skipped_count += 1
                        continue

                    easily_apply = card.query_selector(
                        ".iaLabel, "
                        ":has-text('Easily apply'), "
                        ":has-text('Solicitar'), "
                        "[class*='easy']"
                    )

                    if not easily_apply:
                        self.log(f"  Not 'Easily Apply'. Skipping.")
                        self.skipped_count += 1
                        continue

                    if title_el:
                        title_el.click()
                    else:
                        card.click()
                    self.human_delay(2, 4)

                    job_url = page.url

                    apply_btn = page.query_selector(
                        "button:has-text('Apply now'), "
                        "button:has-text('Solicitar ahora'), "
                        "a:has-text('Apply now'), "
                        "#indeedApplyButton, "
                        "[id*='applyButton']"
                    )

                    if not apply_btn:
                        self.log(f"  No apply button in detail pane. Skipping.")
                        self.skipped_count += 1
                        continue

                    if dry_run:
                        self.log(f"  [DRY RUN] Would apply: {title} @ {company}")
                        self.applied_count += 1
                        continue

                    apply_btn.click()
                    self.human_delay(3, 5)

                    pages_with_questions = 0
                    max_steps = 6

                    for step in range(max_steps):
                        continue_btn = page.query_selector(
                            "button:has-text('Continue'), "
                            "button:has-text('Continuar'), "
                            "button[data-testid='continue-button']"
                        )
                        submit_btn = page.query_selector(
                            "button:has-text('Submit'), "
                            "button:has-text('Enviar'), "
                            "button[data-testid='submit-button']"
                        )
                        review_btn = page.query_selector(
                            "button:has-text('Review'), "
                            "button:has-text('Revisar')"
                        )

                        if submit_btn and submit_btn.is_visible():
                            submit_btn.click()
                            self.human_delay(2, 4)
                            self.log(f"  Applied!")
                            self.applied_count += 1
                            self.save_application(company, title, job_url, loc)
                            break

                        if review_btn and review_btn.is_visible():
                            review_btn.click()
                            self.human_delay(2, 3)
                            continue

                        required_fields = page.query_selector_all(
                            "input[required]:not([type='hidden']), "
                            "select[required], "
                            "textarea[required]"
                        )
                        unfilled = [f for f in required_fields if f.is_visible() and not f.input_value()]

                        if len(unfilled) > 2:
                            self.log(f"  Too many required fields ({len(unfilled)}). Skipping.")
                            self.skipped_count += 1
                            close = page.query_selector(
                                "button[aria-label='Close'], "
                                "button:has-text('Discard'), "
                                "button:has-text('Return')"
                            )
                            if close:
                                close.click()
                                self.human_delay(1, 2)
                            break

                        if continue_btn and continue_btn.is_visible():
                            continue_btn.click()
                            self.human_delay(2, 3)
                        else:
                            self.log(f"  Stuck at step {step+1}. Skipping.")
                            self.skipped_count += 1
                            break

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
    parser = argparse.ArgumentParser(description="Indeed job application automation")
    parser.add_argument("--keywords", default="Data Engineer")
    parser.add_argument("--location", default="Remote")
    parser.add_argument("--remote-only", action="store_true")
    parser.add_argument("--job-type", default="", choices=["", "fulltime", "parttime", "contract"])
    parser.add_argument("--age", default="14", help="Days since posted")
    parser.add_argument("--max-applications", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-delay", type=float, default=3)
    parser.add_argument("--max-delay", type=float, default=7)
    args = parser.parse_args()

    bot = IndeedAutomation(config={
        "min_delay": args.min_delay,
        "max_delay": args.max_delay,
        "max_applications": args.max_applications,
    })

    print("=" * 60)
    print("  Indeed Job Application Automation")
    print("=" * 60)
    print()

    if not args.dry_run:
        resp = input("Continue? (yes/no): ").strip().lower()
        if resp != "yes":
            print("Aborted.")
            return

    bot.run(
        keywords=args.keywords,
        location=args.location,
        remote_only=args.remote_only,
        job_type=args.job_type,
        age=args.age,
        max_applications=args.max_applications,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
