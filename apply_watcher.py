#!/usr/bin/env python3
"""
apply_watcher.py — watches Google Sheets for Tailored jobs and auto-applies.

Runs as a daemon. Polls Sheets every 10 minutes for rows with status="Tailored".
For each, temporarily sets status to "Validated" so apply.py picks it up,
runs apply.py with --submit, then checks the result.

Usage:
    python3 apply_watcher.py           # continuous daemon mode
    python3 apply_watcher.py --once    # run once and exit
    python3 apply_watcher.py --dry-run # check what would be applied, no submission
"""

import argparse
import logging
import random
import subprocess
import sys
import time
import os
import datetime
from pathlib import Path

# Add parent dir to path for local imports
sys.path.insert(0, str(Path(__file__).parent))
from sheets_logger import get_sheet_jobs, update_job_status
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=True)

NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")
POLL_INTERVAL = 600  # 10 minutes
DAILY_CAP = 15

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [apply_watcher] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "apply_watcher.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def send_ntfy(title: str, message: str, priority: str = "default"):
    """Send push notification via ntfy."""
    if not NTFY_TOPIC:
        return
    try:
        import requests
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode(),
            headers={"Title": title, "Priority": priority},
            timeout=10,
        )
    except Exception as e:
        logger.warning(f"ntfy failed: {e}")


_SESSION_PATH = Path(__file__).parent / "linkedin_session" / "state.json"


