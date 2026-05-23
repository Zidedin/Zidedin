#!/usr/bin/env python3
"""CLI interface for the job search toolkit."""

import argparse
import json
import sys
import textwrap

from . import cover_letter, interview_prep, job_search, tracker
from .config import PROFILE


def cmd_search(args):
    """Generate job search links."""
    role = args.role or "Data Engineer"
    location = args.location or "Remote"
    print(f"\n🔍 Job search links for: {role} ({location})\n")
    print("=" * 60)

    links = job_search.generate_search_links(role, location)
    for board, url in links.items():
        print(f"\n  {board}:")
        print(f"    {url}")

    if args.niche:
        print(f"\n{'=' * 60}")
        print("\n📋 Niche & Specialized Job Boards:\n")
        for category, boards in job_search.NICHE_BOARDS.items():
            print(f"  {category}:")
            for board in boards:
                print(f"    - {board['name']}: {board['url']}")
            print()


def cmd_add(args):
    """Add a job application."""
    row = tracker.add_application(
        company=args.company,
        position=args.position,
        status=args.status,
        priority=args.priority,
        source=args.source,
        salary_range=args.salary or "",
        location=args.location or "",
        remote=args.remote,
        job_url=args.url or "",
        contact=args.contact or "",
        notes=args.notes or "",
    )
    print(f"\n✅ Added application #{row['id']}: {row['position']} at {row['company']}")


def cmd_list(args):
    """List applications."""
    rows = tracker.list_applications(status=args.status, priority=args.priority)
    if not rows:
        print("\n📭 No applications found.")
        return

    print(f"\n📋 Job Applications ({len(rows)} total)\n")
    print(f"{'ID':>4} | {'Company':<20} | {'Position':<25} | {'Status':<20} | {'Priority':<8} | {'Source':<10}")
    print("-" * 100)
    for r in rows:
        print(
            f"{r['id']:>4} | {r['company']:<20} | {r['position']:<25} | "
            f"{r['status']:<20} | {r['priority']:<8} | {r['source']:<10}"
        )


def cmd_update(args):
    """Update application status."""
    row = tracker.update_status(args.id, args.status)
    if row:
        print(f"\n✅ Updated #{row['id']} ({row['company']}) -> {row['status']}")
    else:
        print(f"\n❌ Application #{args.id} not found.")


def cmd_stats(args):
    """Show application stats."""
    stats = tracker.get_stats()
    print("\n📊 Application Statistics\n")
    print(f"  Total applications: {stats['total']}")
    print()
    for status in tracker.VALID_STATUSES:
        count = stats.get(status, 0)
        bar = "█" * count
        print(f"  {status:<22} {count:>3} {bar}")


