"""
Gmail client — authentication + read/send helpers.
"""

import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv(override=True)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service():
    """Authenticate and return a Gmail API service object."""
    creds = None
    token_path = os.getenv("GMAIL_TOKEN_PATH", os.path.expanduser("~/anelo/token.json"))
    creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", os.path.expanduser("~/anelo/credentials.json"))

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_recent_recruiter_emails(service, hours: int = 24) -> list[dict]:
    """
    Fetch emails from the last `hours` hours that look like actual recruiter outreach.
    Tight filter — only real human recruiters and ATS platforms, no newsletters/alerts.
    Returns list of dicts with: id, subject, sender, snippet, body, date.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    after_ts = int(cutoff.timestamp())

    # Very specific recruiter subject phrases — not generic words like "job" or "opportunity"
    recruiter_subjects = (
        'subject:("interview" OR "technical screen" OR "phone screen" OR '
        '"recruiter" OR "I came across your profile" OR "your background" OR '
        '"reaching out about" OR "open role" OR "job opportunity at" OR '
        '"we\'d like to connect" OR "next steps" OR "move forward" OR '
        '"offer letter" OR "hiring manager" OR "availability")'
    )

    # Known ATS / hiring platforms — these are always job-related
    ats_senders = (
        '(from:greenhouse.io OR from:lever.co OR from:workday.com '
        'OR from:smartrecruiters.com OR from:jobvite.com OR from:icims.com '
        'OR from:ashbyhq.com OR from:myworkdayjobs.com OR from:taleo.net '
        'OR from:bamboohr.com OR from:rippling.com OR from:ripplehire.com)'
    )

    # Exclude all automated, marketing, and social senders
    exclusions = (
        '-from:noreply -from:no-reply -from:donotreply -from:mailer- '
        '-from:newsletter -from:notifications@ -from:alerts@ -from:support@ '
        '-from:info@ -from:hello@ -from:team@ -from:news@ '
        '-from:linkedin.com -from:indeed.com -from:dice.com -from:glassdoor.com '
        '-from:ziprecruiter.com -from:monster.com -from:careerbuilder.com '
        '-from:google.com -from:apple.com -from:amazon.com -from:microsoft.com '
        '-from:airbnb.com -from:plaid.com -from:experian.com -from:wellsfargo.com '
        '-from:anthropic.com -from:ddoseitutu@gmail.com '
        '-subject:"Job Digest" '
        '-label:promotions -label:social -label:forums -label:updates -label:spam'
    )

    query = f"after:{after_ts} ({recruiter_subjects} OR {ats_senders}) {exclusions}"
    results = service.users().messages().list(userId="me", q=query, maxResults=50).execute()
    messages = results.get("messages", [])

    emails = []
    for msg_ref in messages:
        msg = service.users().messages().get(userId="me", id=msg_ref["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        subject = headers.get("Subject", "")
        sender = headers.get("From", "")
        date_str = headers.get("Date", "")
        snippet = msg.get("snippet", "")
        body = _extract_body(msg["payload"])

        emails.append({
            "id": msg_ref["id"],
            "subject": subject,
            "sender": sender,
            "snippet": snippet,
            "body": body[:3000],  # cap to avoid token bloat
            "date": date_str,
        })

    return emails


def send_email(service, to: str, subject: str, html_body: str):
    """Send an HTML email via Gmail API."""
    message = MIMEMultipart("alternative")
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text or HTML body from a Gmail message payload."""
    if "parts" in payload:
        for part in payload["parts"]:
            result = _extract_body(part)
            if result:
                return result
    mime = payload.get("mimeType", "")
    if mime in ("text/plain", "text/html"):
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return ""
