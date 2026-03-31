"""
cover_letter.py — AI cover letter generation via Anthropic Claude.
"""
import os
import logging
import anthropic

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
MODEL = "claude-haiku-4-5-20251001"


def generate_cover_letter(resume_text: str, job: dict) -> str:
    """
    Returns a cover letter for the given job, based on the resume.
    """
    prompt = f"""You are an expert cover letter writer. Write a compelling, concise cover letter for the job below based on the candidate's resume.

RULES:
- 3 short paragraphs max
- Sound human, not robotic
- Match keywords from the job description naturally
- Do not invent experience or skills
- Do not include date, address headers, or "Dear Hiring Manager" — start directly with the opening paragraph
- Return ONLY the cover letter text, no commentary

JOB TITLE: {job.get('title', '')}
COMPANY: {job.get('company', '')}
JOB DESCRIPTION:
{job.get('description', '')[:2000]}

RESUME:
{resume_text[:3000]}

COVER LETTER:"""

    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        logger.error(f"Cover letter generation failed for {job.get('title')}: {e}")
        raise