def check_linkedin_session() -> bool:
    """
    Fast check — returns True if LinkedIn session is valid, False if expired.
    Navigates to /feed/ and checks we're NOT redirected to login.
    Times out in 15s so it never blocks.
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(storage_state=str(_SESSION_PATH))
            page = ctx.new_page()
            page.goto("https://www.linkedin.com/feed/", timeout=15000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            is_logged_in = "linkedin.com/feed" in page.url or "linkedin.com/in/" in page.url
            browser.close()
            return is_logged_in
    except Exception as e:
        logger.warning(f"Session check error: {e}")
        return False


def count_applied_today() -> int:
    """Count applications already submitted today."""
    today = datetime.date.today().isoformat()
    try:
        applied = get_sheet_jobs(status="Applied", min_score=0)
        return sum(1 for job in applied if job.get("date", "").startswith(today))
    except Exception:
        return 0


def run_apply_batch(dry_run: bool = False) -> tuple[int, int]:
    """
    Run apply.py to process all Validated jobs.
    Returns (success_count_estimate, error_flag).
    """
    script = Path(__file__).parent / "apply.py"
    cmd = [sys.executable, str(script), "--status", "Validated"]
    if not dry_run:
        cmd.append("--submit")

    logger.info(f"Running apply.py: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minute timeout for batch
            cwd=Path(__file__).parent,
        )
        output = result.stdout + result.stderr
        logger.info(f"apply.py output:\n{output[-2000:]}")

        if result.returncode == 0:
            # Count "APPLIED" in output
            applied_count = output.count("APPLIED")
            return applied_count, 0
        else:
            logger.error(f"apply.py failed (exit {result.returncode})")
            return 0, 1
    except subprocess.TimeoutExpired:
        logger.error("apply.py timed out after 30 minutes")
        return 0, 1
    except Exception as e:
        logger.error(f"apply.py error: {e}")
        return 0, 1


def watch_once(dry_run: bool = False):
    """Single poll cycle — find Tailored jobs and apply."""
    # LinkedIn is shelved — skip session check so Greenhouse/Lever/Dice jobs
    # are not blocked by an expired LinkedIn session.

    # Check daily cap
    applied_today = count_applied_today()
    if applied_today >= DAILY_CAP:
        logger.info(f"Daily cap reached ({applied_today}/{DAILY_CAP}). Skipping this cycle.")
        return

    # Get Tailored jobs
    try:
        tailored_jobs = get_sheet_jobs(status="Tailored", min_score=0)
    except Exception as e:
        logger.error(f"Could not read Tailored jobs: {e}")
        return

    if not tailored_jobs:
        logger.info("No Tailored jobs waiting. Nothing to apply.")
        return

    # Route all supported ATS types — apply.py handles routing internally
    from apply import detect_ats
    from collections import Counter
    ats_counts = Counter(detect_ats(j.get("link", "")) for j in tailored_jobs)
    unknown_jobs = [j for j in tailored_jobs if detect_ats(j.get("link", "")) == "unknown"]
    routable_jobs = [j for j in tailored_jobs if detect_ats(j.get("link", "")) != "unknown"]

    # Log per-ATS breakdown
    count_parts = [f"{ats}: {n}" for ats, n in sorted(ats_counts.items())]
    logger.info(f"Tailored jobs found — {', '.join(count_parts)}")
    if unknown_jobs:
        logger.info(
            f"Skipping {len(unknown_jobs)} job(s) with unsupported/unknown ATS — require manual application."
        )

    if not routable_jobs:
        logger.info("No auto-applicable jobs in Tailored queue. Nothing to process.")
        return

    remaining_cap = DAILY_CAP - applied_today
    to_process = routable_jobs[:remaining_cap]

    logger.info(f"Found {len(routable_jobs)} auto-applicable Tailored jobs. Processing up to {remaining_cap} today.")

    if dry_run:
        for job in to_process:
            ats = detect_ats(job.get("link", ""))
            logger.info(f"[DRY RUN] Would apply [{ats.upper()}]: {job.get('title')} @ {job.get('company')}")
        return

    # Set status to "Validated" so apply.py picks them up
    promoted = 0
    promoted_rows = set()
    for job in to_process:
        row = job.get("sheet_row")
        if not row:
            logger.warning(f"No sheet_row for {job.get('title')} — skipping")
            continue
        try:
            update_job_status(row, "Validated")
            promoted += 1
            promoted_rows.add(row)
            logger.info(f"Set status=Validated for row {row}: {job.get('title')} @ {job.get('company')}")
        except Exception as e:
            logger.error(f"Failed to update row {row} to Validated: {e}")

    if promoted == 0:
        logger.warning("No jobs could be promoted to Validated. Skipping apply.")
        return

    # Run apply.py which processes all Validated jobs
    success_count, error_flag = run_apply_batch(dry_run=False)

    # Check which jobs were actually applied — revert any still in "Validated" to "Apply Error"
    # (Jobs with no Easy Apply will have been marked "External Apply" by apply.py already)
    try:
        still_validated = get_sheet_jobs(status="Validated", min_score=0)
        for job in still_validated:
            row = job.get("sheet_row")
            if row and row in promoted_rows:
                update_job_status(row, "Apply Error")
                logger.warning(f"Reverted row {row} to 'Apply Error': {job.get('title')} @ {job.get('company')}")
    except Exception as e:
        logger.error(f"Failed to check/revert Validated jobs: {e}")

    # Summary notification
    msg = f"Promoted: {promoted}, Applied: ~{success_count}"
    if error_flag:
        msg += " (with errors)"
    send_ntfy("Job Applications Complete", msg, priority="high" if error_flag else "default")
    logger.info(msg)


def main():
    parser = argparse.ArgumentParser(description="apply_watcher: auto-apply to Tailored jobs")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--dry-run", action="store_true", help="Check what would apply, no submission")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN MODE — no applications will be submitted")

    if args.once or args.dry_run:
        watch_once(dry_run=args.dry_run)
        return

    logger.info(f"apply_watcher starting. Polling every {POLL_INTERVAL}s for Tailored jobs.")
    send_ntfy("apply_watcher started", f"Polling every {POLL_INTERVAL // 60}m for Tailored jobs")

    while True:
        try:
            watch_once()
        except Exception as e:
            logger.error(f"Unhandled error in watch cycle: {e}", exc_info=True)
            send_ntfy("apply_watcher error", str(e), priority="urgent")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
