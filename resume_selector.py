"""
resume_selector.py

Selects and scores resume entries from resume_db.json for a given job description.
Used to build targeted context for Claude resume tailoring prompts.
"""

import json
import os
import re
from typing import Optional
from collections import Counter
from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROLE_TYPE_KEYWORDS = {
    "data-eng": ["data engineer", "etl", "data pipeline", "airflow", "spark", "data platform", "snowflake", "data warehouse", "dbt", "databricks"],
    "analytics": ["data analyst", "analytics engineer", "business intelligence", "bi developer", "tableau", "power bi", "reporting", "dashboard"],
    "ml-eng": ["machine learning", "ml engineer", "ai engineer", "langchain", "llm", "deep learning", "model training", "generative ai"],
    "tpm": ["technical product manager", "tpm", "product manager", "program manager", "product roadmap", "product operations"],
    "ops-mgr": ["technical operations", "operations manager", "engineering manager", "team lead", "cross-functional", "delivery manager"],
    "swe": ["software engineer", "backend engineer", "python developer", "api developer", "microservices", "rest api"],
    "founder": ["founding engineer", "early stage", "series a", "seed", "startup", "0-to-1"],
}

KNOWN_TECH_TERMS = {
    "python", "sql", "spark", "pyspark", "airflow", "snowflake", "aws", "s3", "ec2",
    "docker", "git", "jenkins", "etl", "postgresql", "mongodb", "tableau", "power bi",
    "jira", "confluence", "langchain", "kubernetes", "kafka", "dbt", "terraform",
    "rest api", "microservices", "agile", "scrum", "data modeling", "data warehouse",
    "machine learning", "deep learning", "pytest", "selenium", "informatica",
}

DEFAULT_LIMITS = {
    "experience": 5,
    "skills": 10,
    "projects": 2,
    "education": 99,
    "awards": 99,
    "publications": 3,
}

