#!/usr/bin/env python3
"""
validate.py — Pre-apply validator for shortlisted jobs from Google Sheet.

Reads jobs with status="New" and score >= 7 from the Job Tracker sheet,
visits each live page with Playwright, and checks:
  1. Link is still live
  2. Experience requirements still within range
  3. Salary still acceptable

Prints a summary table and optionally updates sheet status.

Usage:
    python validate.py           # validate and print report
    python validate.py --update  # also update sheet status to Validated/Stale
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv(override=True)

from digest import (
    _validate_link,
    _experience_filter,
    _extract_experience_phrases,
    _parse_salary_from_description,
    _salary_str,
    MAX_YEARS_EXPERIENCE,
    MAX_SALARY_CUTOFF,
    _PLAYWRIGHT_LAUNCH_ARGS,
    _PLAYWRIGHT_UA,
)
from sheets_logger import get_sheet_jobs, update_job_status


def validate_jobs(jobs: list[dict]) -> list[dict]:
    """Run Playwright on each job, return list with validation results added."""
    _session_path = os.path.expanduser("~/anelo/linkedin_session/state.json")
    results = []

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=_PLAYWRIGHT_LAUNCH_ARGS)
            for j in jobs:
                title   = j.get("title", "?")
                company = j.get("company", "?")
                link    = j.get("link", "")
                result  = dict(j)
                result["link_ok"]     = _validate_link(link)
                result["exp_ok"]      = True
                result["exp_reason"]  = ""
                result["live_salary"] = j.get("salary", "Not listed")
                result["action"]      = "APPLY"

                if not result["link_ok"]:
                    result["action"] = "STALE — dead link"
                    results.append(result)
                    continue

                try:
                    is_linkedin = "linkedin.com" in link
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
                    page.goto(link, timeout=25000, wait_until="domcontentloaded")
                    try:
                        page.wait_for_selector(
                            ".jobs-description, .job-details, [class*='description'], [class*='job-view']",
                            timeout=7000,
                        )
                    except Exception:
                        pass
                    page.wait_for_timeout(4000)
                    text = page.inner_text("body")
                    page.close()
                    ctx.close()

                    # Experience check
                    exp_reason = _experience_filter(text)
                    if exp_reason:
                        result["exp_ok"]     = False
                        result["exp_reason"] = exp_reason
                        result["action"]     = f"SKIP — {exp_reason}"

                    # Live salary
                    if result["live_salary"] == "Not listed":
                        min_s, max_s = _parse_salary_from_description(text, limit=10000)
                        if min_s:
                            result["live_salary"] = _salary_str(min_s, max_s)
                            if (max_s or min_s) < MAX_SALARY_CUTOFF:
                                result["action"] = f"SKIP — salary too low ({result['live_salary']})"

                    # Exp phrases for display
                    result["exp_phrases"] = _extract_experience_phrases(text)

                except Exception as e:
                    result["action"] = f"WARN — page load failed: {e}"

                results.append(result)
            browser.close()

    except Exception as e:
        print(f"[ERROR] Playwright failed: {e}", file=sys.stderr)
        # Return with just link checks
        for j in jobs:
            r = dict(j)
            r["link_ok"]     = _validate_link(j.get("link", ""))
            r["exp_ok"]      = True
            r["exp_reason"]  = ""
            r["live_salary"] = j.get("salary", "Not listed")
            r["action"]      = "APPLY (playwright unavailable)"
            results.append(r)

    return results


def print_report(results: list[dict]):
    """Print a formatted validation table."""
    SEP = "-" * 110
    print(SEP)
    print(f"{'#':<4} {'Title':<40} {'Company':<22} {'Link':<5} {'Exp':<5} {'Live Salary':<20} {'Action'}")
    print(SEP)
    for i, r in enumerate(results, 1):
        link_icon = "✓" if r.get("link_ok") else "✗"
        exp_icon  = "✓" if r.get("exp_ok", True) else "✗"
        sal       = r.get("live_salary", "?")[:18]
        title     = r.get("title", "")[:38]
        company   = r.get("company", "")[:20]
        action    = r.get("action", "")
        print(f"{i:<4} {title:<40} {company:<22} {link_icon:<5} {exp_icon:<5} {sal:<20} {action}")
        if r.get("exp_phrases"):
            phrases = " | ".join(r["exp_phrases"][:3])
            print(f"     ⏱  {phrases}")
    print(SEP)
    apply_count = sum(1 for r in results if r.get("action", "").startswith("APPLY"))
    skip_count  = sum(1 for r in results if "SKIP" in r.get("action", ""))
    warn_count  = sum(1 for r in results if "WARN" in r.get("action", "") or "STALE" in r.get("action", ""))
    print(f"\nSummary: {apply_count} apply · {skip_count} skip · {warn_count} warn/stale  (of {len(results)} validated)")


def main():
    parser = argparse.ArgumentParser(description="Validate shortlisted jobs before applying.")
    parser.add_argument("--no-update", action="store_true", help="Preview only — do not update sheet status")
    parser.add_argument("--min-score", type=int, default=7, help="Minimum relevance score (default: 7)")
    parser.add_argument("--queue-tailor", action="store_true", help="Set approved jobs to 'Needs Tailor' instead of 'Validated' (used by pipeline)")
    args = parser.parse_args()

    print("Loading shortlisted jobs from sheet...")
    jobs = get_sheet_jobs(status="New", min_score=args.min_score)
    if not jobs:
        print(f"No jobs to validate (status=New, score>={args.min_score}).")
        return

    print(f"Validating {len(jobs)} job(s) with Playwright...\n")
    results = validate_jobs(jobs)
    print_report(results)

    if not args.no_update:
        approved_status = "Needs Tailor" if args.queue_tailor else "Validated"
        print(f"\nUpdating sheet statuses (approved → {approved_status})...")
        for r in results:
            row = r.get("sheet_row")
            if not row:
                continue
            if r.get("action", "").startswith("APPLY"):
                update_job_status(row, approved_status)
            elif "SKIP" in r.get("action", "") or "STALE" in r.get("action", ""):
                update_job_status(row, "Stale")
        print("Done.")


if __name__ == "__main__":
    main()
