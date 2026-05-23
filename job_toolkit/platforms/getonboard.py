"""
GetOnBoard (getonbrd.com) job application automation.

GetOnBoard is popular in Latin America for tech jobs.
Applications typically require your profile + optional message.

USAGE:
    1. Start Chrome: google-chrome --remote-debugging-port=9222
    2. Log into GetOnBoard manually
    3. Run:
       python -m job_toolkit.platforms.getonboard \\
           --keywords "Data Engineer" --max-applications 5
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


class GetOnBoardAutomation(BasePlatformAutomation):
    name = "GetOnBoard"
    base_url = "https://www.getonbrd.com"

    CATEGORIES = {
        "data": "/jobs/data",
        "programming": "/jobs/programming",
        "devops": "/jobs/devops-sysadmin",
        "machine-learning": "/jobs/machine-learning",
        "all": "/jobs",
    }

    def _build_search_url(self, keywords="", category="data", remote_only=True, country=""):
        path = self.CATEGORIES.get(category, "/jobs")
        params = {}
        if keywords:
            params["q"] = keywords
        if remote_only:
            params["remote"] = "true"
        if country:
            country_map = {
                "chile": "/chile",
                "argentina": "/argentina",
                "mexico": "/mexico",
                "colombia": "/colombia",
                "peru": "/peru",
                "latam": "",
            }
            suffix = country_map.get(country.lower(), "")
            path = f"{path}{suffix}"

        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def _extract_job_info(self, card):
        """Extract job info from a GetOnBoard job card."""
        info = {"title": "", "company": "", "location": "", "salary": "", "remote": "", "url": ""}

        title_el = card.query_selector(".size0, .gb-results-list__item__title, h3 a, a[data-turbo-frame]")
        if title_el:
            info["title"] = title_el.inner_text().strip()
            href = title_el.get_attribute("href")
            if href:
                info["url"] = href if href.startswith("http") else f"{self.base_url}{href}"

        company_el = card.query_selector(".size2, .gb-results-list__item__company, a[data-turbo-frame] + div a, .company-name")
        if company_el:
            info["company"] = company_el.inner_text().strip()

        location_el = card.query_selector(".location, .gb-results-list__item__location, [class*='location']")
        if location_el:
            info["location"] = location_el.inner_text().strip()

        salary_el = card.query_selector(".salary, [class*='salary']")
        if salary_el:
            info["salary"] = salary_el.inner_text().strip()

        remote_el = card.query_selector(".badge--remote, [class*='remote'], .modality")
        if remote_el:
            text = remote_el.inner_text().strip().lower()
            if "remote" in text or "remoto" in text:
                info["remote"] = "Remote"
            elif "hybrid" in text or "mixto" in text or "hibrido" in text:
                info["remote"] = "Hybrid"
            else:
                info["remote"] = "On-site"

        return info

    def _apply_to_job(self, page, job_url, dry_run=False):
        """Navigate to a job page and apply."""
        page.goto(job_url, wait_until="domcontentloaded")
        self.human_delay(2, 4)

        apply_btn = page.query_selector(
            "a:has-text('Postular'), "
            "a:has-text('Apply'), "
            "button:has-text('Postular'), "
            "button:has-text('Apply'), "
            "a[href*='apply'], "
            ".apply-btn, "
            "[data-action*='apply']"
        )

        if not apply_btn:
            self.log("  No apply button found on job page.")
            return False

        if dry_run:
            return True

        apply_btn.click()
        self.human_delay(2, 4)

        if "login" in page.url or "sign_in" in page.url:
            self.log("  ERROR: Not logged in. Please log into GetOnBoard first.")
            return False

        message_field = page.query_selector(
            "textarea[name*='message'], "
            "textarea[name*='cover'], "
            "textarea#application_message, "
            "textarea"
        )
        if message_field and message_field.is_visible():
            from ..cover_letter import generate_email_body
            title_el = page.query_selector("h1, .job-title")
            title = title_el.inner_text().strip() if title_el else "this position"
            company_el = page.query_selector(".company-name, [class*='company']")
            company = company_el.inner_text().strip() if company_el else "your company"

            msg = generate_email_body(company=company, position=title)
            message_field.fill(msg)
            self.human_delay(1, 2)

        submit_btn = page.query_selector(
            "button[type='submit']:has-text('Enviar'), "
            "button[type='submit']:has-text('Send'), "
            "button[type='submit']:has-text('Postular'), "
            "button[type='submit']:has-text('Apply'), "
            "input[type='submit']"
        )

        if submit_btn and submit_btn.is_visible():
            submit_btn.click()
            self.human_delay(2, 4)

            success = page.query_selector(
                ":has-text('postulación'), "
                ":has-text('application'), "
                ":has-text('enviada'), "
                ":has-text('sent'), "
                ".alert-success, "
                ".flash--success"
            )
            return True

        self.log("  Could not find submit button.")
        return False

    def run(self, keywords="Data Engineer", category="data", remote_only=True,
            country="", max_applications=5, dry_run=False):
        max_applications = min(max_applications, self.config["max_applications"])

        self.log(f"Starting GetOnBoard automation")
        self.log(f"  Keywords: {keywords}")
        self.log(f"  Category: {category}")
        self.log(f"  Remote only: {remote_only}")
        self.log(f"  Country: {country or 'all LATAM'}")
        self.log(f"  Max applications: {max_applications}")
        self.log(f"  Dry run: {dry_run}")
        print()

        with sync_playwright() as p:
            browser = self.connect_browser(p)
            if not browser:
                return

            context = browser.contexts[0]
            page = context.new_page()

            search_url = self._build_search_url(keywords, category, remote_only, country)
            self.log(f"Searching: {search_url}")
            page.goto(search_url, wait_until="domcontentloaded")
            self.human_delay(2, 4)

            job_cards = page.query_selector_all(
                ".gb-results-list__item, "
                "[data-result], "
                ".job-item, "
                "div[class*='result'] > a, "
                "ul.jobs-list > li, "
                "turbo-frame[id^='job_']"
            )

            self.log(f"Found {len(job_cards)} job listings.\n")

            jobs = []
            for card in job_cards:
                info = self._extract_job_info(card)
                if info["title"]:
                    jobs.append(info)

            if not jobs:
                all_links = page.query_selector_all("a[href*='/jobs/']")
                for link in all_links:
                    text = link.inner_text().strip()
                    href = link.get_attribute("href") or ""
                    if text and len(text) > 5 and "/jobs/" in href and text.lower() not in ("jobs", "all jobs", "empleos"):
                        jobs.append({
                            "title": text,
                            "company": "",
                            "location": "",
                            "salary": "",
                            "remote": "",
                            "url": href if href.startswith("http") else f"{self.base_url}{href}",
                        })

            self.log(f"Extracted {len(jobs)} jobs to process.\n")

            for i, job in enumerate(jobs):
                if self.applied_count >= max_applications:
                    self.log(f"Reached max applications ({max_applications}).")
                    break

                title = job["title"]
                company = job["company"] or "Unknown"

                self.log(f"[{i+1}/{len(jobs)}] {title} @ {company}")

                if self.should_skip_title(title):
                    self.log(f"  Skipping (filtered out).")
                    self.skipped_count += 1
                    continue

                if not job["url"]:
                    self.log(f"  No URL found. Skipping.")
                    self.skipped_count += 1
                    continue

                try:
                    if dry_run:
                        self.log(f"  [DRY RUN] Would apply: {job['url']}")
                        self.applied_count += 1
                        continue

                    success = self._apply_to_job(page, job["url"], dry_run)
                    if success:
                        self.log(f"  Applied!")
                        self.applied_count += 1
                        self.save_application(
                            company=company,
                            position=title,
                            url=job["url"],
                            location=job.get("location", ""),
                            salary=job.get("salary", ""),
                            remote=job.get("remote", ""),
                        )
                    else:
                        self.skipped_count += 1

                    page.goto(search_url, wait_until="domcontentloaded")
                    self.human_delay()

                except PlaywrightTimeout:
                    self.log(f"  Timeout. Skipping.")
                    self.skipped_count += 1
                    self.errors.append(f"Timeout: {title}")
                except Exception as e:
                    self.log(f"  Error: {e}")
                    self.skipped_count += 1
                    self.errors.append(f"{title}: {e}")

                self.human_delay()

            page.close()

        self.print_summary()


def main():
    parser = argparse.ArgumentParser(description="GetOnBoard job application automation")
    parser.add_argument("--keywords", default="Data Engineer")
    parser.add_argument("--category", default="data",
                        choices=["data", "programming", "devops", "machine-learning", "all"])
    parser.add_argument("--country", default="", help="chile, argentina, mexico, colombia, peru, or empty for all")
    parser.add_argument("--no-remote", action="store_true", help="Don't filter for remote only")
    parser.add_argument("--max-applications", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-delay", type=float, default=2)
    parser.add_argument("--max-delay", type=float, default=6)
    args = parser.parse_args()

    bot = GetOnBoardAutomation(config={
        "min_delay": args.min_delay,
        "max_delay": args.max_delay,
        "max_applications": args.max_applications,
    })

    print("=" * 60)
    print("  GetOnBoard Job Application Automation")
    print("=" * 60)
    print()

    if not args.dry_run:
        resp = input("Continue? (yes/no): ").strip().lower()
        if resp != "yes":
            print("Aborted.")
            return

    bot.run(
        keywords=args.keywords,
        category=args.category,
        remote_only=not args.no_remote,
        country=args.country,
        max_applications=args.max_applications,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