# Stop words to exclude from keyword extraction
_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "we", "you", "they", "he", "she", "it",
    "our", "your", "their", "this", "that", "these", "those", "as", "if", "so",
    "not", "no", "nor", "both", "either", "neither", "each", "more", "most",
    "other", "some", "such", "than", "too", "very", "just", "also", "about",
    "above", "after", "before", "between", "into", "through", "during", "up",
    "experience", "role", "team", "work", "working", "strong", "ability", "skills",
    "using", "use", "build", "building", "develop", "developing", "manage",
    "managing", "support", "supporting", "help", "ensure", "across", "within",
    "including", "well", "new", "key", "large", "high", "good", "great",
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def load_resume_db() -> dict:
    """Load resume_db.json from same directory as this script."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resume_db.json")
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_job_type(title: str, jd_text: str) -> list[str]:
    """Return role_types ranked by keyword match count. Falls back to ['data-eng']."""
    combined = (title + " " + jd_text).lower()
    scores: dict[str, int] = {}

    for role_type, keywords in ROLE_TYPE_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in combined)
        if count > 0:
            scores[role_type] = count

    if not scores:
        return ["data-eng"]

    # Sort by match count descending
    ranked = sorted(scores.keys(), key=lambda rt: scores[rt], reverse=True)
    return ranked


def extract_jd_keywords(jd_text: str) -> list[str]:
    """Extract tech terms + high-freq words from JD. Returns ~20 keywords."""
    text_lower = jd_text.lower()
    found_keywords: list[str] = []

    # First pass: multi-word known tech terms (order matters — longest first)
    multi_word = sorted([t for t in KNOWN_TECH_TERMS if " " in t], key=len, reverse=True)
    for term in multi_word:
        if term in text_lower:
            found_keywords.append(term)

    # Second pass: single-word known tech terms
    words = re.findall(r"\b[a-z][a-z0-9+#.]*\b", text_lower)
    for word in words:
        if word in KNOWN_TECH_TERMS and word not in found_keywords:
            found_keywords.append(word)

    # Third pass: high-frequency non-stop words not already captured
    word_counts = Counter(w for w in words if w not in _STOP_WORDS and len(w) > 3)
    for word, _ in word_counts.most_common(30):
        if word not in found_keywords and word not in _STOP_WORDS:
            found_keywords.append(word)
        if len(found_keywords) >= 20:
            break

    return found_keywords[:20]


def _recency_bonus(entry: dict) -> float:
    """Return a recency score based on start_date or date field."""
    date_str = entry.get("start_date") or entry.get("date") or ""
    if not date_str:
        return 0.0
    try:
        year = int(date_str[:4])
        if year >= 2024:
            return 1.0
        if year >= 2023:
            return 0.5
    except (ValueError, IndexError):
        pass
    return 0.0


def score_entry(entry: dict, job_types: list[str], jd_keywords: list[str]) -> float:
    """Score a resume entry by tag overlap + keyword match in text + recency."""
    score = 0.0
    jd_kw_set = {kw.lower() for kw in jd_keywords}
    job_type_set = set(job_types)

    # Role type overlap (weighted by rank position)
    entry_role_types = set(entry.get("role_types", []))
    for i, jt in enumerate(job_types):
        if jt in entry_role_types:
            score += max(1.0, 3.0 - i * 0.5)  # primary match worth 3, diminishing

    # Tag overlap with job types (tags often embed role type strings)
    entry_tags = set(entry.get("tags", []))
    for tag in entry_tags:
        if tag in job_type_set:
            score += 0.5

    # Keyword match in text fields
    text_fields = " ".join([
        entry.get("text", ""),
        entry.get("name", ""),
        entry.get("description", ""),
        entry.get("outcome", ""),
        entry.get("context", ""),
        " ".join(entry.get("skills", [])),
        " ".join(entry_tags),
    ]).lower()

    for kw in jd_kw_set:
        if kw in text_fields:
            score += 0.5

    # Recency bonus
    score += _recency_bonus(entry)

    return score


def _score_bullet(bullet: dict, job: dict, job_types: list[str], jd_keywords: list[str]) -> float:
    """Score an individual bullet, combining bullet tags + parent job context."""
    jd_kw_set = {kw.lower() for kw in jd_keywords}
    job_type_set = set(job_types)
    score = 0.0

    # Bullet tag overlap with role types
    bullet_tags = set(bullet.get("tags", []))
    for i, jt in enumerate(job_types):
        if jt in bullet_tags:
            score += max(1.0, 3.0 - i * 0.5)

    # Keyword match in bullet text
    bullet_text = bullet.get("text", "").lower()
    for kw in jd_kw_set:
        if kw in bullet_text:
            score += 0.5

    # Prefer quantified impact
    if bullet.get("impact_type") == "quantified":
        score += 0.75

    # Parent job recency bonus
    score += _recency_bonus(job)

    return score


def select_entries(db: dict, job_types: list[str], jd_keywords: list[str], limits: Optional[dict] = None) -> dict:
    """Select top N entries per section from resume DB."""
    if limits is None:
        limits = DEFAULT_LIMITS

    selected: dict = {}

    # --- Experience: score bullets individually, dedupe by job ---
    exp_limit = limits.get("experience", DEFAULT_LIMITS["experience"])
    all_scored_bullets: list[tuple[float, dict, dict]] = []  # (score, bullet, job)

    for job in db.get("experience", []):
        for bullet in job.get("bullets", []):
            s = _score_bullet(bullet, job, job_types, jd_keywords)
            all_scored_bullets.append((s, bullet, job))

    all_scored_bullets.sort(key=lambda x: x[0], reverse=True)

    # Pick top bullets, tracking which jobs are needed for context
    top_bullets = all_scored_bullets[:exp_limit]
    job_to_bullets: dict[str, dict] = {}

    for score, bullet, job in top_bullets:
        job_id = job["id"]
        if job_id not in job_to_bullets:
            job_to_bullets[job_id] = {
                "id": job["id"],
                "role": job["role"],
                "company": job["company"],
                "start_date": job.get("start_date", ""),
                "end_date": job.get("end_date"),
                "bullets": [],
            }
        job_to_bullets[job_id]["bullets"].append(bullet)

    # Preserve original job ordering
    job_order = [j["id"] for j in db.get("experience", [])]
    selected["experience"] = [
        job_to_bullets[jid] for jid in job_order if jid in job_to_bullets
    ]

    # --- Skills: score and return top N ---
    skill_limit = limits.get("skills", DEFAULT_LIMITS["skills"])
    scored_skills = []
    for skill in db.get("skills", []):
        s = score_entry(skill, job_types, jd_keywords)
        scored_skills.append((s, skill))
    scored_skills.sort(key=lambda x: x[0], reverse=True)
    selected["skills"] = [sk for _, sk in scored_skills[:skill_limit]]

    # --- Projects: score and return top N ---
    proj_limit = limits.get("projects", DEFAULT_LIMITS["projects"])
    scored_projects = []
    for project in db.get("projects", []):
        s = score_entry(project, job_types, jd_keywords)
        scored_projects.append((s, project))
    scored_projects.sort(key=lambda x: x[0], reverse=True)
    selected["projects"] = [p for _, p in scored_projects[:proj_limit]]

    # --- Education: return all (up to limit) ---
    edu_limit = limits.get("education", DEFAULT_LIMITS["education"])
    selected["education"] = db.get("education", [])[:edu_limit]

    # --- Awards: return all (up to limit) ---
    award_limit = limits.get("awards", DEFAULT_LIMITS["awards"])
    selected["awards"] = db.get("awards", [])[:award_limit]

    # --- Publications: return top N ---
    pub_limit = limits.get("publications", DEFAULT_LIMITS["publications"])
    selected["publications"] = db.get("publications", [])[:pub_limit]

    return selected


def _format_date(date_str: Optional[str]) -> str:
    """Convert ISO date string to human-readable month/year."""
    if not date_str:
        return "Present"
    try:
        dt = datetime.strptime(date_str[:7], "%Y-%m")
        return dt.strftime("%b %Y")
    except ValueError:
        return date_str


def format_selected_context(selected: dict) -> str:
    """Render selected entries to a structured text block for Claude prompt."""
    sections: list[str] = []

    # === EXPERIENCE ===
    exp_entries = selected.get("experience", [])
    if exp_entries:
        lines = ["=== EXPERIENCE ==="]
        for job in exp_entries:
            start = _format_date(job.get("start_date"))
            end = _format_date(job.get("end_date"))
            lines.append(f"{job['role']} @ {job['company']} ({start} - {end})")
            for bullet in job.get("bullets", []):
                lines.append(f"  - {bullet['text']}")
            lines.append("")
        sections.append("\n".join(lines).rstrip())

    # === SKILLS ===
    skills = selected.get("skills", [])
    if skills:
        skill_names = [s["name"] for s in skills]
        sections.append("=== SKILLS ===\n" + ", ".join(skill_names))

    # === PROJECTS ===
    projects = selected.get("projects", [])
    if projects:
        lines = ["=== PROJECTS ==="]
        for proj in projects:
            lines.append(f"{proj['name']}")
            lines.append(f"  {proj.get('description', '')}")
            if proj.get("outcome"):
                lines.append(f"  Outcome: {proj['outcome']}")
            if proj.get("skills"):
                lines.append(f"  Skills: {', '.join(proj['skills'])}")
            lines.append("")
        sections.append("\n".join(lines).rstrip())

    # === EDUCATION ===
    education = selected.get("education", [])
    if education:
        lines = ["=== EDUCATION ==="]
        for edu in education:
            grad = _format_date(edu.get("graduation_date"))
            minors = ""
            if edu.get("minors"):
                minors = f" | Minors: {', '.join(edu['minors'])}"
            lines.append(f"{edu['degree']} {edu['field']} — {edu['institution']} ({grad}){minors}")
        sections.append("\n".join(lines))

    # === AWARDS ===
    awards = selected.get("awards", [])
    if awards:
        lines = ["=== AWARDS ==="]
        for award in awards:
            date = _format_date(award.get("date"))
            lines.append(f"{award['name']} — {award.get('issuer', '')} ({date})")
            if award.get("description"):
                lines.append(f"  {award['description']}")
        sections.append("\n".join(lines))

    # === PUBLICATIONS ===
    publications = selected.get("publications", [])
    if publications:
        lines = ["=== PUBLICATIONS ==="]
        for pub in publications:
            date = _format_date(pub.get("date"))
            lines.append(f"{pub['title']}")
            lines.append(f"  {pub.get('venue', '')} ({date})")
            if pub.get("cited_by"):
                lines.append(f"  Cited by: {pub['cited_by']}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# CLI test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    db = load_resume_db()
    job_types = detect_job_type("Analytics Engineer", "SQL Snowflake dbt data warehouse reporting Tableau")
    keywords = extract_jd_keywords("SQL Snowflake dbt data warehouse reporting Tableau pipeline")
    selected = select_entries(db, job_types, keywords)
    print(format_selected_context(selected))
