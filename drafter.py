#!/usr/bin/env python3
"""
Component 3 — Message Drafter (manual CLI tool)

Usage:
    python drafter.py

Paste in a LinkedIn DM or recruiter email, optionally add context,
and Claude drafts a reply in David's voice.
"""

import os
import sys

import anthropic
from dotenv import load_dotenv

from resume_context import get_resume_text, VOICE_INSTRUCTIONS, JOB_CRITERIA

load_dotenv(override=True)


def draft_reply(message: str, context: str = "") -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resume = get_resume_text()

    context_block = f"\nDavid's notes: {context}" if context.strip() else ""

    prompt = f"""You are drafting a reply for David Osei-Tutu, a Data Engineer II at Nutanix.

DAVID'S RESUME:
{resume}

JOB PREFERENCES:
- Remote only — no hybrid, no on-site
- Minimum $140,000/year
- Target roles: Data Engineer, Senior Data Engineer, Data Engineering Manager, TPM

VOICE INSTRUCTIONS:
{VOICE_INSTRUCTIONS}

THE MESSAGE DAVID RECEIVED:
{message}
{context_block}

Write a reply in David's voice. Be direct, confident, and concise.
Do NOT add a subject line. Just the reply body.
Do NOT sign off with a full signature block — just "David" or nothing at all."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def main():
    print("=" * 60)
    print("  Anelo — Message Drafter")
    print("  Paste the message, then press Enter twice when done.")
    print("=" * 60)
    print()

    print("Paste the LinkedIn DM or recruiter email:")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    message = "\n".join(lines).strip()

    if not message:
        print("No message provided. Exiting.")
        sys.exit(0)

    print()
    print("Any context for your reply? (e.g. 'interested but negotiating salary')")
    print("Press Enter to skip:")
    context = input().strip()

    print()
    print("Drafting reply...")
    print("-" * 60)

    try:
        reply = draft_reply(message, context)
        print()
        print(reply)
        print()
        print("-" * 60)
        print("Copy the reply above. Review and send manually.")

        # Optionally save to clipboard on macOS
        try:
            import subprocess
            subprocess.run(["pbcopy"], input=reply.encode(), check=True)
            print("(Copied to clipboard)")
        except Exception:
            pass

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
