"""
scorer.py — Score and filter jobs against user preferences.
Simple keyword matching — no AI call needed for this step.
"""
import re


def score_job(job: dict, prefs: dict) -> int:
    """
    Returns a score 0–100 for how well a job matches preferences.
    """
    score = 0
    text = f"{job.get('title','')} {job.get('description','')}".lower()

    # Skills match
    skills_raw = prefs.get("skills") or ""
    if skills_raw:
        skills = [s.strip().lower() for s in re.split(r"[,;]", skills_raw) if s.strip()]
        matched = sum(1 for s in skills if s in text)
        score += int((matched / max(len(skills), 1)) * 50)

    # Role match
    role = (prefs.get("role") or "").lower()
    if role and role in text:
        score += 30

    # Company type match
    company_types = (prefs.get("company_types") or "").lower()
    if company_types:
        types = [t.strip() for t in re.split(r"[,;]", company_types) if t.strip()]
        company_text = job.get("company", "").lower()
        if any(t in company_text or t in text for t in types):
            score += 20

    return min(score, 100)


def filter_and_rank(jobs: list[dict], prefs: dict, min_score: int = 20) -> list[dict]:
    """Score all jobs, filter low scores, return ranked list."""
    scored = []
    for job in jobs:
        s = score_job(job, prefs)
        if s >= min_score:
            scored.append({**job, "score": s})

    scored.sort(key=lambda j: j["score"], reverse=True)
    return scored
