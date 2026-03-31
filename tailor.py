#!/usr/bin/env python3
"""
tailor.py — AI-powered resume tailoring for each job.

Uses Claude to generate a COMPLETE formatted resume document + cover letter
tailored to a specific job description.

Usage:
    python tailor.py                    # all Validated jobs from sheet
    python tailor.py --url <job_url>    # single job by URL
    python tailor.py --min-score 8      # filter by score
    python tailor.py --status Applied   # use a different status filter
"""

import os
import re
import sys
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

import anthropic
from resume_context import JOB_CRITERIA, IDENTITY
from resume_selector import load_resume_db, detect_job_type, extract_jd_keywords, select_entries, format_selected_context
from sheets_logger import get_sheet_jobs
from digest import _PLAYWRIGHT_LAUNCH_ARGS, _PLAYWRIGHT_UA

OUTPUT_DIR = Path(__file__).parent / "tailored" / "src"
MODEL = "claude-sonnet-4-6"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def _fetch_jd_text(url: str) -> str:
    """Fetch job description text from a URL. Uses Playwright for LinkedIn."""
    if "linkedin.com" in url:
        return _fetch_linkedin_jd(url)
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": _PLAYWRIGHT_UA})
        resp.raise_for_status()
        # Strip HTML tags roughly
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:8000]
    except Exception as e:
        print(f"  [warn] Could not fetch JD via requests: {e}")
        return ""


