#!/usr/bin/env python3
"""
Component 1 — Daily Job Digest

Triggered on login via launchd. Searches Indeed, Dice, and LinkedIn for
matching roles, scores each against David's resume, pulls recent recruiter
emails, formats a digest, sends it to ddoseitutu@gmail.com, and logs all
jobs to the Job Tracker Google Sheet.
"""

import os
import re
import json
import math
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
from datetime import date
from pathlib import Path

import anthropic
from jobspy import scrape_jobs
from dotenv import load_dotenv

from urllib.parse import quote as _url_encode

from resume_context import get_resume_text, JOB_CRITERIA, IDENTITY
from gmail_client import get_gmail_service, get_recent_recruiter_emails, send_email
from sheets_logger import log_jobs, get_existing_job_keys

load_dotenv(override=True)
_LOG_DIR = Path(os.path.expanduser("~/anelo/logs"))
_LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(_LOG_DIR / "digest.log"),
        logging.StreamHandler(),   # also print to stdout
    ],
)
log = logging.getLogger(__name__)

SEARCH_TERMS_INDEED = [
    "Technical Product Manager remote",
    "Product Manager remote",
    "Product Manager data technology remote",
    "Operations Manager remote",
    "Data Engineer remote",
    "Senior Data Engineer remote",
    "Data Engineering Manager remote",
]
SEARCH_TERMS_LINKEDIN = [
    "Technical Product Manager",
    "Product Manager",
    "Product Manager data",
    "Operations Manager",
    "Data Engineer",
    "Senior Data Engineer",
    "Data Engineering Manager",
]
# Priority 1: TPM/PM (main targets), Priority 2: Ops Manager, Priority 3: Data Engineering
TPM_PM_KEYWORDS = ["product manager", "technical product manager", "tpm", " pm "]
OPS_MANAGER_KEYWORDS = ["operations manager", "operations management"]
NEGATIVE_TITLE_KEYWORDS = [k.lower() for k in JOB_CRITERIA["keywords_negative"]]
LOCAL_NEGATIVE_TITLE_KEYWORDS = [
    "h&s", "health & safety", "health and safety",
    "facilities", "facility operations",
    "mechanical test", "environmental",
    "mortgage", "insurance", "sales enablement",
    "embedded firmware", "optical", "satellite", "avionics", "aerospace systems",
]
POSITIVE_TITLE_KEYWORDS = [
    "product manager", "technical product manager", "tpm", "technical program manager",
    "program manager", "operations manager", "software engineer", "engineering manager",
    "data engineer", "data analyst", "data scientist", "machine learning", "ml engineer",
    "analytics engineer",
]
MAX_SALARY_CUTOFF = 120_000  # filter if max listed salary is explicitly below this
MIN_SALARY_CEILING = 200_000 # filter if min listed salary is above this (overqualified)
MAX_YEARS_EXPERIENCE = 4     # filter if job requires 5+ years (per user preference)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_nan(v) -> bool:
    try:
        return math.isnan(float(v))
    except (TypeError, ValueError):
        return False


# ── URL-based de-duplication cache ────────────────────────────────────────────

SEEN_JOBS_PATH = Path(__file__).parent / "seen_jobs.json"


def load_seen_jobs() -> dict:
    """Load dict of seen job URLs (url -> timestamp) from cache."""
    if SEEN_JOBS_PATH.exists():
        try:
            with open(SEEN_JOBS_PATH) as f:
                data = json.load(f)
            # Only keep jobs seen in last 30 days
            cutoff = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
            fresh = {url: ts for url, ts in data.items() if ts > cutoff}
            return fresh
        except Exception:
            return {}
    return {}


def save_seen_jobs(seen: dict):
    """Save seen jobs cache."""
    try:
        with open(SEEN_JOBS_PATH, "w") as f:
            json.dump(seen, f, indent=2)
    except Exception as e:
        log.warning(f"Could not save seen_jobs: {e}")


def mark_job_seen(seen: dict, url: str):
    """Mark a job URL as seen with current timestamp."""
    seen[url] = datetime.datetime.now().isoformat()


