"""
scorer.py — Score and filter jobs against user preferences.
Simple keyword matching — no AI call needed for this step.
"""
import re


_YRS_RE = re.compile(r"(\d+)\+?\s*(?:to\s*(\d+)\s*)?years?", re.IGNORECASE)


def _extract_years_required(text: str) -> int | None:
    """Return the minimum years of experience mentioned in job text, or None."""
    m = _YRS_RE.search(text)
    if m:
        return int(m.group(1))
    return None


def score_job(job: dict, prefs: dict) -> int:
    """
    Returns a score 0–100 for how well a job matches preferences.
    """
    score = 0
    text = f"{job.get('title') or ''} {job.get('description') or ''}".lower()

    # Skills match
    skills_raw = prefs.get("skills") or ""
    if skills_raw:
        skills = [s.strip().lower() for s in re.split(r"[,;]", skills_raw) if s.strip()]
        matched = sum(1 for s in skills if s in text)
        score += int((matched / max(len(skills), 1)) * 50)

    # Role match — check all 3 roles
    roles = [
        (prefs.get("role") or "").lower(),
        (prefs.get("role_2") or "").lower(),
        (prefs.get("role_3") or "").lower(),
    ]
    if any(r and r in text for r in roles):
        score += 30

    # Company type match
    company_types = (prefs.get("company_types") or "").lower()
    if company_types:
        types = [t.strip() for t in re.split(r"[,;]", company_types) if t.strip()]
        company_text = (job.get("company") or "").lower()
        if any(t in company_text or t in text for t in types):
            score += 20

    return min(score, 100)


def filter_and_rank(jobs: list[dict], prefs: dict, min_score: int = 20) -> list[dict]:
    """Score all jobs, filter by score and experience range, return ranked list."""
    exp_min = prefs.get("experience_min")
    exp_max = prefs.get("experience_max")
    try:
        exp_min = int(exp_min) if exp_min is not None else None
        exp_max = int(exp_max) if exp_max is not None else None
    except (ValueError, TypeError):
        exp_min = exp_max = None

    scored = []
    for job in jobs:
        s = score_job(job, prefs)
        if s < min_score:
            continue

        # Experience filter — skip jobs that require more years than our max
        if exp_max is not None:
            desc = (job.get("description") or "").lower()
            title = (job.get("title") or "").lower()
            yrs = _extract_years_required(desc) or _extract_years_required(title)
            if yrs is not None and yrs > exp_max:
                continue

        scored.append({**job, "score": s})

    scored.sort(key=lambda j: j["score"], reverse=True)
    return scored
