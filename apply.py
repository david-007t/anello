#!/usr/bin/env python3
"""
apply.py — LinkedIn Easy Apply automation.

Reads Validated jobs from the sheet, opens each LinkedIn job page,
detects Easy Apply, fills standard fields, and submits or dry-runs.

Usage:
    python apply.py                  # dry run — report what would be applied
    python apply.py --submit         # fill forms and submit
    python apply.py --min-score 8    # filter by relevance score
    python apply.py --status Validated
"""

import os
import sys
import re
import time
import random
import datetime
import argparse
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

from sheets_logger import get_sheet_jobs, update_job_status
from digest import _PLAYWRIGHT_LAUNCH_ARGS, _PLAYWRIGHT_UA
from gmail_client import get_gmail_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DAILY_CAP = 15

# Q&A audit log — one JSON line per field/question filled
_QA_LOG_PATH = Path(__file__).parent / "logs" / "qa_audit.jsonl"
_QA_LOG_PATH.parent.mkdir(exist_ok=True)

def _qa_log(job_title: str, company: str, field: str, question: str, answer: str, action: str = "fill"):
    """Append one Q&A entry to the audit log."""
    entry = {
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "job": job_title,
        "company": company,
        "action": action,
        "field": field,
        "question": question,
        "answer": answer,
    }
    with open(_QA_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

_SESSION_PATH = os.path.expanduser("~/anelo/linkedin_session/state.json")


def _fill_text_if_empty(page, selector: str, value: str, job_title: str = "", company: str = "", field_name: str = ""):
    """Fill a text field only if it's currently empty."""
    try:
        el = page.query_selector(selector)
        if el and not el.input_value():
            el.fill(value)
            _qa_log(job_title, company, field_name or selector, selector, value, action="text_fill")
    except Exception:
        pass


def _answer_screening_questions(page, job_title: str = "", company: str = ""):
    """Answer common yes/no screening questions conservatively."""
    try:
        # "Are you legally authorized to work in the United States?"
        for label in page.query_selector_all("label"):
            text = label.inner_text().strip()
            text_lower = text.lower()
            if "legally authorized" in text_lower or "authorized to work" in text_lower:
                for_id = label.get_attribute("for")
                if for_id:
                    radio = page.query_selector(f"#{for_id}")
                    if radio and radio.get_attribute("value", "") in ("yes", "Yes", "true"):
                        radio.check()
                        _qa_log(job_title, company, "radio", text, "Yes", action="screening")
            if "require sponsorship" in text_lower or "visa sponsorship" in text_lower:
                for_id = label.get_attribute("for")
                if for_id:
                    radio = page.query_selector(f"#{for_id}")
                    if radio and radio.get_attribute("value", "") in ("no", "No", "false"):
                        radio.check()
                        _qa_log(job_title, company, "radio", text, "No", action="screening")
        # Also capture any visible text inputs with labels on the page
        for inp in page.query_selector_all("input[type='text'], input[type='number'], textarea"):
            try:
                val = inp.input_value()
                if not val:
                    continue
                label_el = page.query_selector(f"label[for='{inp.get_attribute('id')}']")
                label_text = label_el.inner_text().strip() if label_el else inp.get_attribute("placeholder") or inp.get_attribute("name") or "unknown"
                _qa_log(job_title, company, "input", label_text, val, action="detected_fill")
            except Exception:
                pass
    except Exception as e:
        log.debug(f"Screening questions: {e}")


def find_tailored_pdf(title: str, company: str) -> Path | None:
    """Find a tailored resume PDF for this job. Looks in tailored/ (converted PDFs)."""
    tailored_dir = Path(__file__).parent / "tailored"
    if not tailored_dir.exists():
        return None
    # Build slug the same way tailor.py does
    slug = re.sub(r'[^a-z0-9]+', '-', f"{title}-{company}".lower()).strip('-')
    slug_parts = [p for p in slug.split('-') if p]

    # Prefer resume PDFs over cover letters
    candidates = list(tailored_dir.glob("*-resume.pdf"))
    for pdf in candidates:
        stem = pdf.stem
        # Match on first 3 meaningful slug parts
        if all(part in stem for part in slug_parts[:3]):
            return pdf
    # Fallback: any partial match
    for pdf in candidates:
        if slug_parts[0] in pdf.stem and (len(slug_parts) < 2 or slug_parts[1] in pdf.stem):
            return pdf
    return None


def verify_application_gmail(title: str, company: str, applied_at: datetime.datetime, wait_seconds: int = 90) -> bool:
    """
    Check Gmail for a LinkedIn application confirmation email.
    Waits up to wait_seconds for the email to arrive, polling every 15s.
    Returns True if confirmation found, False otherwise.
    """
    log.info(f"  Waiting up to {wait_seconds}s for LinkedIn confirmation email ({company})...")
    deadline = datetime.datetime.now() + datetime.timedelta(seconds=wait_seconds)
    # after_ts: Gmail 'after' filter in epoch seconds
    after_ts = int(applied_at.timestamp()) - 60  # 1 min buffer

    try:
        svc = get_gmail_service()
    except Exception as e:
        log.warning(f"  Gmail service unavailable for verification: {e}")
        return False

    company_slug = re.sub(r'[^a-z0-9 ]', '', company.lower()).strip()
    # LinkedIn confirmation emails come from jobs-noreply@linkedin.com
    # Subject patterns: "Your application was sent to X", "Application submitted", etc.
    query = (
        f"from:linkedin.com after:{after_ts} "
        f"(subject:application OR subject:applied OR subject:\"application was sent\") "
        f"{company_slug}"
    )

    while datetime.datetime.now() < deadline:
        try:
            results = svc.users().messages().list(userId="me", q=query, maxResults=5).execute()
            msgs = results.get("messages", [])
            if msgs:
                # Grab the first match and check subject
                msg = svc.users().messages().get(userId="me", id=msgs[0]["id"], format="metadata",
                                                  metadataHeaders=["Subject", "From"]).execute()
                headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
                subject = headers.get("Subject", "")
                sender  = headers.get("From", "")
                log.info(f"  ✅ Gmail confirmed: '{subject}' from {sender}")
                return True
        except Exception as e:
            log.debug(f"  Gmail poll error (non-fatal): {e}")
        time.sleep(15)

    log.warning(f"  ⚠️  No confirmation email found for {title} @ {company} within {wait_seconds}s")
    return False


def apply_to_job(page, job: dict, submit: bool) -> str:
    """
    Attempt Easy Apply for one job. Returns outcome string.
    page: already-navigated Playwright page at the job URL.
    """
    title   = job.get("title", "?")
    company = job.get("company", "?")

    # Detect Easy Apply button
    easy_apply_btn = None
    for selector in [
        "button[aria-label*='Easy Apply']",
        "button.jobs-apply-button",
        "button:has-text('Easy Apply')",
    ]:
        try:
            btn = page.query_selector(selector)
            if btn and btn.is_visible():
                easy_apply_btn = btn
                break
        except Exception:
            pass

    if not easy_apply_btn:
        # Try to find external apply button and follow to real ATS
        try:
            ext_btn = None
            for sel in [
                "button:has-text('Apply')",
                "a:has-text('Apply on company website')",
                "a[href*='greenhouse'], a[href*='lever.co'], a[href*='dice.com']",
            ]:
                ext_btn = page.query_selector(sel)
                if ext_btn and ext_btn.is_visible():
                    break
            if ext_btn:
                # Get the href or click to a new tab to detect ATS URL
                href = ext_btn.get_attribute("href") or ""
                ats = detect_ats(href)
                if ats in ("greenhouse", "lever", "dice"):
                    return f"EXTERNAL_ATS:{ats}:{href}"
        except Exception:
            pass
        return "SKIP — no Easy Apply button (external application)"

    if not submit:
        return "DRY RUN — Easy Apply detected, would apply"

    # Click Easy Apply
    easy_apply_btn.click()
    page.wait_for_timeout(2000)

    # Navigate through modal pages (Next -> Next -> Review -> Submit)
    max_steps = 10
    for step in range(max_steps):
        # Fill phone if present
        phone = os.getenv("LINKEDIN_PHONE", "")
        if phone:
            _fill_text_if_empty(page, "input[id*='phoneNumber']", phone, title, company, "Phone Number")
            _fill_text_if_empty(page, "input[name*='phone']", phone, title, company, "Phone Number")

        # Answer screening questions
        _answer_screening_questions(page, title, company)

        # Upload tailored resume if file input is present
        tailored_pdf = find_tailored_pdf(title, company)
        file_input = page.query_selector('input[type="file"]')
        if file_input and tailored_pdf and tailored_pdf.exists():
            file_input.set_input_files(str(tailored_pdf))
            _qa_log(title, company, "file_upload", "Resume", str(tailored_pdf.name), action="upload")
            log.info(f"Uploaded tailored resume: {tailored_pdf.name}")
            time.sleep(2)

        # Look for Submit button first
        submit_btn = page.query_selector("button[aria-label='Submit application']")
        if not submit_btn:
            submit_btn = page.query_selector("button:has-text('Submit application')")
        if submit_btn and submit_btn.is_visible():
            submit_btn.click()
            page.wait_for_timeout(2000)
            _qa_log(title, company, "outcome", "Application submitted", "APPLIED", action="submit")
            return "APPLIED"

        # Look for Review button
        review_btn = page.query_selector("button[aria-label='Review your application']")
        if not review_btn:
            review_btn = page.query_selector("button:has-text('Review')")
        if review_btn and review_btn.is_visible():
            review_btn.click()
            page.wait_for_timeout(1500)
            continue

        # Look for Next button
        next_btn = page.query_selector("button[aria-label='Continue to next step']")
        if not next_btn:
            next_btn = page.query_selector("button:has-text('Next')")
        if next_btn and next_btn.is_visible():
            next_btn.click()
            page.wait_for_timeout(1500)
            continue

        # No navigation buttons found — might be done or stuck
        break

    return "WARN — reached max steps without submitting"


def detect_ats(url: str) -> str:
    """Returns 'greenhouse', 'lever', 'dice', 'linkedin', 'indeed', or 'unknown'."""
    if not url:
        return "unknown"
    url_lower = url.lower()
    if "linkedin.com" in url_lower:
        return "linkedin"
    if "boards.greenhouse.io" in url_lower or "greenhouse.io/jobs" in url_lower or "grnh.se" in url_lower:
        return "greenhouse"
    if "jobs.lever.co" in url_lower or "lever.co" in url_lower:
        return "lever"
    if "dice.com" in url_lower:
        return "dice"
    if "indeed.com" in url_lower:
        return "indeed"
    return "unknown"


def run(jobs: list[dict], submit: bool) -> list[dict]:
    """Run automated applications for all supported ATS platforms. Returns results list."""
    # Check daily cap
    today = datetime.date.today().isoformat()
    try:
        all_applied_rows = get_sheet_jobs(status="Applied", min_score=0)
        applied_today = [r for r in all_applied_rows if r.get("date", "").startswith(today)]
        if len(applied_today) >= DAILY_CAP:
            log.warning(f"Daily application cap of {DAILY_CAP} reached. Stopping.")
            return []
    except Exception as e:
        log.warning(f"Could not check daily cap (non-fatal): {e}")

    results = []

    # Bucket jobs by ATS
    ats_buckets: dict[str, list[dict]] = {
        "linkedin": [],
        "greenhouse": [],
        "lever": [],
        "dice": [],
        "indeed": [],
        "unknown": [],
    }
    for j in jobs:
        ats = detect_ats(j.get("link", ""))
        ats_buckets[ats].append(j)

    # Unknown → skip immediately
    for j in ats_buckets["unknown"]:
        results.append({**j, "outcome": "SKIP — unrecognised URL / unsupported ATS"})

    # Collect all routable jobs to process with Playwright
    routable = (
        ats_buckets["linkedin"]
        + ats_buckets["greenhouse"]
        + ats_buckets["lever"]
        + ats_buckets["dice"]
    )

    if not routable:
        return results

    try:
        from playwright.sync_api import sync_playwright
        from apply_greenhouse import apply_greenhouse
        from apply_lever import apply_lever
        from apply_dice import apply_dice

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=_PLAYWRIGHT_LAUNCH_ARGS)
            session_state = _SESSION_PATH if os.path.exists(_SESSION_PATH) else None
            ctx = browser.new_context(
                user_agent=_PLAYWRIGHT_UA,
                extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
                storage_state=session_state,
            )

            for j in routable:
                title   = j.get("title", "?")
                company = j.get("company", "?")
                url     = j.get("link", "")
                ats     = detect_ats(url)
                print(f"-> [{ats.upper()}] {title} @ {company}")

                try:
                    page = ctx.new_page()

                    applied_at = datetime.datetime.now()

                    if ats == "linkedin":
                        page.goto(url, timeout=25000, wait_until="domcontentloaded")
                        try:
                            page.wait_for_selector(
                                "button[aria-label*='Easy Apply'], button.jobs-apply-button",
                                timeout=8000,
                            )
                        except Exception:
                            pass
                        page.wait_for_timeout(2000)
                        outcome = apply_to_job(page, j, submit=submit)

                        # LinkedIn job linked to external ATS — re-route
                        if outcome.startswith("EXTERNAL_ATS:"):
                            _, ext_ats, ext_url = outcome.split(":", 2)
                            ext_job = {**j, "link": ext_url}
                            ext_page = ctx.new_page()
                            try:
                                if ext_ats == "greenhouse":
                                    outcome = apply_greenhouse(ext_page, ext_job, submit=submit)
                                elif ext_ats == "lever":
                                    outcome = apply_lever(ext_page, ext_job, submit=submit)
                                elif ext_ats == "dice":
                                    outcome = apply_dice(ext_page, ext_job, submit=submit)
                                else:
                                    outcome = f"SKIP — unsupported external ATS: {ext_ats}"
                            finally:
                                ext_page.close()

                    elif ats == "greenhouse":
                        outcome = apply_greenhouse(page, j, submit=submit)

                    elif ats == "lever":
                        outcome = apply_lever(page, j, submit=submit)

                    elif ats == "dice":
                        outcome = apply_dice(page, j, submit=submit)

                    elif ats == "indeed":
                        # Navigate Indeed job page, click Apply, follow to real ATS
                        try:
                            page.goto(url, timeout=25000, wait_until="domcontentloaded")
                            page.wait_for_timeout(2000)
                            # Find apply button
                            apply_btn = None
                            for sel in ["a#indeedApplyButton", "button[id*='apply']",
                                        "a:has-text('Apply now')", "a:has-text('Apply on company site')"]:
                                apply_btn = page.query_selector(sel)
                                if apply_btn and apply_btn.is_visible():
                                    break
                            if apply_btn:
                                href = apply_btn.get_attribute("href") or ""
                                real_ats = detect_ats(href)
                                if real_ats in ("greenhouse", "lever"):
                                    ext_job = {**j, "link": href}
                                    ext_page = ctx.new_page()
                                    try:
                                        if real_ats == "greenhouse":
                                            outcome = apply_greenhouse(ext_page, ext_job, submit=submit)
                                        else:
                                            outcome = apply_lever(ext_page, ext_job, submit=submit)
                                    finally:
                                        ext_page.close()
                                else:
                                    outcome = f"SKIP — Indeed external link not Greenhouse/Lever: {real_ats}"
                            else:
                                outcome = "SKIP — no apply button found on Indeed page"
                        except Exception as e:
                            outcome = f"ERROR — Indeed navigation: {e}"

                    else:
                        outcome = "SKIP — unrecognised ATS"

                    print(f"  {outcome}")
                    page.close()

                    # Gmail verification only for LinkedIn APPLIED submissions
                    gmail_verified = False
                    if outcome == "APPLIED" and ats == "linkedin":
                        gmail_verified = verify_application_gmail(title, company, applied_at)
                        outcome_with_verify = f"APPLIED ({'✅ email confirmed' if gmail_verified else '⚠️ no email yet'})"
                        print(f"  {outcome_with_verify}")
                    else:
                        outcome_with_verify = outcome

                    results.append({**j, "outcome": outcome_with_verify, "gmail_verified": gmail_verified})

                    # Update sheet based on outcome
                    if outcome == "APPLIED" and j.get("sheet_row"):
                        update_job_status(j["sheet_row"], "Applied")
                    elif "Easy Apply - Manual" in outcome and j.get("sheet_row"):
                        update_job_status(j["sheet_row"], "Easy Apply - Manual")
                    elif "SKIP" in outcome and j.get("sheet_row"):
                        update_job_status(j["sheet_row"], "External Apply")

                    delay = random.uniform(45, 90)
                    log.info(f"Waiting {delay:.0f}s before next application (rate limiting)...")
                    time.sleep(delay)

                except Exception as e:
                    log.error(f"Error on {title} @ {company}: {e}")
                    results.append({**j, "outcome": f"ERROR — {e}"})
                    try:
                        page.close()
                    except Exception:
                        pass

            ctx.close()
            browser.close()

    except Exception as e:
        log.error(f"Playwright init failed: {e}")
        for j in routable:
            results.append({**j, "outcome": f"ERROR — Playwright failed: {e}"})

    return results


