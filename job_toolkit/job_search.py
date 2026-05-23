"""Job search helpers using public sources."""

import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser


@dataclass
class JobListing:
    title: str
    company: str
    location: str = ""
    url: str = ""
    source: str = ""
    description_snippet: str = ""
    salary: str = ""
    remote: str = ""
    posted: str = ""

    def to_dict(self):
        return asdict(self)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self._text.append(data.strip())

    def get_text(self):
        return " ".join(t for t in self._text if t)


def _extract_text(html):
    parser = _TextExtractor()
    parser.feed(html)
    return parser.get_text()


def build_linkedin_search_url(
    keywords="Data Engineer",
    location="",
    remote=True,
    experience_level="",
    time_posted="month",
):
    """Build a LinkedIn job search URL (user opens in browser)."""
    params = {"keywords": keywords, "refresh": "true"}
    if location:
        params["location"] = location
    if remote:
        params["f_WT"] = "2"  # Remote filter
    time_map = {"day": "r86400", "week": "r604800", "month": "r2592000"}
    if time_posted in time_map:
        params["f_TPR"] = time_map[time_posted]
    exp_map = {
        "internship": "1",
        "entry": "2",
        "associate": "3",
        "mid-senior": "4",
        "director": "5",
        "executive": "6",
    }
    if experience_level in exp_map:
        params["f_E"] = exp_map[experience_level]
    return "https://www.linkedin.com/jobs/search/?" + urllib.parse.urlencode(params)


def build_indeed_search_url(
    query="Data Engineer",
    location="Remote",
    radius="",
    job_type="",
    age="14",
):
    """Build an Indeed job search URL."""
    params = {"q": query, "l": location, "fromage": age}
    if radius:
        params["radius"] = radius
    type_map = {"fulltime": "fulltime", "parttime": "parttime", "contract": "contract"}
    if job_type in type_map:
        params["jt"] = type_map[job_type]
    return "https://www.indeed.com/jobs?" + urllib.parse.urlencode(params)


def build_glassdoor_search_url(query="Data Engineer", location="Remote"):
    """Build a Glassdoor job search URL."""
    params = {"sc.keyword": query, "locT": "N", "locKeyword": location}
    return "https://www.glassdoor.com/Job/jobs.htm?" + urllib.parse.urlencode(params)


def build_google_jobs_url(query="Data Engineer remote", location=""):
    """Build a Google Jobs search URL."""
    search = f"{query} jobs"
    if location:
        search += f" {location}"
    return "https://www.google.com/search?" + urllib.parse.urlencode(
        {"q": search, "ibp": "htl;jobs"}
    )


def generate_search_links(role="Data Engineer", location="Remote"):
    """Generate search URLs for multiple job boards."""
    return {
        "LinkedIn": build_linkedin_search_url(keywords=role, location=location),
        "Indeed": build_indeed_search_url(query=role, location=location),
        "Glassdoor": build_glassdoor_search_url(query=role, location=location),
        "Google Jobs": build_google_jobs_url(query=f"{role} {location}"),
    }


NICHE_BOARDS = {
    "Data-specific": [
        {"name": "DataJobs.com", "url": "https://datajobs.com/"},
        {"name": "Data Engineer Jobs", "url": "https://www.dataengineerjobs.com/"},
        {"name": "Analytics Vidhya Jobs", "url": "https://jobsnew.analyticsvidhya.com/jobs"},
    ],
    "Remote-focused": [
        {"name": "We Work Remotely", "url": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs"},
        {"name": "Remote OK", "url": "https://remoteok.com/remote-data-engineer-jobs"},
        {"name": "FlexJobs", "url": "https://www.flexjobs.com/search?search=data+engineer"},
        {"name": "Turing", "url": "https://www.turing.com/remote-developer-jobs/data-engineer"},
    ],
    "Tech-focused": [
        {"name": "Wellfound (AngelList)", "url": "https://wellfound.com/role/data-engineer"},
        {"name": "Dice", "url": "https://www.dice.com/jobs?q=data%20engineer"},
        {"name": "Hired", "url": "https://hired.com/"},
        {"name": "Triplebyte", "url": "https://triplebyte.com/"},
    ],
    "Latin America": [
        {"name": "Torre.ai", "url": "https://torre.ai/jobs?q=data+engineer"},
        {"name": "GetonBoard", "url": "https://www.getonbrd.com/jobs/data"},
        {"name": "Turing (LATAM)", "url": "https://www.turing.com/remote-developer-jobs/data-engineer"},
    ],
}