def _fetch_linkedin_jd(url: str) -> str:
    """Fetch LinkedIn job description using Playwright with session."""
    _session_path = os.path.expanduser("~/anelo/linkedin_session/state.json")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=_PLAYWRIGHT_LAUNCH_ARGS)
            session_state = _session_path if os.path.exists(_session_path) else None
            ctx = browser.new_context(
                user_agent=_PLAYWRIGHT_UA,
                extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
                storage_state=session_state,
            )
            page = ctx.new_page()
            page.goto(url, timeout=25000, wait_until="domcontentloaded")
            try:
                page.wait_for_selector(".jobs-description, [class*='description']", timeout=7000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            text = page.inner_text("body")
            page.close()
            ctx.close()
            browser.close()
            return text[:8000]
    except Exception as e:
        print(f"  [warn] Playwright failed for LinkedIn JD: {e}")
        return ""


def _format_full_db_for_prompt(db: dict) -> str:
    """Format the complete resume_db.json for inclusion in the Claude prompt."""
    lines = []

    identity = db.get("identity", {})
    lines.append("=== CANDIDATE IDENTITY ===")
    lines.append(f"Name: {identity.get('name', '')}")
    lines.append(f"Email: {identity.get('email', '')}")
    lines.append(f"Phone: {identity.get('phone', '')}")
    lines.append(f"LinkedIn: {identity.get('linkedin', '')}")
    lines.append("")

    lines.append("=== ALL WORK EXPERIENCE (include ALL roles in the resume) ===")
    for exp in db.get("experience", []):
        start = exp.get("start_date", "")[:7].replace("-", "/")
        end_raw = exp.get("end_date")
        end = end_raw[:7].replace("-", "/") if end_raw else "Present"
        lines.append(f"\nRole: {exp['role']}")
        lines.append(f"Company: {exp['company']}")
        lines.append(f"Dates: {start} - {end}")
        lines.append("Bullets:")
        for b in exp.get("bullets", []):
            lines.append(f"  - {b['text']}")

    lines.append("\n=== EDUCATION ===")
    for edu in db.get("education", []):
        start_yr = edu.get("start_date", "2020-08-01")[:7].replace("-", "/") if edu.get("start_date") else "08/2020"
        grad = edu.get("graduation_date", "")[:7].replace("-", "/")
        minors = edu.get("minors", [])
        minor_str = f", Double Minor: {', '.join(minors)}" if minors else ""
        lines.append(f"{edu['degree']} in {edu['field']}{minor_str}")
        lines.append(f"{edu['institution']} | {start_yr} - {grad}")

    lines.append("\n=== AWARDS, CERTIFICATIONS & SCHOLARSHIPS ===")
    for award in db.get("awards", []):
        date = award.get("date", "")[:7].replace("-", "/")
        lines.append(f"{award['name']} | {date}")
        lines.append(f"{award['issuer']}")
        if award.get("description"):
            lines.append(f"{award['description']}")

    lines.append("\n=== PUBLICATIONS ===")
    for pub in db.get("publications", []):
        date = pub.get("date", "")[:7].replace("-", "/")
        lines.append(f"{pub['title']} | {date}")
        lines.append(f"{pub['venue']}")
        if pub.get("cited_by"):
            lines.append(f"Cited by: {pub['cited_by']}")

    lines.append("\n=== ALL SKILLS (reorder by relevance in output) ===")
    skill_names = [s["name"] for s in db.get("skills", [])]
    lines.append(", ".join(skill_names))

    return "\n".join(lines)


def tailor_job(title: str, company: str, url: str, jd_text: str) -> dict:
    """Call Claude to generate a complete tailored resume + cover letter."""
    db = load_resume_db()
    job_types = detect_job_type(title, jd_text)
    jd_keywords = extract_jd_keywords(jd_text)
    selected = select_entries(db, job_types, jd_keywords)
    relevance_context = format_selected_context(selected)

    full_db_text = _format_full_db_for_prompt(db)

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    identity_name = IDENTITY.get("name", "the candidate") if isinstance(IDENTITY, dict) else str(IDENTITY)

    system = (
        f"You are a resume writer specializing in translating technical IC experience into PM, Senior DE, and TPM narratives for {identity_name}. "
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

        "STEP 7 — AWARDS: Surface the STAR Award (Top 10% Divisional Talent) prominently in all modes — place it in the summary/headline area or as the first item under the relevant role. This directly addresses seniority gap concerns.\n\n"

        "STEP 8 — SECTIONS TO CUT:\n"
        "- Publications: omit unless the JD explicitly references thought leadership or research.\n"
        "- Certifications unrelated to the target role: move to bottom or cut entirely.\n\n"

        "Never invent metrics, companies, or dates. Be specific, confident, and concrete.\n\n"

        "CRITICAL FORMAT RULE — SUMMARY SECTION: Do NOT include a SUMMARY section header in the resume_markdown. "
        "The summary (fit_summary) is injected separately as a SUMMARY: line after the contact line by the save function. "
        "If you include a SUMMARY section header in resume_markdown, it will create a duplicate summary on the final PDF."
    )

    target_roles = JOB_CRITERIA.get("target_roles", JOB_CRITERIA.get("roles", []))

    prompt = f"""I'm applying for: {title} at {company}
Job URL: {url}

=== JOB DESCRIPTION ===
{jd_text or "(could not fetch — use title/company context)"}

=== RELEVANCE CONTEXT (pre-selected entries for scoring guidance) ===
{relevance_context}

=== FULL RESUME DATABASE (use ALL of this to build the complete resume) ===
{full_db_text}

=== MY JOB CRITERIA ===
Target roles: {", ".join(target_roles)}
Work type: {JOB_CRITERIA.get("work_type", JOB_CRITERIA.get("remote", "Remote only"))}

Please return a JSON object with exactly these keys:
{{
  "resume_markdown": "The complete formatted resume as a markdown string. Apply all mode-specific rules from the system prompt. Follow this EXACT structure:\\n\\nDAVID OSEI-TUTU\\n980-474-6713 • ddoseitutu@gmail.com • linkedin.com/in/david-osei-tutu-89b1ab231\\n[MODE-CALIBRATED HEADLINE — 1 line]\\n\\nWORK EXPERIENCE\\n\\n[All roles newest first. Omit any self-founded/consulting role that overlaps current employment. For each role: Role Title\\nCompany | MM/YYYY - MM/YYYY or Present\\n• Most recent role: 6-7 bullets rewritten per mode rules. Prior roles: 4-5 bullets. Oldest roles: 3-4 bullets.]\\n\\nEDUCATION\\n\\n[Degree | Institution | MM/YYYY - MM/YYYY]\\n\\nAWARDS & CERTIFICATIONS\\n\\n[STAR Award first, then others relevant to the mode]\\n\\nPUBLICATIONS\\n\\n[Only if JD references thought leadership or research — otherwise omit this section entirely]\\n\\nSKILLS\\n[Mode-filtered skill list, most JD-relevant first]",
  "cover_letter": "Write a cover letter for this specific role at this specific company. Follow every rule below without exception.\\n\\nHEADER (two lines only):\\nDAVID OSEI-TUTU\\n980-474-6713 • ddoseitutu@gmail.com • linkedin.com/in/david-osei-tutu-89b1ab231\\n\\nSTRUCTURE — 4 paragraphs, no labels, no numbering:\\n\\nParagraph 1 — Hook with the company or the problem space, not David. If the JD contains a clear mission, values signal, or domain-specific challenge, open with it — make that the frame, then in 1-2 sentences place David inside it. If the JD has no meaningful company-specific signal, open with the domain problem this role exists to solve. Never open with 'I am a...' Never open with a generic compliment. Company-specific framing is the hook, not the landing.\\n\\nParagraph 2 — Make the strongest functional case. Pick the single most relevant experience from David's background and go deep: what was the situation, what did he do, what was the outcome. For any stat, add framing — over what timeframe, compared to what baseline, verified by whom. Mirror the exact language of the job description. Do not add a hand-holding sentence that explains the parallel ('That is exactly what this role requires') — make the connection self-evident and let the reader draw it.\\n\\nParagraph 3 — IC scope as a feature, not a gap. Detect whether David's experience shows broad cross-functional impact without formal direct-report authority. If yes: this is a differentiator, especially for BizOps/ops-adjacent roles. Frame it explicitly — driving adoption, alignment, and delivery through influence across organizational boundaries is harder and more transferable than headcount management. Ground it in a real example. Never imply headcount David did not have.\\n\\nParagraph 4 — Forward-looking close. One short paragraph. Connect where David is now to where this role goes. Be specific to the role — not a generic 'I look forward to hearing back.' No hedging. If you cannot write something specific here without hallucinating company details, write a single confident sentence about what David will do in the first 90 days based on the JD.\\n\\nSign-off:\\nBest,\\nDavid\\n\\nBANNED PHRASES — if any of these appear, rewrite the sentence:\\n- 'immediate and measurable impact'\\n- 'ready to take my skills to the next level'\\n- 'I am excited to continue my journey'\\n- 'sits at the intersection of'\\n- 'I have been working toward'\\n- 'There are X things that make me the perfect fit'\\n- First / Second / Finally (enumeration pattern)\\n- 'I think you will find'\\n- 'I am not willing to pass on'\\n- 'I have been following [company] for some time'\\n- 'passionate about'\\n- 'that project required exactly what this role demands' or any sentence that explicitly explains the parallel\\n- Any closing phrase that could be copy-pasted into a different cover letter unchanged\\n\\nCOMPANY RESEARCH RULE — you only have the JD as input, not independent company research. Do not hallucinate specific company facts, recent news, or executive quotes. If you cannot write a company-specific sentence with confidence from the JD alone, skip that sentence entirely. Never use brackets, placeholder text, or [INSERT:...] patterns of any kind.\\n\\nTONE: Declarative and confident. No hedging. No filler. Every sentence must earn its place — if cutting it loses nothing, cut it.",
  "fit_summary": "Write a 2-3 sentence professional summary — narrative, not a bullet list. No pronouns of any kind (no I, me, my, he, his, they). Write in the impersonal professional headline style — start directly with the professional identity or a noun phrase. Example: 'Data Engineer with 2+ years...' or 'Enterprise-scale analytics and operational delivery...' Hard cap: 3 sentences. No buzzwords (results-driven, passionate, proven track record). Calibrate to detected mode (PM / Senior DE / TPM). Must fit in 3 printed lines on a resume.",
  "keywords": ["5-10 keywords from the JD that should appear in my resume"]
}}

Return ONLY the JSON object, no markdown fences, no explanation."""

    message = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    # Strip markdown code fences if present (multiline in case there's preamble)
    raw = re.sub(r"```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```", "", raw)
    raw = raw.strip()
    # If Claude added preamble prose before the JSON, skip to the opening brace
    brace_idx = raw.find("{")
    if brace_idx > 0:
        raw = raw[brace_idx:]
    # Trim anything after the final closing brace (trailing commentary)
    last_brace = raw.rfind("}")
    if last_brace != -1:
        raw = raw[: last_brace + 1]
    if not raw:
        raise ValueError(
            f"Claude returned no JSON content. stop_reason={message.stop_reason!r}, "
            f"content_preview={message.content[0].text[:300]!r}"
        )
    return json.loads(raw)


def save_output(title: str, company: str, url: str, result: dict, row: int | None = None) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if row is not None:
        base = OUTPUT_DIR / f"{row}-david-ot-{_slug(title)}-{_slug(company)}"
    else:
        base = OUTPUT_DIR / f"{_slug(company)}-{_slug(title)}"

    # Save resume — prepend fit_summary as SUMMARY: line after contact line
    resume_path = Path(str(base) + "-resume.md")
    resume_md = result.get("resume_markdown", "")
    fit_summary = result.get("fit_summary", "").strip()
    if fit_summary:
        md_lines = resume_md.splitlines()
        # Find the contact line (second non-empty line) and insert SUMMARY: after it
        non_empty_indices = [i for i, l in enumerate(md_lines) if l.strip()]
        if len(non_empty_indices) >= 2:
            contact_idx = non_empty_indices[1]
            md_lines.insert(contact_idx + 1, f"SUMMARY: {fit_summary}")
            resume_md = "\n".join(md_lines)
    resume_path.write_text(resume_md)

    # Save cover letter
    cover_path = Path(str(base) + "-cover-letter.md")
    cover_letter = result.get("cover_letter", "")
    cover_letter = re.sub(r'\[INSERT:[^\]]*\]', '', cover_letter)
    cover_letter = re.sub(r'\[[A-Z][^\]]{0,80}\]', '', cover_letter)
    cover_letter = cover_letter.strip()
    cover_path.write_text(cover_letter)

    return resume_path, cover_path


def print_result(title: str, company: str, result: dict):
    print(f"\n{'='*70}")
    print(f"  {title} @ {company}")
    print(f"{'='*70}")
    print(f"\nFit: {result.get('fit_summary', '')}")
    print(f"\nKeywords: {', '.join(result.get('keywords', []))}")
    print(f"\n--- RESUME ---\n")
    print(result.get("resume_markdown", ""))
    print(f"\n--- COVER LETTER ---\n")
    print(result.get("cover_letter", ""))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Single job URL to tailor for")
    parser.add_argument("--title", default="", help="Job title (used with --url)")
    parser.add_argument("--company", default="", help="Company name (used with --url)")
    parser.add_argument("--min-score", type=int, default=7)
    parser.add_argument("--status", default="Validated")
    parser.add_argument("--row", type=int, default=None, help="Sheet row number (used with --url)")
    args = parser.parse_args()

    if args.url:
        jobs = [{"title": args.title or "Job", "company": args.company or "Company", "link": args.url, "sheet_row": args.row}]
    else:
        print(f"Loading {args.status} jobs from sheet (score >= {args.min_score})...")
        jobs = get_sheet_jobs(status=args.status, min_score=args.min_score)
        if not jobs:
            print(f"No jobs found with status={args.status} and score>={args.min_score}.")
            return

    print(f"Tailoring {len(jobs)} job(s)...\n")
    for j in jobs:
        title   = j.get("title", "Job")
        company = j.get("company", "Company")
        url     = j.get("link", "")
        row     = j.get("sheet_row")
        print(f"→ {title} @ {company}")
        print(f"  Fetching job description...")
        jd_text = _fetch_jd_text(url) if url else ""
        print(f"  Calling Claude...")
        try:
            result = tailor_job(title, company, url, jd_text)
            resume_path, cover_path = save_output(title, company, url, result, row=row)
            print_result(title, company, result)
            print(f"\n  Saved resume:       {resume_path}")
            print(f"  Saved cover letter: {cover_path}")
        except Exception as e:
            print(f"  [error] {e}")
            sys.exit(1)

    print(f"\nDone. Outputs in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