# Shared Playwright browser config — used by digest and validate
_PLAYWRIGHT_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-infobars",
]
_PLAYWRIGHT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _playwright_verify_linkedin_jobs(qualified: list, near_misses: list, cookies: dict) -> tuple:
    """
    Open ONE browser, visit each qualified LinkedIn job page, and:
    1. Run _experience_filter on the FULL page text (catches requirements LinkedIn hides from jobspy)
    2. Fill missing salary from page text while we're there
    Returns updated (qualified, near_misses).
    """
    linkedin_jobs = [j for j in qualified if j.get("source") == "LinkedIn"]
    other_jobs   = [j for j in qualified if j.get("source") != "LinkedIn"]

    if not linkedin_jobs:
        return qualified, near_misses

    log.info(f"Playwright verify: checking {len(linkedin_jobs)} LinkedIn jobs for full-page requirements...")
    verified, failed = [], []
    _cookie_expiry_alerted = False

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=_PLAYWRIGHT_LAUNCH_ARGS)
            ctx = browser.new_context(
                user_agent=_PLAYWRIGHT_UA,
                extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            )

            for j in linkedin_jobs:
                try:
                    page = ctx.new_page()
                    page.goto(j["link"], timeout=25000, wait_until="domcontentloaded")
                    idx = linkedin_jobs.index(j) + 1
                    print(f"  [Playwright {idx}/{len(linkedin_jobs)}] {j['title'][:40]} @ {j['company']}", flush=True)
                    # Wait for job description to render (requirements section loads via JS)
                    try:
                        page.wait_for_selector(
                            ".jobs-description, .job-details, [class*='description'], "
                            ".job-view-layout, [class*='job-view']",
                            timeout=7000,
                        )
                    except Exception:
                        pass
                    page.wait_for_timeout(2000)  # 2s sufficient; was 5s causing timeout on large batches
                    text = page.inner_text("body")
                    page.close()

                    # Detect login wall — check for ABSENCE of job content
                    job_content_markers = ["responsibilities", "requirements", "qualifications", "experience", "what you'll do", "about the role", "about this role", "job description"]
                    has_job_content = any(marker in text.lower() for marker in job_content_markers)
                    if not has_job_content:
                        if not _cookie_expiry_alerted:
                            _cookie_expiry_alerted = True
                            topic = os.getenv("NTFY_TOPIC", "david-jobs-x7k2")
                            try:
                                import requests as _req
                                _req.post(f"https://ntfy.sh/{topic}", data="LinkedIn login wall detected (no cookies mode)".encode(), headers={"Title": "⚠️ Anelo: LinkedIn Login Wall", "Priority": "high", "Tags": "warning"}, timeout=5)
                            except Exception:
                                pass
                            log.warning("LinkedIn login wall detected (no cookies mode) — Playwright skipping verification. Ntfy alert sent.")
                        # Re-run experience filter on the jobspy description we already have
                        fallback_exp = _experience_filter(j.get("description_full", ""))
                        if fallback_exp:
                            log.info(f"Login-wall fallback caught: {fallback_exp} — {j['title']} @ {j['company']}")
                            j["filter_reason"] = f"{fallback_exp} (jobspy description)"
                            failed.append(j)
                        else:
                            j["score_reason"] = "⚠️ Unverified — could not load page"
                            verified.append(j)
                        continue

                    # Full-page experience check — always run on the complete Playwright text
                    # (catches requirements that LinkedIn hides from jobspy descriptions)
                    exp_reason = _experience_filter(text)
                    if exp_reason:
                        log.info(f"Playwright caught: {exp_reason} — {j['title']} @ {j['company']}")
                        j["filter_reason"] = f"{exp_reason} (full-page scan)"
                        failed.append(j)
                        continue

                    # Opportunistically fill missing salary — use large limit since
                    # authenticated LinkedIn pages have nav/sidebar before job content
                    if j.get("salary") == "Not listed":
                        min_s, max_s = _parse_salary_from_description(text, limit=10000)
                        if min_s:
                            j["salary"] = _salary_str(min_s, max_s)
                            j["min_salary_raw"] = min_s
                            j["max_salary_raw"] = max_s
                            score, median, reason = _salary_score(min_s, max_s)
                            j["relevance_score"] = score
                            j["salary_median"] = median
                            j["score_reason"] = reason

                    verified.append(j)

                except Exception as e:
                    log.info(f"Playwright page visit failed for {j['title']}: {e}")
                    try:
                        page.close()
                    except Exception:
                        pass
                    # Re-run experience filter on jobspy description before passing through
                    fallback_exp = _experience_filter(j.get("description_full", ""))
                    if fallback_exp:
                        log.info(f"Exception fallback caught: {fallback_exp} — {j['title']} @ {j['company']}")
                        j["filter_reason"] = f"{fallback_exp} (jobspy description)"
                        failed.append(j)
                    else:
                        j["score_reason"] = "⚠️ Unverified — could not load page"
                        verified.append(j)  # include but flag as unverified

            browser.close()

    except Exception as e:
        log.error(f"Playwright batch verify error: {e}")
        return qualified, near_misses   # fall back to unverified list on hard failure

    near_misses.extend(failed)
    log.info(f"Playwright verify: {len(verified)} passed, {len(failed)} removed.")
    return other_jobs + verified, near_misses


def _load_linkedin_cookies() -> dict:
    session_path = os.path.expanduser("~/anelo/linkedin_session/state.json")
    try:
        with open(session_path) as f:
            state = json.load(f)
        # Load ALL linkedin.com cookies — not just li_at/JSESSIONID.
        # bcookie, bscookie, etc. are required to avoid redirect loops in headless Playwright.
        return {
            c["name"]: c["value"]
            for c in state.get("cookies", [])
            if "linkedin.com" in c.get("domain", "")
        }
    except Exception:
        return {}


def _salary_str(min_s, max_s) -> str:
    parts = []
    if min_s and not _is_nan(min_s):
        parts.append(f"${int(float(min_s)):,}")
    if max_s and not _is_nan(max_s):
        parts.append(f"${int(float(max_s)):,}")
    return " – ".join(parts) if parts else "Not listed"


def _parse_salary_from_description(text: str, limit: int = 2500) -> tuple:
    """
    Extract (min, max) annual salary from job page text.
    - Strips LinkedIn 'Salary Insights' sections (market averages) before parsing
    - `limit` controls how many chars to search (default 2500 for jobspy descriptions;
      use 10000 for Playwright full-page text where nav pushes salary badge further down)
    - Converts hourly rates to annual (× 2080)
    Returns (min_float, max_float) or (None, None).
    """
    # Strip LinkedIn salary insights sections which show market averages, not job salary
    for marker in ("salary insights", "how your salary compares", "similar jobs"):
        idx = text.lower().find(marker)
        if idx != -1:
            text = text[:idx]

    text = text[:limit].replace("\u2013", "-").replace("\u2014", "-")

    # Hourly range: "$50/hr - $60/hr" or "$50-$60/hr"
    hourly = re.search(
        r'\$(\d{2,3}(?:\.\d+)?)\s*/\s*hr(?:our)?(?:\s*[-–to]+\s*\$(\d{2,3}(?:\.\d+)?)\s*/\s*hr(?:our)?)?',
        text, re.IGNORECASE
    )
    if hourly:
        mn = float(hourly.group(1)) * 2080
        mx = float(hourly.group(2)) * 2080 if hourly.group(2) else mn
        if 30_000 < mn < 500_000:
            return mn, mx

    # Annual range: $118K-$148K or $118,000-$148,000
    annual_patterns = [
        r'\$(\d{2,3}(?:\.\d)?)[Kk](?:/yr(?:ear)?)?(?:\s*[-–to]+\s*)\$(\d{2,3}(?:\.\d)?)[Kk]',
        r'\$(\d{3},\d{3})(?:/y(?:r|ear))?(?:\s*[-–to]+\s*)\$(\d{3},\d{3})',
        r'\$(\d{2,3}(?:\.\d)?)[Kk]\s+(?:to|-)\s+\$(\d{2,3}(?:\.\d)?)[Kk]',
        # "150,000 - 180,000" or "150000 to 180000" (no $ sign)
        r'(\d{3},\d{3})\s*(?:[-–to]+)\s*(\d{3},\d{3})(?:\s*(?:USD|per\s+year|annually))?',
    ]
    for pat in annual_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw_min = m.group(1).replace(',', '')
            raw_max = m.group(2).replace(',', '')
            mn = float(raw_min) * (1000 if float(raw_min) < 1000 else 1)
            mx = float(raw_max) * (1000 if float(raw_max) < 1000 else 1)
            if 30_000 < mn < 2_000_000 and mn <= mx:
                return mn, mx

    # Single-value patterns: base salary / USD formats
    single_value_patterns = [
        r'[Uu]p\s+to\s+\$(\d{2,3}(?:,\d{3})?(?:\.\d)?)[Kk]?(?:\s*(?:USD|per\s+year|/yr|annually))?',
        r'(?:salary|compensation|pay)[:\s]+\$(\d{2,3}(?:\.\d)?)[Kk]',
        r'\$(\d{2,3}(?:,\d{3})?(?:\.\d)?)[Kk]?\s+annually',
        r'(?:earn|make)\s+\$(\d{2,3}(?:\.\d)?)[Kk]',
        # "Base salary: $150K" or "Salary: $150,000"
        r'(?:base\s+salary|salary|compensation)[:\s]+\$(\d{2,3}(?:\.\d)?)[Kk]',
        r'(?:base\s+salary|salary|compensation)[:\s]+\$(\d{3},\d{3})',
        # "USD 150,000" or "USD 150K"
        r'USD\s+(\d{3},\d{3})',
        r'USD\s+(\d{2,3})[Kk]',
    ]
    for pat in single_value_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(',', '')
            val = float(raw) * (1000 if float(raw) < 1000 else 1)
            if 30_000 < val < 2_000_000:
                return val, val

    # Single value: "$180K/yr", "$180K/year", "$180,000/yr", "$180,000/year"
    # Negative lookahead excludes all range separator variants (ASCII hyphen, en-dash, em-dash, space-hyphen-space)
    single = re.search(r'\$(\d{2,3}(?:\.\d)?)[Kk](?:/y(?:r|ear))?(?!\s*[-\u2013\u2014]\s*\$)', text, re.IGNORECASE)
    if not single:
        single = re.search(r'\$(\d{3},\d{3})(?:/y(?:r|ear))?(?!\s*[-\u2013\u2014]\s*\$)', text, re.IGNORECASE)
    if single:
        raw = single.group(1).replace(',', '')
        val = float(raw) * (1000 if float(raw) < 1000 else 1)
        if 30_000 < val < 2_000_000:
            return val, val

    return None, None


