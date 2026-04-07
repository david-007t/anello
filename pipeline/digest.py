"""
digest.py — Send daily job digest emails via Resend.
"""
import os
import logging
import resend

logger = logging.getLogger(__name__)
resend.api_key = os.environ.get("RESEND_API_KEY", "")


def send_digest(user_email: str, user_name: str, jobs: list[dict], user_role: str = "") -> bool:
    """Send a digest email with top job matches to the user."""
    if not jobs:
        logger.info(f"No jobs to send for {user_email}")
        return False

    if not resend.api_key:
        logger.error("RESEND_API_KEY not set")
        return False

    job_cards = ""
    for i, j in enumerate(jobs[:5]):
        salary = ""
        if j.get("salary_min") and j.get("salary_max"):
            salary = f"${int(j['salary_min']):,}–${int(j['salary_max']):,}"
        elif j.get("salary_min"):
            salary = f"${int(j['salary_min']):,}+"
        elif j.get("salary_range"):
            salary = j["salary_range"]

        meta_parts = [j.get("company", ""), j.get("location", "")]
        if salary:
            meta_parts.append(salary)
        meta = " · ".join(p for p in meta_parts if p)

        num = str(i + 1).zfill(2)

        job_cards += f"""
        <div style="background:#ffffff;border:1px solid #f1f5f9;border-radius:16px;padding:20px 22px;margin-bottom:10px;">
          <table style="width:100%;border-collapse:collapse;">
            <tr>
              <td style="width:36px;vertical-align:top;padding-top:1px;">
                <span style="font-size:18px;font-weight:900;color:#cbd5e1;line-height:1;">{num}</span>
              </td>
              <td style="vertical-align:top;">
                <div style="margin-bottom:4px;">
                  <a href="{j.get('url', '#')}" style="font-size:14px;font-weight:700;color:#0f172a;text-decoration:none;">{j.get('title', '')}</a>
                </div>
                <div style="font-size:13px;color:#64748b;margin-bottom:10px;">{meta}</div>
                {f'<div style="font-size:13px;color:#64748b;font-style:italic;margin-bottom:12px;line-height:1.5;">{j["anelo_note"]}</div>' if j.get("anelo_note") else '<div style="margin-bottom:12px;"></div>'}
                <a href="{j.get('url', '#')}" style="display:inline-block;background:#0f172a;color:#ffffff;font-size:12px;font-weight:600;padding:7px 16px;border-radius:8px;text-decoration:none;">Apply →</a>
              </td>
            </tr>
          </table>
        </div>"""

    remaining = len(jobs) - 5
    more_note = ""
    if remaining > 0:
        more_note = f'<p style="font-size:13px;color:#94a3b8;text-align:center;margin:16px 0 0;">+ {remaining} more match{"es" if remaining != 1 else ""} found today.</p>'

    name = user_name or "there"
    role_label = f" {user_role}" if user_role else ""
    subject_line = f"Your top 5{role_label} matches today"

    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
  <div style="max-width:580px;margin:40px auto;padding:0 16px 40px;">

    <!-- Header -->
    <div style="margin-bottom:28px;">
      <p style="font-size:13px;font-weight:700;color:#94a3b8;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 10px;">anelo</p>
      <h1 style="font-size:26px;font-weight:800;color:#0f172a;margin:0 0 6px;letter-spacing:-0.5px;">{subject_line}</h1>
      <p style="font-size:14px;color:#64748b;margin:0;">Hi {name} — here are your top 5{role_label} picks for today.</p>
    </div>

    <!-- Job cards -->
    {job_cards}
    {more_note}

    <!-- Footer -->
    <div style="margin-top:36px;padding-top:20px;border-top:1px solid #e2e8f0;">
      <p style="font-size:12px;color:#94a3b8;margin:0;">
        Anelo · <a href="https://anelo.io" style="color:#94a3b8;text-decoration:none;">anelo.io</a>
      </p>
    </div>

  </div>
</body>
</html>"""

    text_parts = [f"{subject_line}\nHi {name} — here are your top 5{role_label} picks for today.\n"]
    for i, j in enumerate(jobs[:5]):
        num = str(i + 1).zfill(2)
        text_parts.append(f"{num}. {j.get('title', '')} at {j.get('company', '')}\n   {j.get('url', '')}\n")
    text = "\n".join(text_parts)

    try:
        resend.Emails.send({
            "from": "Anelo <digest@anelo.io>",
            "to": [user_email],
            "subject": subject_line,
            "html": html,
            "text": text,
        })
        logger.info(f"Digest sent to {user_email} ({len(jobs)} jobs)")
        return True
    except Exception as e:
        logger.error(f"Failed to send digest to {user_email}: {e}")
        return False
