"""
tailor.py — AI resume tailoring + cover letter via Anthropic Claude.
Uses fine-tuned prompts for PM/Senior DE/TPM mode detection.
Returns JSON: {resume_markdown, cover_letter, fit_summary}
"""
import os
import re
import json
import logging
import anthropic

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
MODEL = "claude-sonnet-4-6"


def tailor_job(resume_text: str, job: dict) -> dict:
    """
    Returns {resume_markdown, cover_letter, fit_summary} for the given job.
    """
    title = job.get("title", "")
    company = job.get("company", "")
    description = job.get("description", "")[:4000]

    system = (
        "You are a resume writer specializing in translating technical IC experience into PM, Senior DE, and TPM narratives. "
        "Follow every rule below without exception.\n\n"

        "STEP 1 — ROLE DETECTION: Classify the target role into one of three modes based on the job title and JD:\n"
        "- PM mode: target is a Product Manager or product-adjacent role. Lead with product impact, user outcomes, cross-functional delivery, PRDs, adoption metrics, business outcomes. Minimize raw technical stack depth.\n"
        "- Senior DE mode: target is a Senior/Staff/Principal Data Engineer. Lead with technical depth, system scale, architecture decisions. Quantify data volume, pipeline complexity, reliability. Keep stack specifics.\n"
        "- TPM mode: target is a Technical Program Manager, Program Manager, or ops-adjacent role. Lead with delivery cadence, dependency management, organizational coordination. Emphasize program scope, milestone ownership, influence without authority. Balance technical credibility with operational execution.\n\n"

        "STEP 2 — HEADLINE: Generate a 1-line headline after the contact line, calibrated to the detected mode:\n"
        "- PM: e.g. 'Product-Minded Data Engineer | PRD Authorship | Cross-Functional Delivery | Executive Stakeholder Management'\n"
        "- Senior DE: e.g. 'Data Engineer II | Enterprise-Scale Pipelines | Snowflake/PostgreSQL/Spark | C-Suite Reporting Systems'\n"
        "- TPM: e.g. 'Technical Program Lead | Enterprise Platform Delivery | Cross-Functional Alignment | Metrics Governance'\n\n"

        "STEP 3 — BULLET REWRITING BY MODE:\n"
        "- PM mode: Cut infrastructure metrics (storage costs, pipeline counts, refresh runtimes). Translate into product outcomes — adoption, time-to-value, decision impact.\n"
        "- Senior DE mode: Keep technical metrics. Add architectural context — why the design decision was made, what scale it had to handle.\n"
        "- TPM mode: Reframe every bullet around coordination scope, delivery outcome, and stakeholder tier. Technical details become supporting evidence, not the lead.\n\n"

        "STEP 4 — IC FRAMING (applies to all modes): This candidate operates at broad cross-functional scope without direct reports. "
        "Never imply headcount. Use: 'coordinated across,' 'drove adoption through,' 'influenced without authority.' "
        "In TPM mode, make this a feature — call it out as a core competency explicitly.\n\n"

        "STEP 5 — SKILLS SECTION BY MODE:\n"
        "- PM: Include Jira, Confluence, Tableau, SQL, stakeholder management, Agile/Scrum. Omit Docker, Jenkins, Selenium, PyTest.\n"
        "- Senior DE: Keep full technical stack. Add any JD-specific tools not already listed.\n"
        "- TPM: Include Jira, Confluence, Agile/Scrum, SQL, Tableau, Python. Omit purely infrastructure tools unless the JD references them.\n\n"

        "STEP 6 — OVERLAPPING ROLES: If the resume contains a self-founded or consulting role with dates that overlap the current full-time role, omit it entirely. Do not flag it or explain the omission.\n\n"

        "STEP 7 — AWARDS: Surface any top-performer or talent recognition awards prominently in all modes — place in the summary/headline area or as the first item under the relevant role. This directly addresses seniority gap concerns.\n\n"

        "STEP 8 — SECTIONS TO CUT:\n"
        "- Publications: omit unless the JD explicitly references thought leadership or research.\n"
        "- Certifications unrelated to the target role: move to bottom or cut entirely.\n\n"

        "Never invent metrics, companies, or dates. Be specific, confident, and concrete.\n\n"

        "CRITICAL FORMAT RULE — SUMMARY SECTION: Do NOT include a SUMMARY section header in the resume_markdown. "
        "The summary (fit_summary) is injected separately. If you include a SUMMARY section header in resume_markdown, it will create a duplicate."
    )

    prompt = f"""I'm applying for: {title} at {company}

=== JOB DESCRIPTION ===
{description or "(no description available — use title/company context)"}

=== MY RESUME ===
{resume_text[:4000]}

Please return a JSON object with exactly these keys:
{{
  "resume_markdown": "The complete formatted resume as a markdown string. Apply all mode-specific rules from the system prompt. Structure: NAME\\nCONTACT LINE\\n[MODE-CALIBRATED HEADLINE]\\n\\nWORK EXPERIENCE\\n[All roles newest first. Most recent: 6-7 bullets rewritten per mode. Prior roles: 4-5 bullets. Oldest: 3-4 bullets.]\\n\\nEDUCATION\\n[Degree | Institution | Dates]\\n\\nAWARDS & CERTIFICATIONS\\n[Top-performer award first, then role-relevant others]\\n\\nSKILLS\\n[Mode-filtered skill list, most JD-relevant first]",
  "cover_letter": "Write a cover letter for this specific role at this specific company. Follow every rule below without exception.\\n\\nSTRUCTURE — 4 paragraphs, no labels, no numbering:\\n\\nParagraph 1 — Hook with the company or the problem space, not the candidate. If the JD contains a clear mission, values signal, or domain-specific challenge, open with it — make that the frame, then in 1-2 sentences place the candidate inside it. If the JD has no meaningful company-specific signal, open with the domain problem this role exists to solve. Never open with 'I am a...' Never open with a generic compliment.\\n\\nParagraph 2 — Make the strongest functional case. Pick the single most relevant experience from the candidate's background and go deep: what was the situation, what did they do, what was the outcome. For any stat, add framing — over what timeframe, compared to what baseline. Mirror the exact language of the job description. Do not add a hand-holding sentence that explains the parallel — make the connection self-evident.\\n\\nParagraph 3 — IC scope as a feature, not a gap. Frame broad cross-functional impact without formal direct-report authority as a differentiator. Ground it in a real example. Never imply headcount the candidate did not have.\\n\\nParagraph 4 — Forward-looking close. One short paragraph. Connect where the candidate is now to where this role goes. Be specific to the role. No hedging. No generic closing.\\n\\nSign-off: Best,\\n[Candidate Name from resume]\\n\\nBANNED PHRASES — if any appear, rewrite the sentence:\\n- 'immediate and measurable impact'\\n- 'ready to take my skills to the next level'\\n- 'sits at the intersection of'\\n- 'passionate about'\\n- 'I am excited to'\\n- 'There are X things that make me the perfect fit'\\n- First / Second / Finally (enumeration)\\n- Any closing phrase that could be copy-pasted into a different cover letter\\n- Any sentence that explicitly explains the parallel between experience and role\\n\\nCOMPANY RESEARCH RULE: You only have the JD as input. Do not hallucinate specific company facts. Never use brackets or [INSERT:...] patterns.\\n\\nTONE: Declarative and confident. No hedging. No filler. Every sentence must earn its place.",
  "fit_summary": "2-3 sentence professional summary. No pronouns. Impersonal headline style — start with professional identity or noun phrase. Hard cap: 3 sentences. No buzzwords. Calibrate to detected mode."
}}

Return ONLY the JSON object, no markdown fences, no explanation."""

    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip() if msg.content else ""
        if not raw:
            logger.warning(f"Empty response from Claude for {title} at {company} — skipping tailor")
            return {"resume_markdown": resume_text, "cover_letter": "", "fit_summary": ""}
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
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Tailoring failed for {title} at {company}: {e}")
        raise


def tailor_resume(resume_text: str, job: dict) -> str:
    """Legacy wrapper — returns only resume_markdown for backward compat (main.py)."""
    result = tailor_job(resume_text, job)
    return result.get("resume_markdown", resume_text)