def _filter_reason(title: str, max_salary, min_salary=None) -> str | None:
    """Return a rejection reason string, or None if the job passes."""
    if max_salary and not _is_nan(max_salary) and float(max_salary) < MAX_SALARY_CUTOFF:
        return f"Max salary too low (${int(float(max_salary)):,})"
    if min_salary and not _is_nan(min_salary) and float(min_salary) > MIN_SALARY_CEILING:
        return f"Min salary too high (${int(float(min_salary)):,}) — overqualified"
    title_lower = title.lower()
    for k in NEGATIVE_TITLE_KEYWORDS:
        if re.search(rf'\b{re.escape(k)}\b', title_lower):
            return f"Title contains '{k}'"
    for k in LOCAL_NEGATIVE_TITLE_KEYWORDS:
        if k in title_lower:
            return f"Title contains '{k}'"
    # Filter senior/staff/principal + manager combos — too senior.
    # "Senior Data Engineer" is fine (no manager). "Data Engineering Manager" is fine (no senior/staff).
    # "Senior Product Manager", "Staff Engineering Manager" etc. → filtered.
    if re.search(r'\bmanager\b', title_lower) and re.search(r'\b(?:senior|sr\.?|staff|principal)\b', title_lower):
        return "Senior/staff manager role — out of target seniority"
    # Filter Level 4+ numeric roles — user is L2, max L3/Senior
    if re.search(r'\b(?:l\s*[45]|level\s*[-–]?\s*[45]|level\s+(?:iv|v))\b', title_lower, re.IGNORECASE):
        return "Level 4+ role (L4/L5) — above target seniority"
    # Filter staff/principal IC roles (L5+ equivalent for engineers)
    if re.search(r'\b(?:staff|principal|distinguished|fellow)\b', title_lower) and not re.search(r'\bmanager\b', title_lower):
        return "Staff/Principal IC role — above target seniority"
    # Require at least one positive keyword — blocks completely off-target roles.
    if not any(kw in title_lower for kw in POSITIVE_TITLE_KEYWORDS):
        return "Title not in target roles"
    return None  # passes


def _experience_filter(description: str) -> str | None:
    """Return rejection reason if description requires more than MAX_YEARS_EXPERIENCE."""
    patterns = [
        # "5+ years of work experience", "8+ years of SaaS product management experience"
        r'(\d+)\s*\+\s*years?\s+[\w\s]{0,60}?experience',
        # "10 years of relevant experience", "5 years of experience"
        r'(\d+)\s+years?\s+of\s+[\w\s]{0,60}?experience',
        # "at least 5 years experience", "minimum 5 years experience"
        r'(?:at\s+least|minimum\s+of?|minimum)\s+(\d+)\s+years?\s+[\w\s]{0,40}?experience',
        # "5 or more years of experience"
        r'(\d+)\s+or\s+more\s+years?\s+(?:of\s+)?(?:[\w\s]{0,60}?)experience',
        # "5 years experience" (bare)
        r'(\d+)\s+years?\s+experience\b',
        # "3-5 years of experience" — take the max
        r'\d+\s*[-–]\s*(\d+)\s+years?\s+(?:of\s+)?experience',
        # NEW: "5+ years as a data engineer", "8 years as a senior engineer"
        r'(\d+)\s*\+?\s*years?\s+as\s+a?\s+\w',
        # NEW: "8 years in software engineering", "5 years in data"
        r'(\d+)\s*\+?\s*years?\s+in\s+\w',
        # NEW: "Experience - 10+ Years", "Experience: 5+ Years"
        r'[Ee]xperience\s*[-:]\s*(\d+)\s*\+?\s*[Yy]ears?',
        # NEW: "10+ Years" or "10+ years" as a standalone bullet value
        r'^[\s•\-*]*(\d+)\s*\+\s*[Yy]ears?\s*$',
        # NEW: "minimum X years" without "experience" keyword (e.g. "minimum 5 years as...")
        r'(?:minimum|at\s+least)\s+(\d+)\s*\+?\s*years?',
        # NEW: "X-Y years in/as/of" range patterns
        r'\d+\s*[-–]\s*(\d+)\s+years?\s+(?:in|as|of)\s+\w',
    ]
    max_found = 0
    for pat in patterns:
        for m in re.finditer(pat, description, re.IGNORECASE | re.MULTILINE):
            try:
                years = int(m.group(1))
                if years > max_found:
                    max_found = years
            except (IndexError, ValueError):
                pass
    if max_found > MAX_YEARS_EXPERIENCE:
        return f"Requires {max_found}+ years experience"
    return None


