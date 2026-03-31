#!/usr/bin/env python3
"""
apply_dice.py — Dice Easy Apply automation.

URL patterns: dice.com/job-detail/, dice.com/jobs/

Usage:
    from apply_dice import apply_dice
    outcome = apply_dice(page, job, submit=False)
"""

import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent
_FALLBACK_RESUME = _BASE_DIR / "dot_resume.pdf"


def apply_dice(page, job: dict, submit: bool) -> str:
    """
    Submit a Dice Easy Apply application.

    Returns outcome string: APPLIED, DRY RUN, SKIP, or ERROR - reason
    """
    from apply import find_tailored_pdf, _qa_log

    title = job.get("title", "?")
    company = job.get("company", "?")
    url = job.get("link", "")

    try:
        # ── Navigate ──────────────────────────────────────────────────────────
        log.info(f"Dice: navigating to {url}")
        page.goto(url, timeout=25000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if "dice.com" not in page.url:
            return f"SKIP — not a Dice URL after redirect ({page.url})"

        # ── Find Easy Apply button ─────────────────────────────────────────────
        easy_apply_btn = None
        for sel in [
            'button[data-cy="apply-button"]',
            'button[data-testid="apply-button"]',
            "button:has-text('Easy Apply')",
            "button:has-text('Apply Now')",
            "a:has-text('Easy Apply')",
        ]:
            try:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    easy_apply_btn = btn
                    break
            except Exception:
                pass

        if not easy_apply_btn:
            return "SKIP — Dice: no Easy Apply button found"

        if not submit:
            return "DRY RUN — Dice Easy Apply detected, would apply"

        # ── Click Easy Apply ───────────────────────────────────────────────────
        easy_apply_btn.click()
        page.wait_for_timeout(3000)

        # ── Identity fields (modal / panel) ───────────────────────────────────
        from resume_context import IDENTITY

        # Dice may pre-fill from profile — fill only if empty
        for sel, value, field in [
            ('input[name="firstName"], input[id*="firstName"], input[placeholder*="First"]', IDENTITY["first_name"], "first_name"),
            ('input[name="lastName"], input[id*="lastName"], input[placeholder*="Last"]', IDENTITY["last_name"], "last_name"),
            ('input[name="email"], input[type="email"]', IDENTITY["email"], "email"),
            ('input[name="phone"], input[type="tel"]', IDENTITY["phone"], "phone"),
        ]:
            _dice_fill(page, sel, value, title, company, field)

        # ── Resume upload ─────────────────────────────────────────────────────
        tailored = find_tailored_pdf(title, company)
        resume_path = tailored if tailored and tailored.exists() else _FALLBACK_RESUME
        if resume_path.exists():
            file_input = page.query_selector('input[type=file]')
            if file_input:
                file_input.set_input_files(str(resume_path))
                _qa_log(title, company, "file_upload", "Resume", resume_path.name, action="upload")
                log.info(f"Dice: uploaded {resume_path.name}")
                time.sleep(2)

        # ── Work authorization ─────────────────────────────────────────────────
        _dice_work_auth(page, title, company)

        # ── Navigate multi-step modal if present ──────────────────────────────
        max_steps = 8
        for step in range(max_steps):
            # Check for final submit
            submit_btn = None
            for sel in [
                "button:has-text('Submit Application')",
                "button:has-text('Apply')",
                "button:has-text('Submit')",
                'button[data-cy="submit-button"]',
                'button[type="submit"]',
            ]:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    # Make sure it's not "Next" hidden as submit
                    btn_text = btn.inner_text().strip().lower()
                    if btn_text in ("apply", "submit", "submit application"):
                        submit_btn = btn
                        break

            if submit_btn:
                submit_btn.click()
                page.wait_for_timeout(3000)
                _qa_log(title, company, "outcome", "Application submitted", "APPLIED", action="submit")
                return "APPLIED"

            # Try Next
            next_btn = None
            for sel in [
                "button:has-text('Next')",
                "button:has-text('Continue')",
                'button[data-cy="next-button"]',
            ]:
                btn = page.query_selector(sel)
                if btn and btn.is_visible():
                    next_btn = btn
                    break

            if next_btn:
                next_btn.click()
                page.wait_for_timeout(2000)
                continue

            # No navigation buttons found
            break

        return "WARN — Dice: reached max steps without submitting"

    except Exception as e:
        log.error(f"Dice error on {title} @ {company}: {e}")
        return f"ERROR — Dice: {e}"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _dice_fill(page, selector: str, value: str, job_title: str, company: str, field_name: str) -> bool:
    """
    Try each comma-separated selector until one is found and filled.
    Returns True if any field was filled.
    """
    try:
        from apply import _qa_log
        for sel in [s.strip() for s in selector.split(",")]:
            el = page.query_selector(sel)
            if el and el.is_visible():
                current = el.input_value()
                if not current:
                    el.fill(value)
                    _qa_log(job_title, company, field_name, sel, value, action="text_fill")
                return True
    except Exception:
        pass
    return False


def _dice_work_auth(page, title: str, company: str):
    """Handle work authorization on Dice Easy Apply modal."""
    try:
        from apply import _qa_log

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

        # Selects
        selects = page.query_selector_all("select")
        for sel_el in selects:
            label_text = ""
            sel_id_attr = sel_el.get_attribute("id")
            if sel_id_attr:
                lbl = page.query_selector(f"label[for='{sel_id_attr}']")
                if lbl:
                    label_text = lbl.inner_text().lower()
            combined = ((sel_el.get_attribute("name") or "") + " " + label_text).lower()

            if any(k in combined for k in ["authorized", "work in the u", "eligible"]):
                options = sel_el.query_selector_all("option")
                for opt in options:
                    if opt.inner_text().strip().lower() in ("yes", "yes, i am authorized"):
                        sel_el.select_option(value=opt.get_attribute("value"))
                        _qa_log(title, company, "work_auth", "work authorization", "Yes", action="select")
                        break

            if any(k in combined for k in ["sponsorship", "visa"]):
                options = sel_el.query_selector_all("option")
                for opt in options:
                    if opt.inner_text().strip().lower() in ("no", "no, i do not"):
                        sel_el.select_option(value=opt.get_attribute("value"))
                        _qa_log(title, company, "sponsorship", "visa sponsorship", "No", action="select")
                        break

    except Exception as e:
        log.debug(f"Dice work auth: {e}")
