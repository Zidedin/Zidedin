#!/usr/bin/env python3
"""
Run job application automation across multiple platforms.

USAGE:
    1. Start Chrome: google-chrome --remote-debugging-port=9222
    2. Log into all platforms you want to use
    3. Run:
       python -m job_toolkit.platforms.run_all \\
           --platforms getonboard linkedin indeed \\
           --keywords "Data Engineer" \\
           --max-per-platform 3 \\
           --dry-run
"""

import argparse
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Multi-platform job application automation")
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["getonboard"],
        choices=["getonboard", "indeed", "wellfound", "linkedin"],
        help="Platforms to automate",
    )
    parser.add_argument("--keywords", default="Data Engineer")
    parser.add_argument("--location", default="Remote")
    parser.add_argument("--max-per-platform", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--min-delay", type=float, default=3)
    parser.add_argument("--max-delay", type=float, default=7)
    args = parser.parse_args()

    config = {
        "min_delay": args.min_delay,
        "max_delay": args.max_delay,
        "max_applications": args.max_per_platform,
    }

    print("=" * 60)
    print("  Multi-Platform Job Application Automation")
    print(f"  Platforms: {', '.join(args.platforms)}")
    print(f"  Keywords: {args.keywords}")
    print(f"  Max per platform: {args.max_per_platform}")
    print(f"  Dry run: {args.dry_run}")
    print("=" * 60)
    print()

    if not args.dry_run:
        resp = input("Continue? (yes/no): ").strip().lower()
        if resp != "yes":
            print("Aborted.")
            return

    total_applied = 0
    total_skipped = 0

    for platform_name in args.platforms:
        print(f"\n{'=' * 60}")
        print(f"  Platform: {platform_name.upper()}")
        print(f"{'=' * 60}\n")

        try:
            if platform_name == "getonboard":
                from .getonboard import GetOnBoardAutomation
                bot = GetOnBoardAutomation(config=config)
                bot.run(
                    keywords=args.keywords,
                    max_applications=args.max_per_platform,
                    dry_run=args.dry_run,
                )

            elif platform_name == "indeed":
                from .indeed import IndeedAutomation
                bot = IndeedAutomation(config=config)
                bot.run(
                    keywords=args.keywords,
                    location=args.location,
                    max_applications=args.max_per_platform,
                    dry_run=args.dry_run,
                )

            elif platform_name == "wellfound":
                from .wellfound import WellfoundAutomation
                bot = WellfoundAutomation(config=config)
                bot.run(
                    role=args.keywords.lower().replace(" ", "-"),
                    max_applications=args.max_per_platform,
                    dry_run=args.dry_run,
                )

            elif platform_name == "linkedin":
                from ..browser_automation import run_easy_apply
                run_easy_apply(
                    keywords=args.keywords,
                    location=args.location,
                    max_applications=args.max_per_platform,
                    dry_run=args.dry_run,
                )

            total_applied += getattr(bot, "applied_count", 0) if platform_name != "linkedin" else 0
            total_skipped += getattr(bot, "skipped_count", 0) if platform_name != "linkedin" else 0

        except Exception as e:
            print(f"\nError on {platform_name}: {e}\n")

    print(f"\n{'=' * 60}")
    print(f"  ALL PLATFORMS COMPLETE")
    print(f"  Total applied: {total_applied}")
    print(f"  Total skipped: {total_skipped}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