def _extract_experience_phrases(description: str) -> list[str]:
    """Return all matched experience requirement phrases (for email display)."""
    patterns = [
        r'\d+\s*\+\s*years?[\w\s]{0,60}?experience',
        r'\d+\s+years?\s+of\s+[\w\s]{0,60}?experience',
        r'(?:at\s+least|minimum\s+of?|minimum)\s+\d+\s+years?[\w\s]{0,40}?experience',
        r'\d+\s+or\s+more\s+years?(?:\s+of)?(?:[\w\s]{0,60}?)experience',
        r'\d+\s+years?\s+experience\b',
        r'\d+\s*[-–]\s*\d+\s+years?\s+(?:of\s+)?experience',
        # NEW formats
        r'\d+\s*\+?\s*years?\s+as\s+a?\s+[\w\s]{0,30}',
        r'\d+\s*\+?\s*years?\s+in\s+[\w\s]{0,30}',
        r'[Ee]xperience\s*[-:]\s*\d+\s*\+?\s*[Yy]ears?',
        r'(?:minimum|at\s+least)\s+\d+\s*\+?\s*years?[\w\s]{0,30}',
        r'\d+\s*[-–]\s*\d+\s+years?\s+(?:in|as|of)\s+[\w\s]{0,30}',
    ]
    found = []
    seen = set()
    for pat in patterns:
        for m in re.finditer(pat, description, re.IGNORECASE | re.MULTILINE):
            phrase = m.group(0).strip()[:80]  # cap length
            key = phrase.lower()
            if key not in seen:
                seen.add(key)
                found.append(phrase)
    return found


def _is_explicitly_remote(row) -> bool:
    """Return True only if job is confirmed remote."""
    # jobspy sets is_remote=True when it detects remote from the source
    if row.get("is_remote") is True:
        return True
    location = str(row.get("location", "")).lower()
    title = str(row.get("title", "")).lower()
    desc = str(row.get("description", "")).lower()
    if "remote" in location or "remote" in title:
        return True
    # Any mention of "remote" in description (covers Indeed which uses location="United States")
    if "remote" in desc:
        return True
    return False


def _validate_link(url: str) -> bool:
    """Return True if URL is reachable (2xx or 3xx). False if dead.

    Indeed and LinkedIn block HEAD requests with 4xx even for valid jobs,
    so those domains are trusted unconditionally (jobspy already confirmed
    they exist). All other URLs are validated via a HEAD request.
    """
    if not url or url == "nan":
        return False
    if "indeed.com" in url or "linkedin.com" in url:
        return True
    try:
        resp = requests.head(url, timeout=5, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        return resp.status_code < 400
    except Exception:
        return False


def _validate_links_parallel(jobs: list[dict]) -> list[dict]:
    """Remove jobs with dead links. Runs HEAD checks in parallel."""
    valid = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_validate_link, j["link"]): j for j in jobs}
        for fut in as_completed(futures):
            j = futures[fut]
            if fut.result():
                valid.append(j)
            else:
                log.info(f"Dead link removed: {j['title']} @ {j['company']} — {j['link']}")
    return valid


def _job_priority(title: str) -> int:
    """1 = TPM/PM (top priority), 2 = Operations Manager, 3 = Data Engineering (fallback)."""
    t = title.lower()
    for kw in TPM_PM_KEYWORDS:
        if kw in t:
            return 1
    for kw in OPS_MANAGER_KEYWORDS:
        if kw in t:
            return 2
    return 3


def _normalize(row, source: str, li_cookies: dict = None) -> dict:
    min_s = row.get("min_amount")
    max_s = row.get("max_amount")
    interval = str(row.get("interval", "")).lower()
    description = str(row.get("description", ""))
    job_url = str(row.get("job_url", ""))
    title = str(row.get("title", "")).strip()

    # Convert hourly rates to annual
    if interval in ("hourly", "hour") and min_s and not _is_nan(min_s):
        min_s = float(min_s) * 2080
        max_s = float(max_s) * 2080 if max_s and not _is_nan(max_s) else min_s

    # Fallback: parse salary from title when jobspy found none (e.g. "Up to $100k", "$150K-$180K")
    if (not min_s or _is_nan(min_s)) and (not max_s or _is_nan(max_s)):
        title_min, title_max = _parse_salary_from_description(title, limit=len(title))
        if title_min:
            min_s = title_min
            max_s = title_max
            log.info(f"Salary parsed from title: {_salary_str(min_s, max_s)} — {title}")

    return {
        "title": title,
        "company": str(row.get("company", "")).strip(),
        "source": source,
        "link": job_url,
        "salary": _salary_str(min_s, max_s),
        "description": description[:500],
        "description_full": description,
        "min_salary_raw": min_s,
        "max_salary_raw": max_s,
        "is_easy_apply": bool(row.get("is_easy_apply")) if source == "LinkedIn" else False,
    }


# ── Job Search ────────────────────────────────────────────────────────────────

def _scrape_one_site(site: str, label: str, search_term: str, li_cookies: dict = None) -> tuple[list[dict], list[dict]]:
    """Scrape a single jobspy site with one search term, return (qualified, near_misses)."""
    try:
        kwargs = dict(
            site_name=[site],
            search_term=search_term,
            location="United States",
            results_wanted=25,
            hours_old=48,
            is_remote=True,
        )
        if site == "indeed":
            kwargs["country_indeed"] = "USA"
        if site == "linkedin":
            kwargs["linkedin_fetch_description"] = True
        df = scrape_jobs(**kwargs)
        qualified, near_misses = [], []
        for _, row in df.iterrows():
            j = _normalize(row, label, li_cookies=li_cookies if site == "linkedin" else None)

            # Remote check first
            if not _is_explicitly_remote(row):
                j["filter_reason"] = "Not confirmed remote"
                near_misses.append(j)
                continue

            # Salary + title keyword filter
            reason = _filter_reason(j["title"], j["max_salary_raw"], j.get("min_salary_raw"))
            if reason:
                j["filter_reason"] = reason
                near_misses.append(j)
                continue

            # Experience filter — use FULL description, not truncated display version
            exp_reason = _experience_filter(j["description_full"])
            if exp_reason:
                j["filter_reason"] = exp_reason
                near_misses.append(j)
                continue

            # Add priority tag
            j["priority"] = _job_priority(j["title"])
            # Store experience phrases for email visibility
            phrases = _extract_experience_phrases(j.get("description_full", ""))
            if phrases:
                j["exp_phrases"] = phrases
            qualified.append(j)

        log.info(f"{label}: {len(df)} raw → {len(qualified)} qualified, {len(near_misses)} near-misses")
        return qualified, near_misses
    except Exception as e:
        log.error(f"{label} scrape failed: {e}")
        return [], []


