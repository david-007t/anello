"""
digest.py — Send daily job digest emails via Resend.
"""
import os
import logging
import resend

logger = logging.getLogger(__name__)
resend.api_key = os.environ.get("RESEND_API_KEY", "")


def send_digest(user_email: str, user_name: str, jobs: list[dict]) -> bool:
    """Send a digest email with top job matches to the user."""
    if not jobs:
        logger.info(f"No jobs to send for {user_email}")
        return False

    if not resend.api_key:
        logger.error("RESEND_API_KEY not set")
        return False

    job_rows = ""
    for j in jobs[:10]:  # cap at 10 per digest
        salary = ""
        if j.get("salary_min") and j.get("salary_max"):
            salary = f" · ${int(j['salary_min']):,}–${int(j['salary_max']):,}"
        elif j.get("salary_min"):
            salary = f" · ${int(j['salary_min']):,}+"

        job_rows += f"""
        <tr>
          <td style="padding:12px 0;border-bottom:1px solid #f1f5f9;">
            <a href="{j.get('url','#')}" style="font-weight:600;color:#4f46e5;text-decoration:none;">
              {j.get('title','')}
            </a><br>
            <span style="color:#64748b;font-size:13px;">
              {j.get('company','')} · {j.get('location','')}{salary}
            </span>
          </td>
        </tr>"""

    html = f"""
    <html>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8fafc;margin:0;padding:0;">
      <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:16px;padding:32px;border:1px solid #e2e8f0;">
        <h1 style="font-size:22px;font-weight:800;color:#0f172a;margin:0 0 4px;">
          Your daily job digest
        </h1>
        <p style="color:#64748b;font-size:14px;margin:0 0 24px;">
          Hi {user_name or 'there'} — here are today's top matches.
        </p>
        <table style="width:100%;border-collapse:collapse;">
          {job_rows}
        </table>
        <div style="margin-top:24px;padding-top:20px;border-top:1px solid #f1f5f9;">
          <a href="https://anelo.io/dashboard" style="display:inline-block;background:#4f46e5;color:#fff;font-weight:600;font-size:14px;padding:10px 20px;border-radius:10px;text-decoration:none;">
            View dashboard →
          </a>
        </div>
        <p style="color:#94a3b8;font-size:12px;margin-top:20px;">
          Anelo · <a href="https://anelo.io" style="color:#94a3b8;">anelo.io</a>
        </p>
      </div>
    </body>
    </html>"""

    try:
        resend.Emails.send({
            "from": "Anelo <digest@anelo.io>",
            "to": [user_email],
            "subject": f"Your {len(jobs)} job matches today",
            "html": html,
        })
        logger.info(f"Digest sent to {user_email} ({len(jobs)} jobs)")
        return True
    except Exception as e:
        logger.error(f"Failed to send digest to {user_email}: {e}")
        return False
