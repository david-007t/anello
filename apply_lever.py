#!/usr/bin/env python3
"""
apply_lever.py — Lever ATS form filler.

URL patterns: jobs.lever.co

Usage:
    from apply_lever import apply_lever
    outcome = apply_lever(page, job, submit=False)
"""

import os
import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent
_FALLBACK_RESUME = _BASE_DIR / "dot_resume.pdf"


def apply_lever(page, job: dict, submit: bool) -> str:
    """
    Fill a Lever ATS application form.

    Returns outcome string: APPLIED, DRY RUN, SKIP, or ERROR - reason
    """
    from apply import find_tailored_pdf, _qa_log

    title = job.get("title", "?")
    company = job.get("company", "?")
    url = job.get("link", "")

    try:
        # ── Navigate ──────────────────────────────────────────────────────────
        log.info(f"Lever: navigating to {url}")
        page.goto(url, timeout=25000, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        if "lever.co" not in page.url:
            return f"SKIP — not a Lever URL after redirect ({page.url})"

        if not submit:
            return "DRY RUN — Lever detected, would apply"

        # ── Identity fields ───────────────────────────────────────────────────
        from resume_context import IDENTITY

        _lv_fill(page, 'input[name="name"]', IDENTITY["name"], title, company, "full_name")
        _lv_fill(page, 'input[name="email"]', IDENTITY["email"], title, company, "email")
        _lv_fill(page, 'input[name="phone"]', IDENTITY["phone"], title, company, "phone")

        # Current company — use current title as org
        _lv_fill(page, 'input[name="org"]', "Nutanix", title, company, "current_company")

        # LinkedIn
        _lv_fill(
            page,
            'input[name="urls[LinkedIn]"]',
            f"https://{IDENTITY['linkedin']}",
            title,
            company,
            "linkedin",
        )

        # ── Resume upload ─────────────────────────────────────────────────────
        tailored = find_tailored_pdf(title, company)
        resume_path = tailored if tailored and tailored.exists() else _FALLBACK_RESUME
        if resume_path.exists():
            file_input = page.query_selector('input[type=file]')
            if file_input:
                file_input.set_input_files(str(resume_path))
                _qa_log(title, company, "file_upload", "Resume", resume_path.name, action="upload")
                log.info(f"Lever: uploaded {resume_path.name}")
                time.sleep(2)

        # ── Work authorization ─────────────────────────────────────────────────
        _lv_work_auth(page, title, company)

        # ── Submit ────────────────────────────────────────────────────────────
        submit_btn = None
        for sel in [
            "button[type=submit]",
            "button:has-text('Submit Application')",
            "button:has-text('Submit')",
            ".submit-app-btn",
            "input[type=submit]",
        ]:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                submit_btn = btn
                break

        if not submit_btn:
            return "ERROR — Lever: submit button not found"

        submit_btn.click()
        page.wait_for_timeout(3000)
        _qa_log(title, company, "outcome", "Application submitted", "APPLIED", action="submit")
        return "APPLIED"

    except Exception as e:
        log.error(f"Lever error on {title} @ {company}: {e}")
        return f"ERROR — Lever: {e}"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _lv_fill(page, selector: str, value: str, job_title: str, company: str, field_name: str) -> bool:
    """Fill field only if it exists and is currently empty. Returns True on success."""
    try:
        from apply import _qa_log
        el = page.query_selector(selector)
        if el and el.is_visible():
            current = el.input_value()
            if not current:
                el.fill(value)
                _qa_log(job_title, company, field_name, selector, value, action="text_fill")
            return True
    except Exception:
        pass
    return False


def _lv_work_auth(page, title: str, company: str):
    """Handle work authorization select dropdowns and radio buttons on Lever forms."""
    try:
        from apply import _qa_log

        # Check for selects
        selects = page.query_selector_all("select")
        for sel_el in selects:
            label_text = ""
            sel_id_attr = sel_el.get_attribute("id")
            if sel_id_attr:
                lbl = page.query_selector(f"label[for='{sel_id_attr}']")
                if lbl:
                    label_text = lbl.inner_text().lower()
            combined = ((sel_el.get_attribute("name") or "") + " " + label_text).lower()

            if any(k in combined for k in ["authorized", "work in the u", "eligible to work"]):
                options = sel_el.query_selector_all("option")
                for opt in options:
                    if opt.inner_text().strip().lower() in ("yes", "yes, i am authorized"):
                        sel_el.select_option(value=opt.get_attribute("value"))
                        _qa_log(title, company, "work_auth", "work authorization", "Yes", action="select")
                        break

            if any(k in combined for k in ["sponsorship", "visa", "require sponsor"]):
                options = sel_el.query_selector_all("option")
                for opt in options:
                    if opt.inner_text().strip().lower() in ("no", "no, i do not"):
                        sel_el.select_option(value=opt.get_attribute("value"))
                        _qa_log(title, company, "sponsorship", "visa sponsorship", "No", action="select")
                        break

        # Check for radio buttons (Lever uses these for yes/no questions)
        for label in page.query_selector_all("label"):
            text = label.inner_text().strip().lower()
            if "legally authorized" in text or "authorized to work" in text:
                for_id = label.get_attribute("for")
                if for_id:
                    radio = page.query_selector(f"#{for_id}")
                    if radio and radio.get_attribute("value", "") in ("yes", "Yes", "true"):
                        radio.check()
                        _qa_log(title, company, "radio", label.inner_text().strip(), "Yes", action="screening")
            if "require sponsorship" in text or "visa sponsorship" in text:
                for_id = label.get_attribute("for")
                if for_id:
                    radio = page.query_selector(f"#{for_id}")
                    if radio and radio.get_attribute("value", "") in ("no", "No", "false"):
                        radio.check()
                        _qa_log(title, company, "radio", label.inner_text().strip(), "No", action="screening")

    except Exception as e:
        log.debug(f"Lever work auth: {e}")