def search_jobspy(extra_terms: list[str] | None = None) -> tuple[list[dict], list[dict]]:
    """Scrape Indeed and LinkedIn across multiple search terms, validate links."""
    li_cookies = _load_linkedin_cookies()
    q_all, nm_all = [], []

    indeed_terms = SEARCH_TERMS_INDEED + (extra_terms or [])
    for i, term in enumerate(indeed_terms, 1):
        print(f"  [Indeed {i}/{len(indeed_terms)}] {term}...", flush=True)
        q, nm = _scrape_one_site("indeed", "Indeed", search_term=term)
        q_all.extend(q)
        nm_all.extend(nm)
    print(f"  Indeed done: {len(q_all)} qualified so far", flush=True)

    linkedin_terms = SEARCH_TERMS_LINKEDIN + (extra_terms or [])
    for i, term in enumerate(linkedin_terms, 1):
        print(f"  [LinkedIn {i}/{len(linkedin_terms)}] {term}...", flush=True)
        q, nm = _scrape_one_site("linkedin", "LinkedIn", search_term=term, li_cookies=li_cookies)
        q_all.extend(q)
        nm_all.extend(nm)
    print(f"  LinkedIn done", flush=True)

    # Validate links in parallel — drop dead ones silently
    before = len(q_all)
    q_all = _validate_links_parallel(q_all)
    dropped = before - len(q_all)
    if dropped:
        log.info(f"Link validation: removed {dropped} dead link(s).")

    # Playwright full-page verify for LinkedIn — catches hidden experience requirements
    q_all, nm_all = _playwright_verify_linkedin_jobs(q_all, nm_all, li_cookies)

    return q_all, nm_all


def search_dice() -> tuple[list[dict], list[dict]]:
    """Search Dice.com via their REST API."""
    url = "https://api.dice.com/api/rest/jobsearch/v2/simple"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Referer": "https://www.dice.com/",
        "X-API-KEY": "1YAt0R9wBg4Wb3FHFn3jMSaGGqOU3F0u",
    }
    queries = ["Technical Product Manager", "Product Manager", "Operations Manager", "Data Engineer", "Senior Data Engineer", "Data Engineering Manager"]
    qualified, near_misses = [], []

    for q in queries:
        try:
            params = {
                "text": q,
                "location": "Remote",
                "country": "US",
                "radius": "30",
                "radiusUnit": "mi",
                "page": "1",
                "pageSize": "20",
                "filters.isRemote": "true",
                "language": "en",
            }
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code != 200:
                log.warning(f"Dice returned {resp.status_code} for '{q}'")
                continue
            data = resp.json()
            for j in data.get("data", []):
                title = j.get("title", "")
                company = j.get("organization", "")
                description = j.get("jobDescription", "")
                job_url = j.get("applyUrl") or f"https://www.dice.com/job-detail/{j.get('id', '')}"
                salary_min = j.get("salary", {}).get("minimum") if j.get("salary") else None
                salary_max = j.get("salary", {}).get("maximum") if j.get("salary") else None

                entry = {
                    "title": title,
                    "company": company,
                    "source": "Dice",
                    "link": job_url,
                    "salary": _salary_str(salary_min, salary_max),
                    "description": description[:2000],
                    "min_salary_raw": salary_min,
                }
                entry["max_salary_raw"] = salary_max
                reason = _filter_reason(title, salary_max)
                if reason is None:
                    qualified.append(entry)
                else:
                    entry["filter_reason"] = reason
                    near_misses.append(entry)
        except Exception as e:
            log.warning(f"Dice search failed for '{q}': {e}")

    log.info(f"Dice: {len(qualified)} qualified, {len(near_misses)} near-misses")
    return qualified, near_misses


def search_jobs(extra_terms: list[str] | None = None) -> tuple[list[dict], list[dict]]:
    """Aggregate jobs from all sources, dedup against Sheets history. Returns (qualified, near_misses)."""
    log.info("Starting job search across all sources...")

    q1, nm1 = search_jobspy(extra_terms=extra_terms or [])
    # Dice API endpoint deprecated — returns 404 for all queries as of 2026-03
    # search_dice() kept in file for re-enablement; skipped here until a working endpoint is found
    log.info("Dice: skipped — API endpoint deprecated")

    # Dedup within this run by (title, company)
    def dedup_run(jobs):
        seen, unique = set(), []
        for j in jobs:
            key = (j["title"].lower().strip(), j["company"].lower().strip())
            if key not in seen:
                seen.add(key)
                unique.append(j)
        return unique

    qualified = dedup_run(q1)
    near_misses = dedup_run(nm1)

    # Dedup against Sheets — skip jobs already logged in past 24h (title + company only)
    try:
        existing = get_existing_job_keys(days=1)
        before = len(qualified)
        qualified = [j for j in qualified if (j["title"].lower().strip(), j["company"].lower().strip()) not in existing]
        skipped = before - len(qualified)
        if skipped:
            log.info(f"Dedup: skipped {skipped} jobs already in Sheets.")
    except Exception as e:
        log.warning(f"Sheets dedup skipped (non-fatal): {e}")

    log.info(f"Total: {len(qualified)} qualified, {len(near_misses)} near-misses")
    return qualified, near_misses


# ── Salary Scoring (no API calls — pure math) ─────────────────────────────────

