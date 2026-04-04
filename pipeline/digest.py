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
        elif j.get("salary_range"):
            salary = f" · {j['salary_range']}"

        job_rows += f"""
        <tr>
          <td style="padding:14px 0;border-bottom:1px solid #1a1a1a;">
            <a href="{j.get('url','#')}" style="font-weight:600;color:#fff;text-decoration:none;font-size:14px;">
              {j.get('title','')}
            </a><br>
            <span style="color:#555;font-size:13px;">
              {j.get('company','')} · {j.get('location','')}{salary}
            </span>
          </td>
        </tr>"""

    html = f"""
    <html>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#000;margin:0;padding:0;">
      <div style="max-width:560px;margin:40px auto;background:#0d0d0d;border-radius:16px;padding:36px;border:1px solid #1f1f1f;">
        <p style="font-size:22px;font-weight:800;color:#fff;margin:0 0 4px;letter-spacing:-0.5px;">
          Your {len(jobs)} matches today
        </p>
        <p style="color:#555;font-size:13px;margin:0 0 28px;">
          Hi {user_name or 'there'} — here's what Anelo found.
        </p>
        <table style="width:100%;border-collapse:collapse;">
          {job_rows}
        </table>
        <p style="color:#333;font-size:12px;margin-top:28px;border-top:1px solid #1a1a1a;padding-top:20px;">
          Anelo · <a href="https://anelo.io" style="color:#444;text-decoration:none;">anelo.io</a>
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
