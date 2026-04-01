"""
drafter.py — Claude-powered outreach message drafter for the Anelo pipeline.
Drafts personalized LinkedIn connection requests, InMails, and cold emails.
"""
import os
import re
import json
import logging
import anthropic

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
MODEL = "claude-sonnet-4-6"

LINKEDIN_CONNECTION_CHAR_LIMIT = 300

SYSTEM_PROMPT = (
    "You are an outreach message writer. You write personalized, direct messages for job seekers "
    "reaching out to recruiters and hiring managers. Follow every rule below without exception.\n\n"

    "BANNED OPENERS — never start with these:\n"
    "- 'I came across your posting'\n"
    "- 'I saw your job listing'\n"
    "- 'I noticed your job post'\n"
    "- Any variation of discovering the job listing\n\n"

    "BANNED PHRASES — rewrite any sentence that contains:\n"
    "- 'passionate about'\n"
    "- 'excited to'\n"
    "- 'perfect fit'\n"
    "- 'team player'\n"
    "- 'hard worker'\n"
    "- 'go-getter'\n"
    "- 'self-starter'\n\n"

    "TONE RULES:\n"
    "- Open with a specific hook about the company or role — not the candidate\n"
    "- Be warm but direct. No hedging language\n"
    "- End with a single, clear ask (15-min call, coffee chat, brief call)\n"
    "- Sign with the candidate's name extracted from the resume\n\n"

    "MESSAGE TYPE RULES:\n"
    "- linkedin_connection: under 300 characters, punchy, 2-3 sentences max, no subject line\n"
    "- linkedin_inmail: 4-5 sentences max (~300 words), includes subject line, lead with strongest credential match\n"
    "- cold_email: 4-5 sentences max, includes subject line, lead with strongest credential match\n\n"

    "Return ONLY a JSON object with these exact keys:\n"
    "{\n"
    '  "message": "the full drafted message text",\n'
    '  "subject": "subject line (empty string for linkedin_connection)",\n'
    '  "message_type": "the message type passed in"\n'
    "}\n\n"
    "No markdown fences. No explanation. Only the JSON object."
)


def draft_message(resume_text: str, job: dict, message_type: str = "linkedin_connection") -> dict:
    """
    Returns {
        "message": str,      # the drafted message
        "subject": str,      # subject line (for inmail/email; empty for connection)
        "char_count": int,   # character count of the message
        "message_type": str,
        "warnings": list,    # any constraint violations
    }
    """
    title = job.get("title", job.get("role", ""))
    company = job.get("company", "")
    description = (job.get("description", "") or "")[:2000]

    type_instruction = {
        "linkedin_connection": (
            "Write a LinkedIn CONNECTION REQUEST message. "
            "HARD LIMIT: must be under 300 characters total. "
            "2-3 sentences max. No subject line needed."
        ),
        "linkedin_inmail": (
            "Write a LinkedIn INMAIL message. "
            "4-5 sentences, ~300 words max. "
            "Include a compelling subject line."
        ),
        "cold_email": (
            "Write a COLD EMAIL. "
            "4-5 sentences. "
            "Include a concise, specific subject line."
        ),
    }.get(message_type, "Write a LinkedIn connection request message under 300 characters.")

    prompt = f"""Target role: {title} at {company}

Job description excerpt:
{description or "(no description available — use title and company context)"}

Candidate resume:
{resume_text[:3000]}

Task: {type_instruction}

Return ONLY the JSON object with keys: message, subject, message_type."""

    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        # Strip markdown fences if present
        raw = re.sub(r"```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```", "", raw)
        raw = raw.strip()
        brace_idx = raw.find("{")
        if brace_idx > 0:
            raw = raw[brace_idx:]
        last_brace = raw.rfind("}")
        if last_brace != -1:
            raw = raw[:last_brace + 1]

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"drafter: JSON parse failed, returning raw text as message")
            result = {
                "message": raw,
                "subject": "",
                "message_type": message_type,
            }

        message_text = result.get("message", "")
        char_count = len(message_text)
        warnings = []

        if message_type == "linkedin_connection" and char_count > LINKEDIN_CONNECTION_CHAR_LIMIT:
            warnings.append(
                f"LinkedIn connection message exceeds 300-char limit ({char_count} chars). "
                "Trim before sending."
            )

        return {
            "message": message_text,
            "subject": result.get("subject", ""),
            "char_count": char_count,
            "message_type": result.get("message_type", message_type),
            "warnings": warnings,
        }

    except Exception as e:
        logger.error(f"drafter: failed for {title} at {company}: {e}")
        raise
