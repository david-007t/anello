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
from notifier import notify_match, already_notified, log_notification

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

MAX_JOBS_PER_USER = 20
FRESHNESS_HOURS = 48
TOP_TAILOR_COUNT = 5  # tailor resume for top N matches only


def run(on_step=None, send_digest: bool = True):
    """
    Run the full pipeline. Optional on_step(msg: str) callback receives
    human-readable status updates at each key stage.
    """
    def _step(msg: str):
        logger.info(msg)
        if on_step:
            try:
                on_step(msg)
            except Exception:
                pass

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Missing Supabase credentials")
        return

    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get all users who have set preferences
    prefs_res = db.table("preferences").select("*").execute()
    all_prefs = prefs_res.data or []
    _step(f"Starting — {len(all_prefs)} user(s) found")

    for prefs in all_prefs:
        user_id = prefs.get("user_id")
        if not user_id:
            continue

        # Skip users with no role set
        if not prefs.get("role"):
            logger.info(f"Skipping {user_id} — no role set")
            continue

        # Look up user email/name early — needed for notifications + digest
        user_res = (
            db.table("users")
            .select("email,first_name")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        user_row = user_res.data[0] if user_res.data else {}
        user_email = user_row.get("email", "")
        user_name = user_row.get("first_name", "")

        roles = [r for r in [prefs.get("role"), prefs.get("role_2"), prefs.get("role_3")] if r]
        _step(f"Fetching jobs for {', '.join(roles)} · {prefs.get('location', 'any location')}")

        # 1. Fetch jobs (fetch_jobs handles all roles from prefs internally)
        raw_jobs = fetch_jobs(prefs, max_results=MAX_JOBS_PER_USER)
        if not raw_jobs:
            logger.warning(f"No jobs found for user {user_id}")
            continue

        _step(f"Scoring {len(raw_jobs)} jobs")

        # 2. Score + filter
        ranked = filter_and_rank(raw_jobs, prefs)
        if not ranked:
            logger.info(f"No qualifying jobs for user {user_id}")
            continue

        # Deduplicate by (company, title) — Adzuna returns same posting for many locations
        seen_jobs: set[tuple] = set()
        deduped = []
        for job in ranked:
            key = (
                (job.get("company") or "").lower().strip(),
                (job.get("title") or "").lower().strip(),
                (job.get("url") or "").lower().strip(),
            )
            if key not in seen_jobs:
                seen_jobs.add(key)
                deduped.append(job)
        ranked = deduped

        # Sort: direct ATS URLs (auto-applicable) first, aggregator/unknown last
        _ATS_HOSTS = ("greenhouse.io", "lever.co", "ashby.com", "workable.com", "teamtailor.com")
        def _ats_priority(job):
            url = (job.get("url") or "").lower()
            return 0 if any(h in url for h in _ATS_HOSTS) else 1
        ranked.sort(key=_ats_priority)
        logger.info(f"After dedup: {len(ranked)} unique jobs")

        # Freshness filter: only keep jobs posted within FRESHNESS_HOURS
        from notifier import _parse_posted_at, _minutes_ago
        fresh = []
        for job in ranked:
            posted_at = job.get("posted_at")
            if not posted_at:
                continue
            dt = _parse_posted_at(posted_at)
            if dt is None:
                continue
            if _minutes_ago(dt) <= FRESHNESS_HOURS * 60:
                fresh.append(job)
        if fresh:
            logger.info(f"Freshness filter: {len(fresh)}/{len(ranked)} jobs within {FRESHNESS_HOURS}h")
            ranked = fresh
        else:
            logger.info(f"Freshness filter: no jobs within {FRESHNESS_HOURS}h — keeping all {len(ranked)}")

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

        _step(f"Tailoring resume for top {min(TOP_TAILOR_COUNT, len(ranked))} matches")

        # 4. Tailor resume for top matches
        for i, job in enumerate(ranked[:TOP_TAILOR_COUNT]):
            if resume_text:
                try:
                    ranked[i]["tailored_resume"] = tailor_resume(resume_text, job)
                except Exception as e:
                    logger.error(f"Tailoring failed for {job.get('title')} at {job.get('company')}: {e} — continuing")

        # 4b. Send real-time notifications for fresh matches
        _step(f"Sending notifications for fresh matches")
        notified_count = 0
        for i, job in enumerate(ranked):
            job_url = job.get("url") or job.get("display_url", "")
            if already_notified(db, user_id, job_url):
                continue

            # Cover letter is only available if we tailored (top N only)
            # tailor_resume() returns a string (resume_markdown), not a dict —
            # so no cover letter is available through this path.
            cover_letter = ""
            resume_pdf = b""

            sent = notify_match(job, user_email, user_name, cover_letter, resume_pdf)
            if sent:
                log_notification(db, user_id, job)
                notified_count += 1

        if notified_count:
            logger.info(f"Sent {notified_count} real-time notifications for user {user_id}")

        _step(f"Saving {len(ranked)} jobs to digest")

        # Prune digest_jobs: remove rows older than FRESHNESS_HOURS on digest runs
        if send_digest:
            try:
                from datetime import datetime, timezone, timedelta
                cutoff = (datetime.now(timezone.utc) - timedelta(hours=FRESHNESS_HOURS)).isoformat()
                db.table("digest_jobs").delete().eq("user_id", user_id).lt("matched_at", cutoff).execute()
                logger.info(f"Pruned digest_jobs older than {FRESHNESS_HOURS}h for user {user_id}")
            except Exception as e:
                logger.warning(f"Could not prune digest_jobs: {e}")

        # 5. Save to digest_jobs
        rows = []
        for job in ranked:
            rows.append({
                "user_id": user_id,
                "company": job.get("company", ""),
                "role": job.get("title", ""),
                "job_url": job.get("url") or job.get("display_url", ""),
                "location": job.get("location", ""),
                "salary_range": _fmt_salary(job),
                "source": job.get("source", "adzuna"),
                "applied": False,
            })

        # Cross-run dedup: skip jobs already in digest_jobs for this user
        try:
            existing_res = db.table("digest_jobs").select("job_url").eq("user_id", user_id).execute()
            existing_urls = {r["job_url"] for r in (existing_res.data or []) if r.get("job_url")}
            rows = [r for r in rows if r.get("job_url") and r["job_url"] not in existing_urls]
        except Exception as e:
            logger.warning(f"Could not fetch existing jobs for dedup: {e}")

        if rows:
            db.table("digest_jobs").insert(rows).execute()
            logger.info(f"Saved {len(rows)} jobs for user {user_id}")

        _step("Sending digest email")

        # 6. Send digest email (only on scheduled daily digest, not intraday polls)
        if send_digest:
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