def print_report(results: list[dict]):
    print(f"\n{'='*70}")
    print(f"{'Title':<38} {'Company':<20} {'Outcome'}")
    print(f"{'='*70}")
    for r in results:
        print(f"{r.get('title','')[:36]:<38} {r.get('company','')[:18]:<20} {r.get('outcome','')}")
    print(f"{'='*70}")
    applied   = sum(1 for r in results if "APPLIED" in r.get("outcome", ""))
    confirmed = sum(1 for r in results if r.get("gmail_verified"))
    dry_run   = sum(1 for r in results if "DRY RUN" in r.get("outcome", ""))
    skipped   = sum(1 for r in results if "SKIP" in r.get("outcome", ""))
    errors    = sum(1 for r in results if "ERROR" in r.get("outcome", ""))
    if applied:
        print(f"\nApplied: {applied}  (Gmail confirmed: {confirmed}/{applied})")
    if dry_run:
        print(f"Would apply: {dry_run}  (run with --submit to apply)")
    if skipped:
        print(f"Skipped: {skipped}")
    if errors:
        print(f"Errors: {errors}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", action="store_true", help="Actually submit applications")
    parser.add_argument("--min-score", type=int, default=7)
    parser.add_argument("--status", default="Tailored")
    args = parser.parse_args()

    mode = "SUBMIT" if args.submit else "DRY RUN"
    print(f"apply.py — mode: {mode}")
    print(f"Loading {args.status} jobs (score >= {args.min_score}) from sheet...")

    jobs = get_sheet_jobs(status=args.status, min_score=args.min_score)
    if not jobs:
        print(f"No jobs found with status={args.status} and score>={args.min_score}.")
        return

    # Show ATS breakdown before running
    from collections import Counter
    ats_counts = Counter(detect_ats(j.get("link", "")) for j in jobs)
    print(f"Found {len(jobs)} job(s) to process:")
    for ats_name, count in sorted(ats_counts.items()):
        print(f"  {ats_name}: {count}")
    print()

    results = run(jobs, submit=args.submit)
    print_report(results)


if __name__ == "__main__":
    main()
