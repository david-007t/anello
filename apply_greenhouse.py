#!/usr/bin/env python3
"""
apply_greenhouse.py — Greenhouse ATS form filler.

URL patterns: boards.greenhouse.io, greenhouse.io/jobs

Usage:
    from apply_greenhouse import apply_greenhouse
    outcome = apply_greenhouse(page, job, submit=False)
"""

import os
import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent
_FALLBACK_RESUME = _BASE_DIR / "dot_resume.pdf"


def apply_greenhouse(page, job: dict, submit: bool) -> str:
    """
    Fill a Greenhouse ATS application form.

    Returns outcome string: APPLIED, DRY RUN, SKIP, or ERROR - reason
    """
    from apply import find_tailored_pdf, _qa_log  # local import to avoid circular

    title = job.get("title", "?")
    company = job.get("company", "?")
    url = job.get("link", "")

    try:
        # ── Navigate ──────────────────────────────────────────────────────────
        log.info(f"Greenhouse: navigating to {url}")
        page.goto(url, timeout=25000, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Confirm we're on a Greenhouse page
        if "greenhouse.io" not in page.url:
            return f"SKIP — not a Greenhouse URL after redirect ({page.url})"

        if not submit:
            return "DRY RUN — Greenhouse detected, would apply"

        # ── Identity fields ───────────────────────────────────────────────────
        from resume_context import IDENTITY

        _gh_fill(page, "input#first_name", IDENTITY["first_name"], title, company, "first_name")
        _gh_fill(page, "input#last_name", IDENTITY["last_name"], title, company, "last_name")
        _gh_fill(page, "input#email", IDENTITY["email"], title, company, "email")
        _gh_fill(page, "input#phone", IDENTITY["phone"], title, company, "phone")

        # LinkedIn — several common selectors
        for linkedin_sel in [
            "input#job_application_linkedin_profile",
            "input[name*='linkedin']",
            "input[placeholder*='LinkedIn']",
            "input[id*='linkedin']",
        ]:
            if _gh_fill(page, linkedin_sel, f"https://{IDENTITY['linkedin']}", title, company, "linkedin"):
                break

        # ── Resume upload ─────────────────────────────────────────────────────
        tailored = find_tailored_pdf(title, company)
        resume_path = tailored if tailored and tailored.exists() else _FALLBACK_RESUME
        if resume_path.exists():
            for file_sel in ["input#job_application_resume", "input[type=file]"]:
                file_input = page.query_selector(file_sel)
                if file_input:
                    file_input.set_input_files(str(resume_path))
                    _qa_log(title, company, "file_upload", "Resume", resume_path.name, action="upload")
                    log.info(f"Greenhouse: uploaded {resume_path.name}")
                    time.sleep(2)
                    break

        # ── Work authorization dropdowns ──────────────────────────────────────
        _gh_work_auth(page, title, company)

        # ── Custom questions (Claude if key available) ─────────────────────────
        _gh_custom_questions(page, title, company)

        # ── Submit ────────────────────────────────────────────────────────────
        submit_btn = None
        for sel in [
            "input[type=submit]",
            "button[type=submit]",
            "button:has-text('Submit Application')",
            "button:has-text('Submit')",
            "#submit_app",
        ]:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                submit_btn = btn
                break

        if not submit_btn:
            return "ERROR — Greenhouse: submit button not found"

        submit_btn.click()
        page.wait_for_timeout(3000)
        _qa_log(title, company, "outcome", "Application submitted", "APPLIED", action="submit")
        return "APPLIED"

    except Exception as e:
        log.error(f"Greenhouse error on {title} @ {company}: {e}")
        return f"ERROR — Greenhouse: {e}"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _gh_fill(page, selector: str, value: str, job_title: str, company: str, field_name: str) -> bool:
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


def _gh_work_auth(page, title: str, company: str):
    """Handle work authorization select dropdowns."""
    try:
        from apply import _qa_log
        selects = page.query_selector_all("select")
        for sel_el in selects:
            sel_id = (sel_el.get_attribute("id") or "").lower()
            sel_name = (sel_el.get_attribute("name") or "").lower()
            combined = sel_id + " " + sel_name

            # Label-based detection
            label_text = ""
            sel_id_attr = sel_el.get_attribute("id")
            if sel_id_attr:
                lbl = page.query_selector(f"label[for='{sel_id_attr}']")
                if lbl:
                    label_text = lbl.inner_text().lower()

            combined_with_label = combined + " " + label_text

            if any(k in combined_with_label for k in ["authorized", "authorization", "work in the u", "eligible to work"]):
                # Select "Yes" option
                options = sel_el.query_selector_all("option")
                for opt in options:
                    if opt.inner_text().strip().lower() in ("yes", "yes, i am authorized"):
                        sel_el.select_option(value=opt.get_attribute("value"))
                        _qa_log(title, company, "work_auth", "work authorization", "Yes", action="select")
                        break

            if any(k in combined_with_label for k in ["sponsorship", "visa", "require sponsor"]):
                # Select "No" option
                options = sel_el.query_selector_all("option")
                for opt in options:
                    if opt.inner_text().strip().lower() in ("no", "no, i do not"):
                        sel_el.select_option(value=opt.get_attribute("value"))
                        _qa_log(title, company, "sponsorship", "visa sponsorship", "No", action="select")
                        break
    except Exception as e:
        log.debug(f"Greenhouse work auth: {e}")


def _gh_custom_questions(page, title: str, company: str):
    """Answer custom questions using Claude if ANTHROPIC_API_KEY is set, else skip."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return

    try:
        from apply import _qa_log
        from resume_context import RESUME_TEXT
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Find unanswered text areas and text inputs not already handled
        handled_ids = {"first_name", "last_name", "email", "phone"}
        inputs = page.query_selector_all("textarea, input[type=text]")

        for inp in inputs:
            try:
                inp_id = inp.get_attribute("id") or ""
                if inp_id in handled_ids:
                    continue
                if inp.input_value():
                    continue  # already filled

                # Find associated label
                label_text = ""
                if inp_id:
                    lbl = page.query_selector(f"label[for='{inp_id}']")
                    if lbl:
                        label_text = lbl.inner_text().strip()
                if not label_text:
                    label_text = inp.get_attribute("placeholder") or inp.get_attribute("aria-label") or ""
                if not label_text or len(label_text) < 5:
                    continue

                # Skip cover letter fields
                if any(k in label_text.lower() for k in ["cover letter", "coverletter"]):
                    continue

                prompt = (
                    f"You are filling out a job application for: {title} at {company}.\n"
                    f"Question: {label_text}\n\n"
                    f"Resume:\n{RESUME_TEXT}\n\n"
                    "Answer concisely (1-3 sentences max). Be direct and professional."
                )
                msg = client.messages.create(
                    model="claude-haiku-4-5",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}],
                )
                answer = msg.content[0].text.strip()
                if answer:
                    inp.fill(answer)
                    _qa_log(title, company, "custom_question", label_text, answer, action="claude_fill")
                    log.info(f"Greenhouse: Claude answered '{label_text[:50]}...'")
            except Exception as e:
                log.debug(f"Greenhouse custom question error: {e}")
    except Exception as e:
        log.debug(f"Greenhouse Claude questions skipped: {e}")
