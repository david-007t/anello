"""
tailor.py — AI resume tailoring via Anthropic Claude.
Rewrites user's resume to match a specific job description.
"""
import os
import logging
import anthropic

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
MODEL = "claude-haiku-4-5-20251001"  # fast + cheap for tailoring


def tailor_resume(resume_text: str, job: dict) -> str:
    """
    Returns a tailored version of resume_text for the given job.
    """
    prompt = f"""You are an expert resume writer. Rewrite the resume below to better match the job posting.

RULES:
- Keep all facts accurate — do not invent experience or skills
- Reorder and emphasize relevant experience
- Mirror keywords from the job description naturally
- Keep the same general structure and length
- Return ONLY the rewritten resume, no commentary

JOB TITLE: {job.get('title', '')}
COMPANY: {job.get('company', '')}
JOB DESCRIPTION:
{job.get('description', '')[:2000]}

ORIGINAL RESUME:
{resume_text[:3000]}

TAILORED RESUME:"""

    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        logger.error(f"Tailoring failed for {job.get('title')}: {e}")
        return resume_text  # fall back to original