def _salary_score(min_s, max_s) -> tuple[int, float, str]:
    """
    Score 1-10 based purely on salary.
    Primary sort key: median salary. Secondary: max salary.
    Returns (score, median_value, reason_string).
    """
    min_v = None if (not min_s or _is_nan(min_s)) else float(min_s)
    max_v = None if (not max_s or _is_nan(max_s)) else float(max_s)

    if min_v and max_v:
        median = (min_v + max_v) / 2
        reason = f"Median ${median/1000:.0f}k (range ${min_v/1000:.0f}k – ${max_v/1000:.0f}k)"
    elif max_v:
        median = max_v
        reason = f"Max ${max_v/1000:.0f}k listed (no min)"
    elif min_v:
        median = min_v
        reason = f"Min ${min_v/1000:.0f}k listed (no max)"
    else:
        return 5, 0.0, "Salary not listed — unknown"

    if median >= 250_000:   score = 10
    elif median >= 220_000: score = 9
    elif median >= 195_000: score = 8
    elif median >= 170_000: score = 7
    elif median >= 150_000: score = 6
    elif median >= 130_000: score = 5
    elif median >= 110_000: score = 4
    else:                   score = 3

    return score, median, reason


def score_jobs(jobs: list[dict]) -> list[dict]:
    """Score each job by salary (median primary, max secondary). No API calls."""
    for j in jobs:
        score, median, reason = _salary_score(
            j.get("min_salary_raw"), j.get("max_salary_raw")
        )
        j["relevance_score"] = score
        j["salary_median"] = median
        j["score_reason"] = reason

    # Sort: salary desc primary; role type as tiebreaker (TPM/PM=1 > Ops=2 > Data Eng=3).
    # A data engineer with higher pay ranks above a PM with lower pay.
    jobs.sort(
        key=lambda x: (
            -x["salary_median"],
            -(float(x["max_salary_raw"] or 0) if not _is_nan(x.get("max_salary_raw") or 0) else 0),
            x.get("priority", 3),
        ),
    )
    return jobs


# ── Email Digest ──────────────────────────────────────────────────────────────

SOURCE_CONFIG = [
    ("Indeed",   "#2563eb"),
    ("LinkedIn", "#0a66c2"),
]

def _job_rows_html(jobs_subset: list[dict]) -> str:
    if not jobs_subset:
        return '<tr><td colspan="3" style="padding:12px;color:#9ca3af;font-style:italic;">No results from this source today.</td></tr>'
    rows = ""
    for j in jobs_subset:
        score = j.get("relevance_score", "?")
        try:
            score_int = int(score)
        except (ValueError, TypeError):
            score_int = 0
        score_color = "#22c55e" if score_int >= 7 else "#f59e0b" if score_int >= 5 else "#ef4444"
        reason = j.get("score_reason", "")
        exp_phrases = j.get("exp_phrases", [])
        exp_html = ""
        if exp_phrases:
            phrases_joined = " | ".join(exp_phrases[:4])  # cap at 4
            exp_html = f'<div style="margin-top:4px;font-size:11px;color:#f59e0b;">⏱ {phrases_joined}</div>'
        spot_exp = j.get("spot_exp_phrases", [])
        spot_sal = j.get("spot_salary_live", "")
        spot_checked = j.get("spot_checked", False)
        spot_html = ""
        if spot_checked:
            parts = []
            if spot_exp:
                phrases_str = " | ".join(spot_exp[:4])
                parts.append(f'<span style="color:#f59e0b;">🔍 Live exp: {phrases_str}</span>')
            else:
                parts.append('<span style="color:#9ca3af;">⏱ Exp: Not explicitly stated</span>')
            if spot_sal and spot_sal != "Not listed":
                parts.append(f'<span style="color:#16a34a;">💰 Live salary: {spot_sal}</span>')
            spot_html = f'<div style="margin-top:4px;font-size:11px;">{" · ".join(parts)}</div>'

        tailor_mailto = (
            "mailto:ddoseitutu@gmail.com"
            f"?subject=TAILOR%3A%20{_url_encode(j.get('title', ''))}"
            f"%20%7C%20{_url_encode(j.get('company', ''))}"
            f"%20%7C%20row%3D{j.get('sheet_row', '')}"
            f"&body={_url_encode(j.get('link', ''))}"
        )
        tailor_link_html = (
            '<div style="margin-top:5px;">'
            f'<a href="{tailor_mailto}" style="display:inline-block;font-size:11px;'
            'color:white;background:#6366f1;border-radius:4px;padding:2px 8px;'
            'text-decoration:none;font-weight:600;">✦ Tailor Resume</a></div>'
        )

        rows += f"""
        <tr>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;">
                <a href="{j['link']}" style="color:#1d4ed8;font-weight:600;text-decoration:none;font-size:14px;">{j['title']}</a><br>
                <span style="color:#374151;font-size:13px;">{j['company']}</span>
                {"<br><span style='color:#6b7280;font-size:12px;font-style:italic;margin-top:2px;display:inline-block;'>" + reason + "</span>" if reason else ""}
                {exp_html}
                {spot_html}
                {tailor_link_html}
            </td>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;color:#374151;font-size:13px;white-space:nowrap;">{j['salary']}</td>
            <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;text-align:center;">
                <span style="background:{score_color};color:white;border-radius:12px;padding:3px 11px;font-weight:700;font-size:13px;">{score}/10</span>
            </td>
        </tr>"""
    return rows


