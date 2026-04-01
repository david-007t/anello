"""
apply.py — Easy Apply automation via Playwright for Greenhouse and Lever ATS.

Exports:
  detect_ats(url) -> str
  apply_to_job(job, applicant, resume_path, cover_letter_path) -> dict
"""
import base64
import logging
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def detect_ats(url: str) -> str:
    """Returns 'greenhouse' | 'lever' | 'ashby' | 'workable' | 'workday' | 'unknown'"""
    if not url:
        return "unknown"
    url_lower = url.lower()
    if "boards.greenhouse.io" in url_lower or "greenhouse.io/jobs" in url_lower:
        return "greenhouse"
    if "jobs.lever.co" in url_lower:
        return "lever"
    if "jobs.ashby.com" in url_lower:
        return "ashby"
    if "apply.workable.com" in url_lower:
        return "workable"
    if ".myworkdayjobs.com" in url_lower or "workday.com" in url_lower:
        return "workday"
    if "teamtailor.com" in url_lower:
        return "teamtailor"
    return "unknown"


def _screenshot_b64(page) -> str:
    """Capture a screenshot and return it as a base64-encoded PNG string."""
    try:
        png_bytes = page.screenshot(full_page=False)
        return base64.b64encode(png_bytes).decode("utf-8")
    except Exception:
        return ""


