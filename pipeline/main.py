"""
main.py — Anelo multi-user pipeline entry point.

Runs daily (triggered by Railway cron or scheduler):
  1. Pull all users + preferences from Supabase
  2. Fetch jobs for each user via Adzuna
  3. Score + filter jobs
  4. Tailor resume for top matches
  5. Save matches to digest_jobs table
  6. Send digest email via Resend

Env vars required:
  SUPABASE_URL (or NEXT_PUBLIC_SUPABASE_URL)
  SUPABASE_SERVICE_ROLE_KEY
  ADZUNA_APP_ID
  ADZUNA_API_KEY
  ANTHROPIC_API_KEY
  RESEND_API_KEY
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

from supabase import create_client
from jobs import fetch_jobs
from scorer import filter_and_rank
from tailor import tailor_resume
from digest import send_digest

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

MAX_JOBS_PER_USER = 20
TOP_TAILOR_COUNT = 5  # tailor resume for top N matches only


def run():
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Missing Supabase credentials")
        return

    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get all users who have set preferences
    prefs_res = db.table("preferences").select("*").execute()
    all_prefs = prefs_res.data or []
    logger.info(f"Running pipeline for {len(all_prefs)} users")

    for prefs in all_prefs:
        user_id = prefs.get("user_id")
        if not user_id:
            continue

        # Skip users with no role set
        if not prefs.get("role"):
            logger.info(f"Skipping {user_id} — no role set")
            continue

        logger.info(f"Processing user {user_id} | role={prefs.get('role')} location={prefs.get('location')}")

        # 1. Fetch jobs
        raw_jobs = fetch_jobs(prefs, max_results=MAX_JOBS_PER_USER)
        if not raw_jobs:
            logger.warning(f"No jobs found for user {user_id}")
            continue

        # 2. Score + filter
        ranked = filter_and_rank(raw_jobs, prefs)
        if not ranked:
            logger.info(f"No qualifying jobs for user {user_id}")
            continue

        # 3. Get user's resume text
        resume_res = (
            db.table("resumes")
            .select("file_path,file_name")
            .eq("user_id", user_id)
            .order("uploaded_at", desc=True)
            .limit(1)
            .execute()
        )
        resume_data = resume_res.data[0] if resume_res.data else None
        resume_text = ""

        if resume_data:
            # Download resume text from Supabase Storage
            try:
                file_bytes = db.storage.from_("resumes").download(resume_data["file_path"])
                resume_text = file_bytes.decode("utf-8", errors="ignore")
            except Exception as e:
                logger.warning(f"Could not load resume for {user_id}: {e}")

        # 4. Tailor resume for top matches
        for i, job in enumerate(ranked[:TOP_TAILOR_COUNT]):
            if resume_text:
                ranked[i]["tailored_resume"] = tailor_resume(resume_text, job)

        # 5. Save to digest_jobs
        rows = []
        for job in ranked:
            rows.append({
                "user_id": user_id,
                "company": job.get("company", ""),
                "role": job.get("title", ""),
                "job_url": job.get("url", ""),
                "location": job.get("location", ""),
                "salary_range": _fmt_salary(job),
                "source": job.get("source", "adzuna"),
                "applied": False,
            })

        if rows:
            db.table("digest_jobs").insert(rows).execute()
            logger.info(f"Saved {len(rows)} jobs for user {user_id}")

        # 6. Send digest email
        # Look up user email from clerk via Supabase users table (if exists)
        # For now, skip if no email mapping — will wire Clerk webhook later
        user_email = prefs.get("email")
        user_name = prefs.get("name", "")
        if user_email:
            send_digest(user_email, user_name, ranked)
        else:
            logger.info(f"No email for user {user_id} — skipping digest send")

    logger.info("Pipeline run complete")


def _fmt_salary(job: dict) -> str:
    lo, hi = job.get("salary_min"), job.get("salary_max")
    if lo and hi:
        return f"${int(lo):,}–${int(hi):,}"
    if lo:
        return f"${int(lo):,}+"
    return ""


if __name__ == "__main__":
    run()
