#!/usr/bin/env python3
"""
tailor_watcher.py — Gmail poller that triggers tailor.py for selected jobs.

Runs every 5 minutes via launchd for 60 minutes after the daily digest sends.
Outside that window, exits immediately (no Gmail API calls).

Flow:
  1. User gets digest email with "Tailor Resume" mailto links per job
  2. User clicks link → sends self-email with subject: TAILOR: {title} | {company} | row={row}
  3. This script detects that email, updates Sheet to "Needs Tailor", runs tailor.py
"""

import os
import re
import sys
import base64
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]

load_dotenv(override=True)

from gmail_client import get_gmail_service
from sheets_logger import update_job_status, find_job_row, get_sheet_jobs

logging.basicConfig(
    filename=os.path.expanduser("~/anelo/logs/tailor_watcher.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

DIGEST_TIMESTAMP_FILE = Path(os.path.expanduser("~/anelo/digest_sent_at.txt"))
WINDOW_MINUTES = 60
SCRIPT_DIR = Path(__file__).parent


def is_within_window() -> bool:
    """Return True if digest was sent within the last WINDOW_MINUTES minutes."""
    if not DIGEST_TIMESTAMP_FILE.exists():
        return False
    try:
        sent_at = datetime.fromisoformat(DIGEST_TIMESTAMP_FILE.read_text().strip())
        return datetime.now() - sent_at < timedelta(minutes=WINDOW_MINUTES)
    except Exception:
        return False


def get_tailor_emails(gmail) -> list[dict]:
    """Search Gmail for unread TAILOR: emails. Returns list of parsed dicts."""
    try:
        result = gmail.users().messages().list(
            userId="me",
            q='subject:"TAILOR:" is:unread',
            maxResults=20,
        ).execute()
        messages = result.get("messages", [])
    except Exception as e:
        log.error(f"Gmail search failed: {e}")
        return []

    parsed = []
    for msg in messages:
        try:
            full = gmail.users().messages().get(
                userId="me", id=msg["id"], format="full"
            ).execute()
            headers = {h["name"]: h["value"] for h in full["payload"]["headers"]}
            subject = headers.get("Subject", "")

            if "TAILOR:" not in subject:
                continue
            rest = subject[subject.index("TAILOR:") + 7:].strip()
            parts = [p.strip() for p in rest.split("|")]
            title   = parts[0] if len(parts) > 0 else ""
            company = parts[1] if len(parts) > 1 else ""
            row_str = parts[2] if len(parts) > 2 else ""
            sheet_row = None
            row_match = re.search(r"row=(\d+)", row_str)
            if row_match:
                sheet_row = int(row_match.group(1))

            # Get URL from body
            url = ""
            payload = full["payload"]
            if payload.get("body", {}).get("data"):
                body_bytes = base64.urlsafe_b64decode(payload["body"]["data"])
                url = body_bytes.decode("utf-8", errors="ignore").strip()
            elif payload.get("parts"):
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        body_bytes = base64.urlsafe_b64decode(part["body"]["data"])
                        url = body_bytes.decode("utf-8", errors="ignore").strip()
                        break

            parsed.append({
                "msg_id": msg["id"],
                "title": title,
                "company": company,
                "sheet_row": sheet_row,
                "url": url,
            })
        except Exception as e:
            log.error(f"Failed to parse message {msg['id']}: {e}")

    return parsed


def mark_as_read(gmail, msg_id: str):
    """Mark a Gmail message as read so we don't process it again."""
    try:
        gmail.users().messages().modify(
            userId="me",
            id=msg_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
    except Exception as e:
        log.warning(f"Could not mark message {msg_id} as read: {e}")


def run_tailor(url: str, title: str = "", company: str = "", row: int = None) -> bool:
    """Run tailor.py --url for a single job URL. Returns True on success."""
    try:
        venv_python = str(SCRIPT_DIR / "venv" / "bin" / "python")
        if not Path(venv_python).exists():
            venv_python = sys.executable
        cmd = [venv_python, str(SCRIPT_DIR / "tailor.py"), "--url", url]
        if title:
            cmd += ["--title", title]
        if company:
            cmd += ["--company", company]
        if row is not None:
            cmd += ["--row", str(row)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(SCRIPT_DIR),
        )
        if result.returncode == 0:
            log.info(f"tailor.py succeeded for {url}")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            log.error(f"tailor.py failed for {url}: {result.stderr}")
            return False
    except Exception as e:
        log.error(f"run_tailor exception: {e}")
        return False


def run_pdf_gen(resume_path: Path, cover_path: Path) -> bool:
    """Run resume_to_pdf.py for the generated resume and cover letter."""
    try:
        venv_python = str(SCRIPT_DIR / "venv" / "bin" / "python")
        if not Path(venv_python).exists():
            venv_python = sys.executable
        results = []
        for path in [resume_path, cover_path]:
            if path.exists():
                cmd = [venv_python, str(SCRIPT_DIR / "resume_to_pdf.py"), "--input", str(path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=str(SCRIPT_DIR))
                if result.returncode == 0:
                    log.info(f"PDF generated for {path.name}")
                    results.append(True)
                else:
                    log.error(f"PDF gen failed for {path.name}: {result.stderr}")
                    results.append(False)
        return all(results)
    except Exception as e:
        log.error(f"run_pdf_gen exception: {e}")
        return False


def process_sheet_needs_tailor():
    """Check sheet for jobs with status 'Needs Tailor' and run tailor.py on each."""
    try:
        jobs = get_sheet_jobs(status="Needs Tailor", min_score=0)
    except Exception as e:
        log.error(f"Could not read Needs Tailor jobs from sheet: {e}")
        return

    if not jobs:
        print("No 'Needs Tailor' jobs in sheet.")
        return

    print(f"Found {len(jobs)} 'Needs Tailor' job(s) in sheet:")
    for job in jobs:
        title   = job["title"]
        company = job["company"]
        url     = job["link"]
        row     = job["sheet_row"]
        print(f"  → {title} @ {company}  (row={row})")
        # Match the naming convention tailor.py uses: {row}-david-ot-{slug_title}-{slug_company}
        pdf_path = SCRIPT_DIR / "tailored" / f"{row}-david-ot-{_slug(title)}-{_slug(company)}-resume.pdf"
        if pdf_path.exists():
            print(f"    Already tailored — skipping (found {pdf_path.name})")
            log.info(f"Skipping row {row} — PDF already exists: {pdf_path.name}")
            # Ensure sheet status is Tailored even if we skipped
            try:
                update_job_status(row, "Tailored")
            except Exception as ex:
                log.warning(f"Could not update row {row} to Tailored: {ex}")
            continue
        if url:
            success = run_tailor(url, title=title, company=company, row=row)
            print(f"    Tailor: {'Done' if success else 'FAILED'}")
            if success:
                # tailor.py saves to tailored/src/{row}-david-ot-{slug_title}-{slug_company}-*
                resume_path = SCRIPT_DIR / "tailored" / "src" / f"{row}-david-ot-{_slug(title)}-{_slug(company)}-resume.md"
                cover_path  = SCRIPT_DIR / "tailored" / "src" / f"{row}-david-ot-{_slug(title)}-{_slug(company)}-cover-letter.md"
                pdf_ok = run_pdf_gen(resume_path, cover_path)
                print(f"    PDF gen: {'Done' if pdf_ok else 'FAILED'}")
                # Advance sheet status so apply_watcher picks it up
                try:
                    update_job_status(row, "Tailored")
                    log.info(f"Row {row} marked Tailored")
                    print(f"    Sheet: Marked Tailored")
                except Exception as ex:
                    log.error(f"Could not update row {row} to Tailored: {ex}")
        else:
            print(f"    No URL in sheet — skipping")


def main():
    # Phase 1: Check Gmail for new TAILOR emails (only within 60-min window)
    if is_within_window():
        log.info("=== tailor_watcher: within window, checking Gmail ===")
        print("Checking Gmail for TAILOR: requests...")

        gmail = get_gmail_service()
        emails = get_tailor_emails(gmail)

        if not emails:
            print("No new TAILOR: emails found.")
            log.info("No TAILOR emails found.")
        else:
            print(f"Found {len(emails)} TAILOR request(s):")
            for e in emails:
                title     = e["title"]
                company   = e["company"]
                url       = e["url"]
                row       = e["sheet_row"]
                print(f"  → {title} @ {company}  (sheet row={row})")

                # If row not in email, look it up by title+company
                if not row and title and company:
                    try:
                        row = find_job_row(title, company)
                    except Exception as ex:
                        log.warning(f"Could not find row for {title} @ {company}: {ex}")
                if row:
                    try:
                        update_job_status(row, "Needs Tailor")
                        log.info(f"Sheet row {row} marked Needs Tailor")
                    except Exception as ex:
                        log.warning(f"Could not update sheet row {row}: {ex}")

                mark_as_read(gmail, e["msg_id"])
    else:
        print("Outside tailor window — skipping Gmail check.")
        log.info("Outside tailor window — skipping Gmail check.")

    # Phase 2: Process any 'Needs Tailor' jobs in the sheet (always runs)
    print()
    process_sheet_needs_tailor()

    print("Done.")
    log.info("=== tailor_watcher: complete ===")


if __name__ == "__main__":
    main()