def _apply_greenhouse(page, job: dict, applicant: dict, resume_path: str, cover_letter_path: str) -> dict:
    url = job.get("url", job.get("apply_url", ""))
    ats = "greenhouse"

    try:
        page.goto(url, timeout=30000)
        page.wait_for_timeout(1000)

        # Click "Apply for this Job" or similar apply button
        apply_selectors = [
            "a[href*='application']",
            "a[href*='apply']",
            "button:has-text('Apply for this Job')",
            "button:has-text('Apply Now')",
            "button:has-text('Apply')",
            "a:has-text('Apply for this Job')",
            "a:has-text('Apply Now')",
            "a:has-text('Apply')",
        ]
        clicked = False
        for sel in apply_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            # May already be on the application form
            logger.info("Greenhouse: no apply button found — assuming already on form")

        page.wait_for_timeout(1500)

        # Fill first name
        for sel in ["input[name*='first_name']", "input[id*='first_name']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.fill(applicant["first_name"])
                    page.wait_for_timeout(500)
                    break
            except Exception:
                continue

        # Fill last name
        for sel in ["input[name*='last_name']", "input[id*='last_name']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.fill(applicant["last_name"])
                    page.wait_for_timeout(500)
                    break
            except Exception:
                continue

        # Fill email
        try:
            el = page.locator("input[type='email']").first
            if el.is_visible(timeout=2000):
                el.fill(applicant["email"])
                page.wait_for_timeout(500)
        except Exception:
            pass

        # Fill phone
        for sel in ["input[type='tel']", "input[name*='phone']", "input[id*='phone']"]:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.fill(applicant.get("phone", ""))
                    page.wait_for_timeout(500)
                    break
            except Exception:
                continue

        # Fill LinkedIn URL if field present
        if applicant.get("linkedin_url"):
            for sel in ["input[name*='linkedin']", "input[id*='linkedin']", "input[placeholder*='linkedin' i]"]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=1000):
                        el.fill(applicant["linkedin_url"])
                        page.wait_for_timeout(500)
                        break
                except Exception:
                    continue

        # Upload resume (first file input)
        file_inputs = page.locator("input[type='file']")
        count = file_inputs.count()
        if count >= 1 and resume_path:
            try:
                file_inputs.nth(0).set_input_files(resume_path)
                page.wait_for_timeout(1000)
            except Exception as e:
                logger.warning(f"Greenhouse: resume upload failed: {e}")

        # Upload cover letter (second file input if available)
        if cover_letter_path and count >= 2:
            try:
                file_inputs.nth(1).set_input_files(cover_letter_path)
                page.wait_for_timeout(1000)
            except Exception as e:
                logger.warning(f"Greenhouse: cover letter upload failed: {e}")

        # Submit form
        submit_selectors = [
            "input[type='submit']",
            "button[type='submit']",
            "button:has-text('Submit Application')",
            "button:has-text('Submit')",
            "button:has-text('Send Application')",
        ]
        for sel in submit_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    break
            except Exception:
                continue

        # Wait for confirmation
        page.wait_for_timeout(3000)
        confirmation = ""
        for text in ["Thank you", "Application submitted", "application has been received", "successfully"]:
            try:
                page.wait_for_selector(f"text={text}", timeout=5000)
                confirmation = text
                break
            except Exception:
                continue

        # Also check URL change as confirmation
        if not confirmation:
            current_url = page.url
            if "confirmation" in current_url or "thank" in current_url or "success" in current_url:
                confirmation = f"Confirmation page: {current_url}"

        screenshot = _screenshot_b64(page)
        return {
            "success": bool(confirmation),
            "ats": ats,
            "confirmation": confirmation,
            "error": "" if confirmation else "No confirmation detected after submission",
            "screenshot_b64": screenshot,
        }

    except Exception as e:
        logger.error(f"Greenhouse apply error: {e}")
        screenshot = _screenshot_b64(page)
        return {
            "success": False,
            "ats": ats,
            "confirmation": "",
            "error": str(e),
            "screenshot_b64": screenshot,
        }


def _apply_lever(page, job: dict, applicant: dict, resume_path: str, cover_letter_path: str) -> dict:
    url = job.get("url", job.get("apply_url", ""))
    ats = "lever"

    try:
        page.goto(url, timeout=30000)
        page.wait_for_timeout(1000)

        # Click Apply button
        apply_selectors = [
            "a[href*='apply']",
            "button:has-text('Apply')",
            "a:has-text('Apply')",
        ]
        for sel in apply_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    break
            except Exception:
                continue

        page.wait_for_timeout(1500)

        # Lever uses name (full name) rather than separate first/last
        full_name = f"{applicant['first_name']} {applicant['last_name']}".strip()
        try:
            el = page.locator("input[name='name']").first
            if el.is_visible(timeout=2000):
                el.fill(full_name)
                page.wait_for_timeout(500)
        except Exception:
            pass

        # Email
        try:
            el = page.locator("input[name='email']").first
            if el.is_visible(timeout=2000):
                el.fill(applicant["email"])
                page.wait_for_timeout(500)
        except Exception:
            pass

        # Phone
        try:
            el = page.locator("input[name='phone']").first
            if el.is_visible(timeout=2000):
                el.fill(applicant.get("phone", ""))
                page.wait_for_timeout(500)
        except Exception:
            pass

        # LinkedIn
        if applicant.get("linkedin_url"):
            try:
                el = page.locator("input[name='urls[LinkedIn]']").first
                if el.is_visible(timeout=1000):
                    el.fill(applicant["linkedin_url"])
                    page.wait_for_timeout(500)
            except Exception:
                pass

        # Resume upload
        if resume_path:
            try:
                file_input = page.locator("input[type='file']").first
                file_input.set_input_files(resume_path)
                page.wait_for_timeout(1000)
            except Exception as e:
                logger.warning(f"Lever: resume upload failed: {e}")

        # Submit
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit Application')",
            "button:has-text('Submit')",
            "button:has-text('Apply')",
        ]
        for sel in submit_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    break
            except Exception:
                continue

        page.wait_for_timeout(3000)

        confirmation = ""
        for text in ["Thank you", "Application submitted", "application received", "successfully"]:
            try:
                page.wait_for_selector(f"text={text}", timeout=5000)
                confirmation = text
                break
            except Exception:
                continue

        if not confirmation:
            current_url = page.url
            if "confirmation" in current_url or "thank" in current_url or "success" in current_url:
                confirmation = f"Confirmation page: {current_url}"

        screenshot = _screenshot_b64(page)
        return {
            "success": bool(confirmation),
            "ats": ats,
            "confirmation": confirmation,
            "error": "" if confirmation else "No confirmation detected after submission",
            "screenshot_b64": screenshot,
        }

    except Exception as e:
        logger.error(f"Lever apply error: {e}")
        screenshot = _screenshot_b64(page)
        return {
            "success": False,
            "ats": ats,
            "confirmation": "",
            "error": str(e),
            "screenshot_b64": screenshot,
        }