def cmd_cover_letter(args):
    """Generate a cover letter."""
    jd = ""
    if args.jd_file:
        with open(args.jd_file) as f:
            jd = f.read()

    letter = cover_letter.generate_cover_letter(
        company=args.company,
        position=args.position,
        job_description=jd,
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(letter)
        print(f"\n✅ Cover letter saved to {args.output}")
    else:
        print(letter)


def cmd_email(args):
    """Generate an outreach email."""
    jd = ""
    if args.jd_file:
        with open(args.jd_file) as f:
            jd = f.read()

    body = cover_letter.generate_email_body(
        company=args.company,
        position=args.position,
        recruiter_name=args.recruiter or "",
        job_description=jd,
    )
    print(body)


def cmd_prep(args):
    """Show interview prep materials."""
    if args.topic:
        details = interview_prep.get_topic_details(args.topic)
        if not details:
            print(f"\n❌ Topic '{args.topic}' not found.")
            print(f"Available: {', '.join(interview_prep.COMMON_TOPICS.keys())}")
            return
        print(f"\n📚 {args.topic} Interview Prep\n")
        print("Key Areas:")
        for area in details["key_areas"]:
            print(f"  - {area}")
        print("\nPractice Questions:")
        for q in details["sample_questions"]:
            print(f"  - {q}")
    elif args.plan:
        plan = interview_prep.get_study_plan(weeks=args.weeks)
        print(f"\n📅 {args.weeks}-Week Study Plan\n")
        for week, topics in plan.items():
            print(f"  {week}: {', '.join(topics)}")
    else:
        print(interview_prep.format_prep_guide())


def cmd_profile(args):
    """Show current profile."""
    print(f"\n👤 Profile: {PROFILE['name']}")
    print(f"   Title: {PROFILE['title']}")
    print(f"   Email: {PROFILE['email']}")
    print(f"   LinkedIn: {PROFILE['linkedin']}")
    print(f"\n   Core Skills: {', '.join(PROFILE['core_skills'])}")
    print(f"   Target Roles: {', '.join(PROFILE['target_roles'])}")
    print(f"   Preferred Locations: {', '.join(PROFILE['preferred_locations'])}")


def main():
    parser = argparse.ArgumentParser(
        description="Job Search Toolkit - Data Engineer Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python -m job_toolkit search --role "Senior Data Engineer" --niche
              python -m job_toolkit add --company Google --position "Data Engineer" --priority High
              python -m job_toolkit list --status "To Apply"
              python -m job_toolkit cover-letter --company Google --position "Data Engineer"
              python -m job_toolkit prep --topic SQL
              python -m job_toolkit stats
        """),
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # search
    sp = subparsers.add_parser("search", help="Generate job search links")
    sp.add_argument("--role", default="Data Engineer", help="Job role to search")
    sp.add_argument("--location", default="Remote", help="Location filter")
    sp.add_argument("--niche", action="store_true", help="Include niche job boards")
    sp.set_defaults(func=cmd_search)

    # add
    sp = subparsers.add_parser("add", help="Add a job application")
    sp.add_argument("--company", required=True)
    sp.add_argument("--position", required=True)
    sp.add_argument("--status", default="To Apply", choices=tracker.VALID_STATUSES)
    sp.add_argument("--priority", default="Medium", choices=tracker.VALID_PRIORITIES)
    sp.add_argument("--source", default="LinkedIn", choices=tracker.VALID_SOURCES)
    sp.add_argument("--salary", default="")
    sp.add_argument("--location", default="")
    sp.add_argument("--remote", default="Remote", choices=tracker.VALID_REMOTE)
    sp.add_argument("--url", default="")
    sp.add_argument("--contact", default="")
    sp.add_argument("--notes", default="")
    sp.set_defaults(func=cmd_add)

    # list
    sp = subparsers.add_parser("list", help="List applications")
    sp.add_argument("--status", choices=tracker.VALID_STATUSES)
    sp.add_argument("--priority", choices=tracker.VALID_PRIORITIES)
    sp.set_defaults(func=cmd_list)

    # update
    sp = subparsers.add_parser("update", help="Update application status")
    sp.add_argument("--id", required=True, type=int)
    sp.add_argument("--status", required=True, choices=tracker.VALID_STATUSES)
    sp.set_defaults(func=cmd_update)

    # stats
    sp = subparsers.add_parser("stats", help="Show application statistics")
    sp.set_defaults(func=cmd_stats)

    # cover-letter
    sp = subparsers.add_parser("cover-letter", help="Generate a cover letter")
    sp.add_argument("--company", required=True)
    sp.add_argument("--position", required=True)
    sp.add_argument("--jd-file", help="Path to job description text file")
    sp.add_argument("--output", "-o", help="Output file path")
    sp.set_defaults(func=cmd_cover_letter)

    # email
    sp = subparsers.add_parser("email", help="Generate outreach email")
    sp.add_argument("--company", required=True)
    sp.add_argument("--position", required=True)
    sp.add_argument("--recruiter", help="Recruiter name")
    sp.add_argument("--jd-file", help="Path to job description text file")
    sp.set_defaults(func=cmd_email)

    # prep
    sp = subparsers.add_parser("prep", help="Interview preparation")
    sp.add_argument("--topic", help="Specific topic (SQL, Python, etc.)")
    sp.add_argument("--plan", action="store_true", help="Generate study plan")
    sp.add_argument("--weeks", type=int, default=4, help="Weeks for study plan")
    sp.set_defaults(func=cmd_prep)

    # profile
    sp = subparsers.add_parser("profile", help="Show profile")
    sp.set_defaults(func=cmd_profile)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