def format_digest_html(jobs: list[dict], recruiter_emails: list[dict], near_misses: list[dict] = None, spot_stats: dict = None) -> str:
    today = date.today().strftime("%B %d, %Y")

    # Bucket jobs and near misses by source
    from collections import defaultdict
    by_source = defaultdict(list)
    nm_by_source = defaultdict(list)
    for j in jobs:
        by_source[j["source"]].append(j)
    indeed_limit = min(10, len(by_source.get("Indeed", [])))
    linkedin_limit = max(0, 10 - indeed_limit)

    source_limits = {"Indeed": indeed_limit, "LinkedIn": linkedin_limit}

    source_sections = ""
    for src_name, src_color in SOURCE_CONFIG:
        src_jobs = sorted(by_source.get(src_name, []), key=lambda x: (-x["salary_median"], x.get("priority", 2)))[:source_limits.get(src_name, 0)]
        qualified_count = len(by_source.get(src_name, []))
        count_label = f'{len(src_jobs)} of {qualified_count} found'
        body_html = f"""
        <table style="width:100%;border-collapse:collapse;margin-bottom:4px;">
            <thead><tr style="background:#f9fafb;">
                <th style="padding:7px 12px;text-align:left;font-size:12px;color:#9ca3af;">Role · Company</th>
                <th style="padding:7px 12px;text-align:left;font-size:12px;color:#9ca3af;">Salary</th>
                <th style="padding:7px 12px;text-align:center;font-size:12px;color:#9ca3af;">Score</th>
            </tr></thead>
            <tbody>{_job_rows_html(src_jobs)}</tbody>
        </table>"""
        source_sections += f"""
        <h3 style="font-size:14px;font-weight:700;margin-top:24px;margin-bottom:8px;">
            <span style="background:{src_color};color:white;border-radius:4px;padding:2px 10px;font-size:12px;">{src_name}</span>
            <span style="color:#6b7280;font-weight:400;font-size:13px;margin-left:8px;">{count_label}</span>
        </h3>
        {body_html}"""

    # Recruiter emails
    if recruiter_emails:
        emails_html = ""
        for e in recruiter_emails[:10]:
            emails_html += f"""
            <div style="border-left:3px solid #6366f1;padding:8px 12px;margin-bottom:10px;background:#f5f3ff;">
                <div style="font-weight:600;color:#1f2937;">{e['subject']}</div>
                <div style="color:#6b7280;font-size:13px;">From: {e['sender']}</div>
                <div style="color:#374151;margin-top:4px;font-size:14px;">{e['snippet']}</div>
            </div>"""
    else:
        emails_html = '<p style="color:#6b7280;">No new recruiter emails.</p>'

    src_counts = " · ".join(
        f"{s}: {len(by_source.get(s,[]))}" for s, _ in SOURCE_CONFIG if by_source.get(s)
    )

    return f"""
    <html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:720px;margin:0 auto;padding:24px;color:#1f2937;">
        <h1 style="font-size:22px;font-weight:700;margin-bottom:4px;">Job Digest — {today}</h1>
        <p style="color:#6b7280;margin-top:0;">{len(jobs)} qualified · {len(recruiter_emails)} recruiter emails</p>
        <p style="color:#9ca3af;font-size:12px;margin-top:-8px;">{src_counts}</p>

        <h2 style="font-size:16px;font-weight:700;margin-top:24px;border-bottom:2px solid #e5e7eb;padding-bottom:6px;">
            Top 10 Total (Indeed first) <span style="font-weight:400;color:#6b7280;font-size:13px;">— ranked by median salary</span>
        </h2>
        {source_sections}

        <h2 style="font-size:16px;font-weight:700;margin-top:32px;margin-bottom:12px;border-bottom:2px solid #e5e7eb;padding-bottom:6px;">Recruiter Emails</h2>
        {emails_html}

        <p style="margin-top:32px;color:#9ca3af;font-size:12px;">
            Run <code>python drafter.py</code> to draft a reply ·
            Job Tracker updated in Google Sheets
        </p>
    </body></html>
    """


# ── Pre-Send Spot Check ───────────────────────────────────────────────────────

