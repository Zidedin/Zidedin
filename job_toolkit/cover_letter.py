"""Cover letter generator tailored for Data Engineer roles."""

from datetime import datetime

from .config import PROFILE


def generate_cover_letter(company, position, job_description="", highlights=None):
    """Generate a personalized cover letter.

    Args:
        company: Target company name.
        position: Job title.
        job_description: Optional job description to match skills against.
        highlights: Optional list of specific achievements to emphasize.
    """
    matched_skills = _match_skills(job_description) if job_description else PROFILE["core_skills"][:8]
    highlights = highlights or _default_highlights()

    date_str = datetime.now().strftime("%B %d, %Y")

    letter = f"""{date_str}

Dear Hiring Manager,

I am writing to express my strong interest in the {position} position at {company}. As a {PROFILE['title']} with {PROFILE['years_experience']}+ years of experience building scalable data solutions, I am confident in my ability to contribute meaningfully to your team.

{PROFILE['summary']}

My technical expertise aligns well with this role. I bring hands-on experience with {', '.join(matched_skills[:6])}, and {matched_skills[6] if len(matched_skills) > 6 else 'more'}. Key highlights from my career include:

"""
    for h in highlights:
        letter += f"  - {h}\n"

    letter += f"""
I am particularly drawn to {company} because of the opportunity to work on challenging data engineering problems at scale. I thrive in environments that value innovation, collaboration, and technical excellence.

I would welcome the opportunity to discuss how my background in data engineering and cloud architecture can benefit your team. Please feel free to reach out at {PROFILE['email']} or connect with me on LinkedIn.

Thank you for your consideration.

Best regards,
{PROFILE['name']}
LinkedIn: {PROFILE['linkedin']}
"""
    return letter


def _match_skills(job_description):
    jd_lower = job_description.lower()
    matched = [s for s in PROFILE["core_skills"] if s.lower() in jd_lower]
    if len(matched) < 5:
        remaining = [s for s in PROFILE["core_skills"] if s not in matched]
        matched.extend(remaining[: 8 - len(matched)])
    return matched


def _default_highlights():
    return [
        "Designed and maintained scalable ETL/ELT pipelines processing large volumes of data daily",
        "Built cloud-native data platforms on AWS and GCP using serverless and containerized architectures",
        "Implemented workflow orchestration with Apache Airflow for complex data transformation pipelines",
        "Established CI/CD practices and infrastructure-as-code using Terraform, Docker, and Kubernetes",
        "Developed real-time data streaming solutions using Apache Kafka",
    ]


def generate_email_body(company, position, recruiter_name="", job_description=""):
    """Generate a shorter email version for direct outreach."""
    matched_skills = _match_skills(job_description) if job_description else PROFILE["core_skills"][:6]
    greeting = f"Hi {recruiter_name}," if recruiter_name else "Hi,"

    return f"""{greeting}

I came across the {position} opening at {company} and I'm very interested. I'm a {PROFILE['title']} with {PROFILE['years_experience']}+ years of experience in {', '.join(matched_skills[:4])}, and cloud-native data solutions.

I'd love to chat about how my experience building scalable data pipelines and cloud architectures could contribute to your team. My LinkedIn profile has more details: {PROFILE['linkedin']}

Would you be open to a quick conversation this week?

Best,
{PROFILE['name']}
"""
