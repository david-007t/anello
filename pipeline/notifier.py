"""
notifier.py — Real-time job match notifications.

Sends an immediate ntfy push + email via Resend for each new job that
clears the scoring threshold.

Env vars:
  NTFY_TOPIC        — ntfy.sh topic (default: anelo-jobs)
  RESEND_API_KEY    — already set
"""
import os
import logging
import base64
from datetime import datetime, timezone

import httpx
import resend

logger = logging.getLogger(__name__)

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "anelo-jobs")
resend.api_key = os.environ.get("RESEND_API_KEY", "")

MAX_AGE_MINUTES = 1440  # 24 hours


def _parse_posted_at(posted_at: str) -> datetime | None:
    """Parse an ISO datetime string to a timezone-aware UTC datetime."""
    if not posted_at:
        return None
    try:
        # Handle trailing Z (common in JSearch responses)
        cleaned = posted_at.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)
    except (ValueError, TypeError):
        return None


def _minutes_ago(dt: datetime) -> int:
    """Return how many minutes ago `dt` was from now (UTC)."""
    now = datetime.now(timezone.utc)
    delta = now - dt
    return int(delta.total_seconds() / 60)


def _fmt_age(minutes: int) -> str:
    """Format age as 'X minutes ago' or 'X hours ago'."""
    if minutes < 60:
        return f"{minutes} minutes ago"
    hours = round(minutes / 60, 1)
    hours_str = f"{int(hours)}h" if hours == int(hours) else f"{hours}h"
    return f"{hours_str} ago"


def _fmt_salary(job: dict) -> str:
    lo, hi = job.get("salary_min"), job.get("salary_max")
    if lo and hi:
        return f"${int(lo):,}–${int(hi):,}"
    if lo:
        return f"${int(lo):,}+"
    return ""


def _send_ntfy(job: dict, minutes: int, apply_url: str) -> bool:
    """Send push notification via ntfy.sh."""
    title = f"New match: {job.get('title', '')} at {job.get('company', '')}"
    # HTTP headers must be ASCII — replace non-ASCII chars
    title_ascii = title.encode("ascii", errors="replace").decode("ascii")
    salary = _fmt_salary(job)
    location = job.get("location", "")
    parts = [p for p in [location, salary, f"posted {_fmt_age(minutes)}"] if p]
    body = " · ".join(parts) + f"\n{apply_url}"

    try:
        resp = httpx.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            content=body.encode("utf-8"),
            headers={
                "Title": title_ascii,
                "Priority": "high",
                "Tags": "briefcase",
            },
            timeout=10,
        )
        resp.raise_for_status()
        logger.info(f"[notifier] ntfy sent: {title}")
        return True
    except Exception as e:
        logger.warning(f"[notifier] ntfy failed: {e}")
        return False


