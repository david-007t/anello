"""
jobs.py — Fetch jobs from Adzuna API based on user preferences.
"""
import os
import httpx
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_API_KEY = os.environ.get("ADZUNA_API_KEY", "")
ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"


def _fetch_for_role(role: str, location: str, min_salary, max_results: int) -> list[dict]:
    """Fetch jobs for a single role."""
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        return []

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
        url = f"{ADZUNA_BASE}/us/search/1"
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
        logger.error(f"Adzuna fetch failed for role='{role}': {e}")
        return []


def fetch_jobs(prefs: dict, max_results: int = 20) -> list[dict]:
    """
    Fetch jobs matching user preferences from Adzuna.
    Supports up to 3 roles (role, role_2, role_3) fetched in parallel.
    """
    roles = [
        prefs.get("role", ""),
        prefs.get("role_2", ""),
        prefs.get("role_3", ""),
    ]
    roles = [r.strip() for r in roles if r and r.strip()]

    if not roles:
        logger.warning("No roles set in preferences")
        return []

    location = prefs.get("location", "")
    min_salary = prefs.get("min_salary")
    per_role = max(max_results // len(roles), 10)

    all_jobs: list[dict] = []
    seen_urls: set[str] = set()

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_fetch_for_role, role, location, min_salary, per_role): role
            for role in roles
        }
        for future in as_completed(futures):
            for job in future.result():
                url = job.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_jobs.append(job)

    logger.info(f"Total unique jobs fetched: {len(all_jobs)} across {len(roles)} role(s)")
    return all_jobs
