"""
jobs.py — Fetch jobs from Adzuna and JSearch (RapidAPI) in parallel.

JSearch returns direct employer ATS URLs (Greenhouse, Lever, etc.) which
enables auto-apply. Adzuna is kept as a supplementary source.
"""
import os
import httpx
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_API_KEY = os.environ.get("ADZUNA_API_KEY", "")
ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
JSEARCH_BASE = "https://jsearch.p.rapidapi.com/search"


def _fetch_adzuna_for_role(role: str, location: str, min_salary, max_results: int) -> list[dict]:
    """Fetch jobs for a single role from Adzuna."""
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
        logger.info(f"[adzuna] Fetched {len(jobs)} jobs for role='{role}'")
        return jobs
    except Exception as e:
        logger.error(f"[adzuna] Fetch failed for role='{role}': {e}")
        return []


def _fetch_jsearch_for_role(role: str, location: str, min_salary, max_results: int) -> list[dict]:
    """Fetch jobs for a single role from JSearch (RapidAPI).

    JSearch aggregates LinkedIn, Indeed, Glassdoor, ZipRecruiter and returns
    direct employer apply links — no aggregator redirect page.
    """
    if not RAPIDAPI_KEY:
        return []

    is_remote = (location or "").lower() == "remote"
    query = f"{role} remote" if is_remote else (f"{role} in {location}" if location else role)

    params = {
        "query": query,
        "num_pages": "1",
        "date_posted": "week",
    }
    if is_remote:
        params["remote_jobs_only"] = "true"

    try:
        resp = httpx.get(
            JSEARCH_BASE,
            params=params,
            headers={
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        jobs = []
        for r in data.get("data", [])[:max_results]:
            city = r.get("job_city") or ""
            state = r.get("job_state") or ""
            country = r.get("job_country") or ""
            loc_parts = [p for p in [city, state, country] if p]
            location_str = ", ".join(loc_parts) if loc_parts else "Remote"

            salary_min = r.get("job_min_salary")
            salary_max = r.get("job_max_salary")

            apply_url = r.get("job_apply_link") or r.get("job_google_link") or ""

            jobs.append({
                "title": r.get("job_title", ""),
                "company": r.get("employer_name", ""),
                "location": location_str,
                "url": apply_url,
                "description": r.get("job_description", "")[:3000],
                "salary_min": salary_min,
                "salary_max": salary_max,
                "source": "jsearch",
            })
        logger.info(f"[jsearch] Fetched {len(jobs)} jobs for role='{role}'")
        return jobs
    except Exception as e:
        logger.error(f"[jsearch] Fetch failed for role='{role}': {e}")
        return []


def fetch_jobs(prefs: dict, max_results: int = 20) -> list[dict]:
    """
    Fetch jobs matching user preferences from Adzuna and JSearch in parallel.
    Supports up to 3 roles. Deduplicates by URL across all sources.
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

    # Build tasks for both sources × all roles
    tasks = []
    for role in roles:
        tasks.append((_fetch_adzuna_for_role, role, location, min_salary, per_role))
        tasks.append((_fetch_jsearch_for_role, role, location, min_salary, per_role))

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(fn, role, loc, sal, n): (fn.__name__, role)
            for fn, role, loc, sal, n in tasks
        }
        for future in as_completed(futures):
            try:
                for job in future.result():
                    url = job.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_jobs.append(job)
            except Exception as e:
                logger.error(f"Job fetch task failed: {e}")

    logger.info(f"Total unique jobs fetched: {len(all_jobs)} across {len(roles)} role(s) from Adzuna + JSearch")
    return all_jobs