def _send_email(
    job: dict,
    user_email: str,
    user_name: str,
    minutes: int,
    apply_url: str,
    cover_letter: str = "",
    resume_pdf_bytes: bytes = b"",
) -> bool:
    """Send immediate per-job email via Resend."""
    if not resend.api_key:
        logger.error("[notifier] RESEND_API_KEY not set — skipping email")
        return False

    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    salary = _fmt_salary(job)

    subject = f"New match: {title} at {company} — posted {_fmt_age(minutes)}"

    # Build HTML body
    salary_html = f"<p style='color:#64748b;'>Salary: {salary}</p>" if salary else ""
    cover_html = ""
    if cover_letter:
        escaped = cover_letter.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        paragraphs = escaped.split("\n\n")
        cover_paras = "".join(f"<p>{p}</p>" for p in paragraphs if p.strip())
        cover_html = f"""
        <div style="margin-top:24px;padding-top:20px;border-top:1px solid #e2e8f0;">
          <h3 style="font-size:16px;color:#0f172a;">Cover Letter</h3>
          {cover_paras}
        </div>"""

    html = f"""
    <html>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8fafc;margin:0;padding:0;">
      <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:16px;padding:32px;border:1px solid #e2e8f0;">
        <h1 style="font-size:20px;font-weight:800;color:#0f172a;margin:0 0 4px;">
          {title}
        </h1>
        <p style="color:#64748b;font-size:14px;margin:0 0 8px;">
          {company} · {location}
        </p>
        {salary_html}
        <p style="color:#94a3b8;font-size:13px;margin:0 0 16px;">
          Posted {_fmt_age(minutes)}
        </p>
        <a href="{apply_url}" style="display:inline-block;background:#4f46e5;color:#fff;font-weight:600;font-size:14px;padding:10px 20px;border-radius:10px;text-decoration:none;">
          Apply now
        </a>
        {cover_html}
        <p style="color:#94a3b8;font-size:12px;margin-top:20px;">
          Anelo · <a href="https://anelo.io" style="color:#94a3b8;">anelo.io</a>
        </p>
      </div>
    </body>
    </html>"""

    email_params: dict = {
        "from": "Anelo <digest@anelo.io>",
        "to": [user_email],
        "subject": subject,
        "html": html,
    }

    # Attach resume PDF if available
    if resume_pdf_bytes:
        company_slug = company.replace(" ", "-").lower()
        email_params["attachments"] = [
            {
                "filename": f"resume-{company_slug}.pdf",
                "content": base64.b64encode(resume_pdf_bytes).decode("utf-8"),
                "content_type": "application/pdf",
            }
        ]

    try:
        resend.Emails.send(email_params)
        logger.info(f"[notifier] Email sent to {user_email}: {title} at {company}")
        return True
    except Exception as e:
        logger.error(f"[notifier] Email failed for {user_email}: {e}")
        return False


def notify_match(
    job: dict,
    user_email: str,
    user_name: str,
    tailored_cover_letter: str = "",
    resume_pdf_bytes: bytes = b"",
) -> bool:
    """Send ntfy push + email for a single job match. Returns True if sent."""
    title = job.get("title", "unknown")
    company = job.get("company", "unknown")
    posted_at = job.get("posted_at")

    # Freshness gate: skip if no post time
    if not posted_at:
        logger.info(f"[notifier] Skipping {title} — no post time")
        return False

    dt = _parse_posted_at(posted_at)
    if dt is None:
        logger.info(f"[notifier] Skipping {title} — unparseable post time: {posted_at}")
        return False

    minutes = _minutes_ago(dt)

    # Freshness gate: skip if older than 2 hours
    if minutes > MAX_AGE_MINUTES:
        logger.info(f"[notifier] Skipping {title} — stale ({minutes}m ago)")
        return False

    apply_url = job.get("url") or job.get("display_url", "")

    ntfy_ok = _send_ntfy(job, minutes, apply_url)
    email_ok = _send_email(
        job, user_email, user_name, minutes, apply_url,
        tailored_cover_letter, resume_pdf_bytes,
    )

    return email_ok


def already_notified(db, user_id: str, job_url: str) -> bool:
    """Check job_notifications table for existing entry."""
    if not job_url:
        return False
    try:
        res = (
            db.table("job_notifications")
            .select("id")
            .eq("user_id", user_id)
            .eq("job_url", job_url)
            .limit(1)
            .execute()
        )
        return bool(res.data)
    except Exception as e:
        logger.warning(f"[notifier] Could not check job_notifications: {e}")
        return False


def log_notification(db, user_id: str, job: dict) -> None:
    """Insert row into job_notifications table."""
    job_url = job.get("url") or job.get("display_url", "")
    try:
        db.table("job_notifications").insert({
            "user_id": user_id,
            "job_url": job_url,
            "job_title": job.get("title", ""),
            "company": job.get("company", ""),
        }).execute()
    except Exception as e:
        logger.error(f"[notifier] Could not log notification: {e}")