def apply_to_job(
    job: dict,
    applicant: dict,
    resume_path: str,
    cover_letter_path: str = "",
) -> dict:
    """
    Attempt to apply to the job via Playwright automation.

    Returns:
        {
            "success": bool,
            "ats": str,
            "confirmation": str,
            "error": str,
            "screenshot_b64": str,
        }
    """
    url = job.get("url", job.get("apply_url", ""))

    # Pre-check: if URL already resolves to a known ATS, skip navigation overhead
    ats = detect_ats(url)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        try:
            # If ATS unknown (e.g. Adzuna job page), navigate and find employer apply link
            if ats == "unknown":
                try:
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)

                    # Try to find "Apply on company site" / "Apply now" link pointing to employer ATS
                    employer_url = None
                    apply_link_selectors = [
                        "a[data-qa='apply-button']",
                        "a[href*='greenhouse.io']",
                        "a[href*='lever.co']",
                        "a[href*='myworkdayjobs.com']",
                        "a:has-text('Apply on company site')",
                        "a:has-text('Apply on employer site')",
                        "a:has-text('Apply now')",
                        "a:has-text('Apply for this job')",
                    ]
                    for sel in apply_link_selectors:
                        try:
                            el = page.locator(sel).first
                            if el.is_visible(timeout=1500):
                                href = el.get_attribute("href") or ""
                                if href and "adzuna" not in href:
                                    employer_url = href
                                    break
                        except Exception:
                            continue

                    if employer_url:
                        resolved_url = employer_url
                    else:
                        resolved_url = page.url

                    ats = detect_ats(resolved_url)
                    job = {**job, "url": resolved_url}
                    logger.info(f"Resolved: {url[:60]}… → {resolved_url[:60]}… (ats={ats})")
                except Exception as e:
                    logger.error(f"Failed to resolve ATS for job: {e}")

            if ats == "workday":
                logger.warning(f"Workday application skipped (too complex): {url}")
                return {
                    "success": False,
                    "ats": "workday",
                    "confirmation": "",
                    "error": "Workday requires manual application — too complex for automation",
                    "screenshot_b64": "",
                }

            if ats in ("ashby", "workable"):
                logger.warning(f"{ats} automation not yet implemented: {url}")
                return {
                    "success": False,
                    "ats": ats,
                    "confirmation": "",
                    "error": f"{ats.title()} auto-apply coming soon",
                    "screenshot_b64": "",
                }

            if ats == "teamtailor":
                return {
                    "success": False,
                    "ats": "teamtailor",
                    "confirmation": "",
                    "error": "Teamtailor auto-apply not yet implemented — apply manually",
                    "screenshot_b64": "",
                }

            if ats == "unknown":
                return {
                    "success": False,
                    "ats": "unknown",
                    "confirmation": "",
                    "error": f"Unrecognized ATS after redirect resolution: {job.get('url', url)}",
                    "screenshot_b64": "",
                }

            if ats == "greenhouse":
                result = _apply_greenhouse(page, job, applicant, resume_path, cover_letter_path)
            elif ats == "lever":
                result = _apply_lever(page, job, applicant, resume_path, cover_letter_path)
            else:
                result = {
                    "success": False,
                    "ats": ats,
                    "confirmation": "",
                    "error": f"No handler for ATS: {ats}",
                    "screenshot_b64": "",
                }
        finally:
            try:
                browser.close()
            except Exception:
                pass

    return result
