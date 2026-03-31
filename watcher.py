#!/usr/bin/env python3
"""
Component 2 — Gmail Watcher

Runs every 4 hours via launchd. Polls Gmail for interview requests, offers,
or urgent recruiter outreach. Sends an Ntfy push notification to David's
phone when something urgent is detected.
"""

import os
import re
import json
import logging

import anthropic
import requests
from dotenv import load_dotenv

from gmail_client import get_gmail_service, get_recent_recruiter_emails

load_dotenv(override=True)
logging.basicConfig(
    filename=os.path.expanduser("~/anelo/logs/watcher.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

# Signals that warrant a notification
ALERT_SUBJECT_KEYWORDS = [
    "interview", "schedule a call", "next steps", "offer", "move forward",
    "technical screen", "hiring manager", "availability", "chat", "connect",
]

# Senders to always skip
IGNORE_SENDER_PATTERNS = [
    r"jobs-noreply@linkedin\.com",
    r"jobalerts-noreply@linkedin\.com",
    r"noreply@",
    r"no-reply@",
    r"donotreply@",
    r"newsletter",
    r"marketing",
    r"unsubscribe",
    r"notifications@",
    r"@greenhouse\.io",   # automated ATS acknowledgements
    r"@lever\.co",
    r"@jobvite\.com",
]


def looks_urgent(email: dict) -> bool:
    """Quick heuristic check before sending to Claude."""
    subject = email.get("subject", "").lower()
    sender = email.get("sender", "").lower()

    # Skip known noise
    for pattern in IGNORE_SENDER_PATTERNS:
        if re.search(pattern, sender):
            return False

    # Check subject keywords
    return any(k in subject for k in ALERT_SUBJECT_KEYWORDS)


def classify_with_claude(emails: list[dict]) -> list[dict]:
    """
    Use Claude to classify which emails need an alert.
    Returns list of urgent emails with a short summary.
    """
    if not emails:
        return []

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    summaries = "\n\n".join(
        f"[{i+1}] From: {e['sender']}\nSubject: {e['subject']}\nSnippet: {e['snippet']}"
        for i, e in enumerate(emails)
    )

    prompt = f"""You are monitoring David Osei-Tutu's inbox for urgent job-related messages.

David is a Data Engineer II actively job hunting. He wants notifications for:
- Interview requests or scheduling emails
- Offers or positive next steps
- Urgent recruiter outreach (not automated blasts)
- Hiring manager / technical screen invites

He does NOT want alerts for:
- Automated job board digests
- LinkedIn notification emails
- Marketing or newsletter emails
- Generic rejection emails
- Automated ATS acknowledgements

EMAILS TO CLASSIFY:
{summaries}

Output a JSON array. For each email that warrants an alert, include:
- index (1-based)
- urgent (true/false)
- summary (max 15 words, as if texting David — e.g. "Google wants to schedule a technical screen")

Only include emails where urgent is true. If none, return [].
Output ONLY valid JSON."""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        results = json.loads(response.content[0].text.strip())
        # Map back to original emails
        urgent = []
        for r in results:
            if r.get("urgent"):
                idx = r["index"] - 1
                if 0 <= idx < len(emails):
                    email = emails[idx].copy()
                    email["alert_summary"] = r.get("summary", email["subject"])
                    urgent.append(email)
        return urgent
    except Exception as e:
        log.error(f"Claude classification failed: {e}")
        return []


def send_ntfy(summary: str, subject: str, sender: str):
    """Send a push notification via Ntfy."""
    topic = os.getenv("NTFY_TOPIC", "david-jobs-x7k2")
    url = f"https://ntfy.sh/{topic}"

    try:
        resp = requests.post(
            url,
            data=summary.encode("utf-8"),
            headers={
                "Title": f"Job Alert: {subject[:60]}",
                "Tags": "briefcase",
                "Priority": "high",
                "X-Message": f"From: {sender}",
            },
            timeout=10,
        )
        resp.raise_for_status()
        log.info(f"Ntfy sent: {summary}")
    except Exception as e:
        log.error(f"Ntfy failed: {e}")


def main():
    log.info("=== Watcher started ===")

    try:
        service = get_gmail_service()
        emails = get_recent_recruiter_emails(service, hours=4)
    except Exception as e:
        log.error(f"Gmail fetch failed: {e}")
        return

    log.info(f"Fetched {len(emails)} emails from last 4 hours.")

    # Quick heuristic filter first to save Claude tokens
    candidates = [e for e in emails if looks_urgent(e)]
    log.info(f"{len(candidates)} candidate emails after heuristic filter.")

    if not candidates:
        log.info("No urgent candidates. Exiting.")
        return

    # Claude classification
    urgent = classify_with_claude(candidates)
    log.info(f"{len(urgent)} email(s) classified as urgent.")

    for email in urgent:
        send_ntfy(
            summary=email["alert_summary"],
            subject=email["subject"],
            sender=email["sender"],
        )

    log.info("=== Watcher complete ===")


if __name__ == "__main__":
    main()
