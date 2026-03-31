"""
jobs.py — Fetch jobs from Adzuna API based on user preferences.
Sign up free at: https://developer.adzuna.com/
"""
import os
import httpx
import logging

logger = logging.getLogger(__name__)

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_API_KEY = os.environ.get("ADZUNA_API_KEY", "")
ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"


def fetch_jobs(prefs: dict, max_results: int = 20) -> list[dict]:
    """
    Fetch jobs matching user preferences from Adzuna.
    prefs keys: role, location, min_salary, skills
    """
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        logger.error("Missing ADZUNA_APP_ID or ADZUNA_API_KEY")
        return []

    role = prefs.get("role", "software engineer")
    location = prefs.get("location", "")
    min_salary = prefs.get("min_salary")
    country = "us"  # default — can extend later

    # Adzuna "where" is geographic — "Remote" is not a valid location.
    # For remote searches, append "remote" to the keyword query instead.
    is_remote = location.lower() == "remote" if location else False
    what_query = f"{role} remote" if is_remote else role

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "results_per_page": min(max_results, 50),
        "what": what_query,
        "content-type": "application/json",
    }

    if location and not is_remote:
        params["where"] = location
    if min_salary:
        try:
            params["salary_min"] = int(min_salary)
        except (ValueError, TypeError):
            pass

    try:
        url = f"{ADZUNA_BASE}/{country}/search/1"
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        jobs = []
        for r in data.get("results", []):
            jobs.append({
                "title": r.get("title", ""),
                "company": r.get("company", {}).get("display_name", ""),
                "location": r.get("location", {}).get("display_name", ""),
                "url": r.get("redirect_url", ""),
                "description": r.get("description", ""),
                "salary_min": r.get("salary_min"),
                "salary_max": r.get("salary_max"),
                "source": "adzuna",
            })

        logger.info(f"Fetched {len(jobs)} jobs for role='{role}' location='{location}'")
        return jobs

    except Exception as e:
        logger.error(f"Adzuna fetch failed: {e}")
        return []