def _spot_check(jobs: list[dict], li_cookies: dict) -> tuple:
    """
    ALWAYS runs before email is sent.
    Visits each job's live page one final time to:
      1. Catch any experience requirements still > MAX_YEARS_EXPERIENCE
      2. Fill salary from page if still "Not listed"
    Removes failures, logs every result clearly.
    Returns (clean, stats) where stats tracks pass/remove/salary counts.
    """
    stats = {
        "passed": 0,
        "removed": 0,
        "salary_filled": 0,
        "exp_caught": 0,
        "playwright_ok": True,
        "removed_details": [],
    }

    if not jobs:
        return jobs, stats

    log.info(f"=== SPOT CHECK: verifying {len(jobs)} final job(s) before send ===")
    clean, removed = [], []

    try:
        from playwright.sync_api import sync_playwright
        _session_path = os.path.expanduser("~/anelo/linkedin_session/state.json")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=_PLAYWRIGHT_LAUNCH_ARGS)
            for j in jobs:
                title   = j.get("title", "?")
                company = j.get("company", "?")
                try:
                    is_linkedin = "linkedin.com" in j.get("link", "")
                    session_state = (
                        _session_path
                        if is_linkedin and os.path.exists(_session_path)
                        else None
                    )
                    ctx = browser.new_context(
                        user_agent=_PLAYWRIGHT_UA,
                        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
                        storage_state=session_state,
                    )
                    page = ctx.new_page()
                    page.goto(j["link"], timeout=25000, wait_until="domcontentloaded")
                    try:
                        page.wait_for_selector(
                            ".jobs-description, .job-details, [class*='description'], [class*='job-view']",
                            timeout=7000,
                        )
                    except Exception:
                        pass
                    page.wait_for_timeout(2000)
                    text = page.inner_text("body")
                    page.close()
                    ctx.close()

                    # Final experience check
                    exp_reason = _experience_filter(text)
                    if exp_reason:
                        log.warning(f"SPOT CHECK FAIL — {exp_reason} — {title} @ {company}")
                        j["filter_reason"] = f"{exp_reason} (spot check)"
                        removed.append(j)
                        stats["removed"] += 1
                        stats["exp_caught"] += 1
                        stats["removed_details"].append({"title": title, "company": company, "reason": f"{exp_reason} (spot check)"})
                        continue

                    # Store experience phrases from live page for email visibility
                    live_phrases = _extract_experience_phrases(text)
                    if live_phrases:
                        j["exp_phrases"] = live_phrases  # overwrite with live page data

                    # Fill salary if still missing
                    if j.get("salary") == "Not listed":
                        min_s, max_s = _parse_salary_from_description(text, limit=10000)
                        if min_s:
                            j["salary"] = _salary_str(min_s, max_s)
                            j["min_salary_raw"] = min_s
                            j["max_salary_raw"] = max_s
                            score, median, reason = _salary_score(min_s, max_s)
                            j["relevance_score"] = score
                            j["salary_median"]   = median
                            j["score_reason"]    = reason
                            stats["salary_filled"] += 1
                            log.info(f"SPOT CHECK salary filled: {j['salary']} — {title} @ {company}")
                            # Reject if filled salary is below cutoff
                            if median < MAX_SALARY_CUTOFF:
                                filter_msg = f"Salary too low after fill (${int(median / 1000)}k)"
                                log.warning(f"SPOT CHECK FAIL — {filter_msg} — {title} @ {company}")
                                j["filter_reason"] = filter_msg
                                removed.append(j)
                                stats["removed"] += 1
                                stats["removed_details"].append({"title": title, "company": company, "reason": filter_msg})
                                continue

                    j["spot_exp_phrases"] = live_phrases
                    j["spot_salary_live"] = j.get("salary", "Not listed")
                    j["spot_checked"] = True
                    log.info(f"SPOT CHECK PASS — salary={j['salary']} — {title} @ {company}")
                    clean.append(j)
                    stats["passed"] += 1

                except Exception as e:
                    log.warning(f"SPOT CHECK page load failed for '{title}' @ {company} — checking scraped description: {e}")
                    try: page.close()
                    except Exception: pass
                    try: ctx.close()
                    except Exception: pass
                    # Fall back to scraped description for experience check
                    fallback_text = j.get("description", "") or ""
                    exp_reason = _experience_filter(fallback_text)
                    if exp_reason:
                        log.warning(f"SPOT CHECK FAIL (fallback) — {exp_reason} — {title} @ {company}")
                        j["filter_reason"] = f"{exp_reason} (spot check fallback)"
                        removed.append(j)
                        stats["removed"] += 1
                        stats["exp_caught"] += 1
                        stats["removed_details"].append({"title": title, "company": company, "reason": f"{exp_reason} (spot check fallback)"})
                    else:
                        j["spot_exp_phrases"] = _extract_experience_phrases(fallback_text)
                        j["spot_salary_live"] = j.get("salary", "Not listed")
                        j["spot_checked"] = True
                        clean.append(j)
                        stats["passed"] += 1

            browser.close()

    except Exception as e:
        log.error(f"SPOT CHECK playwright error: {e} — skipping spot check, sending as-is")
        stats["playwright_ok"] = False
        return jobs, stats

    log.info(f"=== SPOT CHECK done: {len(clean)} clean, {len(removed)} removed ===")
    return clean, stats


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import argparse as _ap
    _parser = _ap.ArgumentParser(add_help=False)
    _parser.add_argument("--extra-terms", action="append", default=[], dest="extra_terms")
    _args, _ = _parser.parse_known_args()
    extra_terms = _args.extra_terms
    if extra_terms:
        print(f"  Extra search terms: {extra_terms}", flush=True)

    log.info("=== Digest started ===")
    print("  Searching jobs across all sources...", flush=True)

    jobs, near_misses = search_jobs(extra_terms=extra_terms)
    print(f"  Found {len(jobs)} qualified jobs, scoring...", flush=True)
    scored_jobs = score_jobs(jobs)

    # Only spot-check the top 20 jobs (those the user will see in the email)
    SPOT_CHECK_LIMIT = 20
    print(f"  Scoring complete. Running spot check on top {min(SPOT_CHECK_LIMIT, len(scored_jobs))} jobs...", flush=True)
    top_jobs = scored_jobs[:SPOT_CHECK_LIMIT]
    remainder = scored_jobs[SPOT_CHECK_LIMIT:]

    li_cookies = _load_linkedin_cookies()
    top_jobs, spot_stats = _spot_check(top_jobs, li_cookies)
    print(f"  Spot check done. Logging to Sheets...", flush=True)

    if not spot_stats.get("playwright_ok"):
        log.error("ABORT: Playwright failed entirely — email not sent.")
        return

    # Recombine: spot-checked top jobs + remainder (all get logged to Sheets)
    all_jobs_for_sheet = top_jobs + remainder

    # URL-based de-duplication (fast first-pass filter before Sheets logging)
    seen_jobs = load_seen_jobs()
    skipped_count = 0
    new_jobs_for_sheet = []
    for j in all_jobs_for_sheet:
        job_url = j.get("link", "")
        if job_url and job_url in seen_jobs:
            log.debug(f"Skipping already-seen job: {j.get('title')} ({job_url[:60]})")
            skipped_count += 1
            continue
        mark_job_seen(seen_jobs, job_url)
        new_jobs_for_sheet.append(j)
    save_seen_jobs(seen_jobs)
    if skipped_count:
        log.info(f"URL dedup: skipped {skipped_count} already-seen job(s).")

    sheet_jobs = [{
        "title": j["title"],
        "company": j["company"],
        "source": j["source"],
        "link": j["link"],
        "salary": j["salary"],
        "relevance_score": j["relevance_score"],
        "remote": "Yes",
        "status": "New",
        "notes": j.get("score_reason", ""),
        "easy_apply": j.get("is_easy_apply", False),
    } for j in new_jobs_for_sheet]

    try:
        log_jobs(sheet_jobs)
    except Exception as e:
        log.error(f"Sheets logging failed: {e}")
    print(f"  Logged {len(sheet_jobs)} jobs to Sheets. Sending digest email...", flush=True)

    try:
        gmail = get_gmail_service()
        recruiter_emails = get_recent_recruiter_emails(gmail, hours=24)
    except Exception as e:
        log.error(f"Gmail fetch failed: {e}")
        recruiter_emails = []

    # Email only contains the spot-checked top jobs
    email_jobs = top_jobs
    try:
        html = format_digest_html(email_jobs, recruiter_emails, spot_stats=spot_stats)
        send_email(
            gmail,
            to=os.getenv("DIGEST_TO", "ddoseitutu@gmail.com"),
            subject=f"Job Digest — {date.today().strftime('%b %d')} ({len(email_jobs)} jobs)",
            html_body=html,
        )
        log.info(f"Digest sent. {len(email_jobs)} jobs in email, {len(all_jobs_for_sheet)} total logged, {len(recruiter_emails)} recruiter emails.")
        # Write timestamp so tailor_watcher knows the 60-min window is active
        import datetime as _dt
        _ts_path = os.path.expanduser("~/anelo/digest_sent_at.txt")
        os.makedirs(os.path.dirname(_ts_path), exist_ok=True)
        with open(_ts_path, "w") as _f:
            _f.write(_dt.datetime.now().isoformat())
    except Exception as e:
        log.error(f"Email send failed: {e}")

    log.info("=== Digest complete ===")
    print(f"Done. {len(email_jobs)} jobs in email, {len(all_jobs_for_sheet)} total logged, digest sent.")


if __name__ == "__main__":
    main()
