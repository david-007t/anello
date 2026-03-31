"""
David Osei-Tutu — resume context for Claude prompts.

Usage:
    from resume_context import get_resume, RESUME_TEXT
"""

IDENTITY = {
    "name": "David Osei-Tutu",
    "first_name": "David",
    "last_name": "Osei-Tutu",
    "email": "ddoseitutu@gmail.com",
    "phone": "980-474-6713",
    "linkedin": "linkedin.com/in/david-osei-tutu-89b1ab231",
    "current_title": "Data Engineer II at Nutanix",
    "education": "B.A. Computer Science, UNC Chapel Hill (2024) — Double Minor: Data Science, Statistics & Analytics",
}

RESUME_TEXT = """
Name: David Osei-Tutu
Email: ddoseitutu@gmail.com | Phone: 980-474-6713
LinkedIn: linkedin.com/in/david-osei-tutu-89b1ab231
Current Title: Data Engineer II at Nutanix (since 09/2025)
Education: B.A. Computer Science, UNC Chapel Hill (2024) — Double Minor: Data Science, Statistics & Analytics

CORE SKILLS
Languages: Python, SQL, JavaScript
Data: Spark (PySpark, Spark SQL), ETL, data modeling, large-scale processing
Orchestration: Apache Airflow, Informatica
Cloud & Warehouses: AWS (S3, EC2, IAM), Snowflake, PostgreSQL, MongoDB
AI/ML: LangChain, AI agents, applied ML
Tools: Docker, Git, GitHub, Jenkins, Tableau, Power BI, Jira, Confluence

KEY ACHIEVEMENTS
- Led end-to-end delivery of enterprise OKR platform — 300+ weekly active users including C-suite
- Architected 4.2TB financial reporting platform consolidating 9 source systems — 99.9%+ uptime
- Built AI-powered support tool that reduced time-to-resolution by 31%
- 36 production ETL pipelines managing 54 daily workflows — runtime optimized 22%
- Founded DOTIQ: built AI voice receptionist (15% → 55% booking conversion), lead gen system, freight chatbot
- STAR Award — Top 10% divisional talent at Nutanix (04/2025)
- Published at IEEE VIS & SIGACCESS ASSETS, cited in Computer Graphics Forum
- Panelist at Santa Clara University AI Panel alongside Nutanix SVP, VP, and Chief AI Officer
"""

JOB_CRITERIA = {
    "target_roles": [
        "Data Engineer",
        "Senior Data Engineer",
        "Data Engineering Manager",
        "Technical Operations Manager",
        "Technical Product Manager",
    ],
    "work_type": "Remote only",
    "min_salary": 140000,
    "location": "US-based",
    "keywords_positive": [
        "Python", "SQL", "Snowflake", "Airflow", "Spark", "ETL",
        "data pipelines", "AWS", "LangChain", "AI", "data platform",
    ],
    "keywords_negative": [
        "junior", "entry-level", "intern", "internship", "on-site required",
        "director", "vice president", "vp of", "chief", "head of",
        "senior manager", "sr. manager", "sr manager",
        "principal engineer", "principal data", "principal product",
        "staff data engineer",
    ],
}

VOICE_INSTRUCTIONS = """
Write in David's voice:
- Direct and confident — not overly formal or stiff
- Professional but conversational — like a sharp engineer who knows their worth
- Concise — no fluff, no filler sentences
- Always mention remote-only and $140k+ minimum salary early if the recruiter hasn't confirmed these
- If the role sounds interesting, express genuine interest — don't be generic
- If the role is clearly not a fit, decline politely and briefly
"""

# Resume variant selection
_VARIANT_PATHS = {
    "general":  "david_ot_resume.pdf",
    "technical": "dot_resume.pdf",
    "qa":       "DOT_QA_Resume.pdf",
    "startup":  "dot_startup_resume.pdf",
}


def get_resume_path(company_type: str = "general") -> str:
    """
    Return the path to the appropriate resume PDF.

    company_type options:
        'general'   — default, data engineering roles
        'technical' — technical/platform focus
        'qa'        — data quality / testing roles
        'startup'   — early-stage companies
    """
    import os
    base = os.path.dirname(os.path.abspath(__file__))
    variant = _VARIANT_PATHS.get(company_type, _VARIANT_PATHS["general"])
    return os.path.join(base, variant)


def get_resume_text() -> str:
    return RESUME_TEXT.strip()
