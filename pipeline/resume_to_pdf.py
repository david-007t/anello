#!/usr/bin/env python3
"""
resume_to_pdf.py — Convert tailored resume/cover letter .md files to PDF using Playwright.

Usage:
    python resume_to_pdf.py --input tailored/company-role-resume.md
    python resume_to_pdf.py --all
    python resume_to_pdf.py --all --output-dir ~/Desktop/resumes/
"""

import argparse
import re
import sys
from pathlib import Path

TAILORED_DIR = Path(__file__).parent / "tailored" / "src"

SECTION_HEADERS = {
    "WORK EXPERIENCE", "EDUCATION", "AWARDS & CERTIFICATIONS",
    "PUBLICATIONS", "SKILLS", "AWARDS AND CERTIFICATIONS"
}


def is_section_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    # Skip separator lines like --- or ===
    if re.match(r'^[-=]+$', stripped):
        return False
    # All caps, no bullets, no dates with slashes
    return (stripped == stripped.upper() and
            not stripped.startswith("•") and
            len(stripped) > 2 and
            "/" not in stripped and
            "|" not in stripped)


def parse_resume_md(text: str) -> dict:
    """Parse markdown resume into structured dict."""
    lines = text.splitlines()

    result = {
        "name": "",
        "contact": "",
        "summary": "",
        "sections": []  # list of {"header": str, "content": [str]}
    }

    # First non-empty line is name, second is contact
    non_empty = [l for l in lines if l.strip()]
    if non_empty:
        result["name"] = non_empty[0].strip()
    if len(non_empty) > 1:
        result["contact"] = non_empty[1].strip()

    # Find sections — skip name, contact, and optional SUMMARY: line
    skip_count = 3
    for i, line in enumerate(lines):
        if line.startswith("SUMMARY: "):
            result["summary"] = line[len("SUMMARY: "):].strip()
            # Adjust skip_count to cover lines up through the summary line + trailing blank
            skip_count = i + 2
            break

    current_section = None
    current_content = []

    for line in lines[skip_count:]:  # skip name, contact, (summary,) blank
        if re.match(r'^[-=]+\s*$', line.strip()):
            continue  # skip separator lines entirely
        if is_section_header(line):
            if current_section is not None:
                result["sections"].append({
                    "header": current_section,
                    "content": current_content
                })
            current_section = line.strip()
            current_content = []
        else:
            current_content.append(line)

    if current_section is not None:
        result["sections"].append({
            "header": current_section,
            "content": current_content
        })

    return result


def parse_cover_letter_md(text: str) -> dict:
    """Parse cover letter markdown."""
    lines = text.splitlines()
    non_empty = [l for l in lines if l.strip()]

    result = {
        "name": non_empty[0].strip() if non_empty else "",
        "contact": non_empty[1].strip() if len(non_empty) > 1 else "",
        "body": []
    }

    # Body starts after name+contact (skip first 3 lines)
    body_lines = lines[3:]
    # Group into paragraphs
    paragraphs = []
    current_para = []
    for line in body_lines:
        if line.strip():
            current_para.append(line.strip())
        else:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
    if current_para:
        paragraphs.append(" ".join(current_para))

    result["body"] = paragraphs
    return result


def _is_role_title(line: str, content_lines: list, idx: int) -> bool:
    """Return True if line at idx looks like a role title (next non-empty line has |)."""
    if not line.strip() or line.strip().startswith("•"):
        return False
    next_nonempty = next(
        (content_lines[j].strip() for j in range(idx + 1, len(content_lines)) if content_lines[j].strip()),
        ""
    )
    return "|" in next_nonempty


def render_work_experience(content_lines: list) -> str:
    """Render WORK EXPERIENCE section HTML."""
    html = ""
    i = 0
    while i < len(content_lines):
        line = content_lines[i].rstrip()

        if not line.strip():
            i += 1
            continue

        if _is_role_title(line, content_lines, i):
            role_title = line.strip()
            i += 1
            # Skip blanks to reach Company | Dates line
            while i < len(content_lines) and not content_lines[i].strip():
                i += 1
            # Company | dates line
            if i < len(content_lines) and "|" in content_lines[i]:
                cd_line = content_lines[i].strip()
                parts = cd_line.split("|", 1)
                company = parts[0].strip()
                date = parts[1].strip()
                html += (
                    f'<div class="company-line">'
                    f'<span class="company-name">{escape_html(company)}</span>'
                    f'<span class="company-date">{escape_html(date)}</span>'
                    f'</div>\n'
                )
                i += 1
            # Role title (italic) after company line
            html += f'<div class="role-title">{escape_html(role_title)}</div>\n'
            # Collect any note lines (e.g. ⭐ award lines) before bullets
            notes = []
            while i < len(content_lines) and content_lines[i].strip() and not content_lines[i].strip().startswith("•"):
                notes.append(content_lines[i].strip())
                i += 1
            for note in notes:
                html += f'<div class="role-note">{escape_html(note)}</div>\n'
            # Bullets
            html += '<ul class="bullets">\n'
            while i < len(content_lines):
                bline = content_lines[i].rstrip()
                if bline.strip().startswith("•"):
                    html += f'  <li>{escape_html(bline.strip()[1:].strip())}</li>\n'
                    i += 1
                elif not bline.strip():
                    i += 1
                    # Peek ahead: if next non-empty is a new role title, stop
                    peek_idx = next((j for j in range(i, len(content_lines)) if content_lines[j].strip()), -1)
                    if peek_idx >= 0 and _is_role_title(content_lines[peek_idx], content_lines, peek_idx):
                        break
                else:
                    break
            html += '</ul>\n'
        elif line.strip().startswith("•"):
            html += '<ul class="bullets">\n'
            while i < len(content_lines) and content_lines[i].strip().startswith("•"):
                html += f'  <li>{escape_html(content_lines[i].strip()[1:].strip())}</li>\n'
                i += 1
            html += '</ul>\n'
        else:
            # Standalone non-bullet, non-role line — render as note
            html += f'<div class="role-note">{escape_html(line.strip())}</div>\n'
            i += 1

    return html


DIVIDER_SECTIONS = {
    "WORK EXPERIENCE", "EDUCATION", "AWARDS & CERTIFICATIONS",
    "AWARDS AND CERTIFICATIONS", "PUBLICATIONS", "SKILLS"
}


def render_section(section: dict) -> str:
    """Render a section to HTML."""
    header = section["header"]
    content = section["content"]

    if header.upper() == "SUMMARY":
        return ""

    html = f'<div class="section">\n'
    html += f'  <div class="section-header">{escape_html(header)}</div>\n'

    if header in ("WORK EXPERIENCE",):
        html += render_work_experience(content)

    elif header in ("EDUCATION",):
        # Degree line, then institution | dates
        i = 0
        while i < len(content):
            line = content[i].strip()
            if not line:
                i += 1
                continue
            if "|" in line and not line.startswith("•"):
                # Could be degree line or institution line
                # Degree line has "B.A." or "B.S." or "Master" etc OR it has "Minors:"
                if re.search(r'\b(B\.A\.|B\.S\.|M\.S\.|M\.A\.|Ph\.D|Bachelor|Master|Minor)', line, re.I) or "Minors:" in line:
                    html += f'  <div class="edu-degree">{escape_html(line)}</div>\n'
                else:
                    # Institution | Date — render two-column
                    parts = line.split("|", 1)
                    inst_name = parts[0].strip()
                    inst_date = parts[1].strip() if len(parts) > 1 else ""
                    html += (
                        f'  <div class="edu-institution">'
                        f'<span class="edu-inst-name">{escape_html(inst_name)}</span>'
                        f'<span class="edu-inst-date">{escape_html(inst_date)}</span>'
                        f'</div>\n'
                    )
            else:
                html += f'  <div class="edu-degree">{escape_html(line)}</div>\n'
            i += 1

    elif header in ("AWARDS & CERTIFICATIONS", "AWARDS AND CERTIFICATIONS"):
        # Award name | date, then issuer line
        i = 0
        while i < len(content):
            line = content[i].strip()
            if not line:
                i += 1
                continue
            if "|" in line:
                html += f'  <div class="award-name">{escape_html(line)}</div>\n'
                i += 1
                if i < len(content) and content[i].strip():
                    html += f'  <div class="award-issuer">{escape_html(content[i].strip())}</div>\n'
                    i += 1
            else:
                html += f'  <div class="award-name">{escape_html(line)}</div>\n'
                i += 1

    elif header in ("PUBLICATIONS",):
        i = 0
        while i < len(content):
            line = content[i].strip()
            if not line:
                i += 1
                continue
            if "|" in line:
                html += f'  <div class="pub-title">{escape_html(line)}</div>\n'
                i += 1
                if i < len(content) and content[i].strip():
                    html += f'  <div class="pub-venue">{escape_html(content[i].strip())}</div>\n'
                    i += 1
            else:
                html += f'  <div class="pub-title">{escape_html(line)}</div>\n'
                i += 1

    elif header in ("SKILLS",):
        html += '<ul class="bullets">\n'
        for line in content:
            line = line.strip()
            if not line:
                continue
            if line.startswith("•"):
                line = line[1:].strip()
            # Handle **Bold:** rest pattern
            bold_match = re.match(r'\*\*(.+?)\*\*[:\s]*(.*)', line)
            if bold_match:
                label = bold_match.group(1)
                rest = bold_match.group(2).strip()
                if rest:
                    html += f'  <li><strong>{escape_html(label)}:</strong> {escape_html(rest)}</li>\n'
                else:
                    html += f'  <li><strong>{escape_html(label)}</strong></li>\n'
            else:
                html += f'  <li>{escape_html(line)}</li>\n'
        html += '</ul>\n'

    else:
        # Generic section
        for line in content:
            if line.strip():
                html += f'  <p>{escape_html(line.strip())}</p>\n'

    html += '</div>\n'
    return html


def escape_html(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


CSS = """
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'EB Garamond', 'Palatino Linotype', Palatino, 'Book Antiqua', Georgia, serif;
    font-size: 10pt;
    line-height: 1.4;
    color: #111;
    background: #fff;
}

@page {
    size: A4;
    margin: 0.5in 0.6in;
}

.name {
    font-size: 24pt;
    font-weight: 700;
    font-variant: small-caps;
    color: #111;
    text-align: center;
    letter-spacing: 0.03em;
    margin-bottom: 3px;
}

.contact {
    font-size: 9.5pt;
    text-align: center;
    color: #222;
    margin-bottom: 6px;
}

.summary {
    font-size: 10pt;
    line-height: 1.5;
    text-align: center;
    color: #333;
    margin: 6px 0 10px 0;
}

.section {
    margin-bottom: 5px;
}

.section-header {
    color: #111;
    font-weight: 700;
    font-size: 10.5pt;
    font-family: 'EB Garamond', serif;
    margin-top: 11px;
    margin-bottom: 0px;
    padding-bottom: 2px;
    border-bottom: 1px solid #111;
    display: block;
}

.role-title {
    font-style: normal;
    font-size: 10pt;
    margin-top: 3px;
    margin-bottom: 2px;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}

.role-location {
    font-style: normal;
    font-size: 9.5pt;
    color: #111;
    white-space: nowrap;
}

.company-line {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 10pt;
    margin-top: 8px;
    margin-bottom: 1px;
}
.company-name {
    font-weight: 700;
    color: #111;
}
.company-date {
    font-weight: 400;
    color: #111;
    font-size: 9.5pt;
    white-space: nowrap;
}

ul.bullets {
    margin: 0;
    padding-left: 16px;
    line-height: 1.45;
}

ul.bullets li {
    margin-bottom: 3px;
    font-size: 10pt;
}

.edu-degree {
    font-weight: 600;
    font-size: 10pt;
    margin-bottom: 1px;
}

.edu-institution {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 10pt;
    margin-bottom: 4px;
}

.edu-inst-name {
    font-weight: 700;
}

.edu-inst-date {
    font-weight: 400;
    font-size: 9.5pt;
    white-space: nowrap;
}

.award-name {
    font-weight: 600;
    font-size: 10pt;
    margin-top: 4px;
    margin-bottom: 1px;
}

.award-issuer {
    font-size: 9.5pt;
    color: #333;
    margin-bottom: 2px;
}

.pub-title {
    font-weight: 600;
    font-size: 10pt;
    margin-top: 4px;
    margin-bottom: 1px;
}

.pub-venue {
    font-size: 9.5pt;
    color: #333;
}

.role-note {
    font-size: 9pt;
    font-style: italic;
    color: #333;
    margin-bottom: 2px;
}

.skills {
    font-size: 9.5pt;
    line-height: 1.5;
}
"""

COVER_CSS = """
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Dancing+Script:wght@600&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: 'EB Garamond', 'Palatino Linotype', Palatino, Georgia, serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #111;
    background: #f5f5f5;
}

@page {
    size: A4;
    margin: 0.7in 0.8in;
    background: #f5f5f5;
}

.cover-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
}

.cover-header-left {
    flex: 1;
}

.cover-name {
    font-size: 22pt;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #111;
    margin-bottom: 4px;
    line-height: 1.1;
}

.cover-title {
    font-size: 11pt;
    font-weight: 700;
    color: #222;
}

.cover-contact {
    text-align: right;
    font-size: 9.5pt;
    color: #333;
    line-height: 1.7;
}

.cover-rule {
    border: none;
    border-top: 1px solid #888;
    margin: 0 0 16px 0;
}

.cover-date {
    text-align: right;
    font-size: 10.5pt;
    margin-bottom: 14px;
    color: #111;
}

.cover-recipient {
    font-size: 10.5pt;
    line-height: 1.6;
    margin-bottom: 14px;
    color: #111;
}

.cover-job-ref {
    font-size: 10pt;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 700;
    margin-bottom: 14px;
    color: #111;
}

.cover-salutation {
    font-size: 10.5pt;
    margin-bottom: 12px;
}

.cover-body p {
    font-size: 12pt;
    line-height: 1.85;
    margin-bottom: 20px;
    text-align: justify;
    color: #111;
}

.cover-signoff {
    font-size: 10.5pt;
    line-height: 1.8;
    margin-top: 16px;
}

.cover-signature {
    font-family: 'Dancing Script', cursive;
    font-size: 20pt;
    font-weight: 600;
    line-height: 1.2;
    margin-top: 2px;
    color: #111;
}
"""


def md_to_html_resume(parsed: dict) -> str:
    sections_html = "".join(render_section(s) for s in parsed["sections"])
    summary_html = f'<div class="summary">{escape_html(parsed["summary"])}</div>\n' if parsed.get("summary") else ""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&display=swap" rel="stylesheet">
<style>
{CSS}
</style>
</head>
<body>
<div class="name">{escape_html(parsed['name'])}</div>
<div class="contact">{escape_html(parsed['contact'])}</div>
{summary_html}{sections_html}
</body>
</html>"""


SIGNOFF_PREFIXES = ("Best,", "Sincerely,", "Warm regards,", "Regards,", "Thank you,")

AUTHOR_NAME = "David Osei-Tutu"


def md_to_html_cover_letter(parsed: dict) -> str:
    import datetime
    today = datetime.date.today()
    today_str = f"{today.strftime('%B')} {today.day}, {today.year}"

    # Split contact into individual lines for stacked display
    contact_raw = parsed.get("contact", "")
    contact_parts = [p.strip() for p in re.split(r"[|·•]", contact_raw) if p.strip()]
    contact_html = "<br>".join(escape_html(p) for p in contact_parts)

    # Separate body paragraphs from sign-off
    body_paragraphs = []
    signoff_parts = []
    found_signoff = False
    for p in parsed["body"]:
        if not found_signoff and any(p.startswith(prefix) for prefix in SIGNOFF_PREFIXES):
            found_signoff = True
            # Keep the closing word but we'll render our own structured sign-off
        elif not found_signoff:
            body_paragraphs.append(p)

    body_html = "".join(f"<p>{escape_html(p)}</p>\n" for p in body_paragraphs)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Dancing+Script:wght@600&display=swap" rel="stylesheet">
<style>
{COVER_CSS}
</style>
</head>
<body>
<div class="cover-header">
  <div class="cover-header-left">
    <div class="cover-name">{escape_html(parsed['name'])}</div>
  </div>
  <div class="cover-contact">{contact_html}</div>
</div>
<hr class="cover-rule">
<div class="cover-date">{today_str}</div>
<div class="cover-salutation">Dear Hiring Manager,</div>
<div class="cover-body">
{body_html}
</div>
<div class="cover-signoff">
  Sincerely,<br>
  {escape_html(AUTHOR_NAME)}<br>
  <span class="cover-signature">{escape_html(AUTHOR_NAME)}</span>
</div>
</body>
</html>"""


def convert_md_to_pdf(input_path: Path, output_dir: Path = None) -> Path:
    """Convert a single .md file to PDF. Returns output PDF path."""
    text = input_path.read_text(encoding="utf-8")

    is_cover = input_path.stem.endswith("-cover-letter")

    if is_cover:
        parsed = parse_cover_letter_md(text)
        html = md_to_html_cover_letter(parsed)
    else:
        parsed = parse_resume_md(text)
        html = md_to_html_resume(parsed)

    out_dir = output_dir if output_dir else input_path.parent.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / (input_path.stem + ".pdf")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            scale=0.88,
        )
        browser.close()

    input_path.unlink()
    return pdf_path


def main():
    parser = argparse.ArgumentParser(description="Convert resume/cover letter .md to PDF")
    parser.add_argument("--input", help="Path to a single .md file")
    parser.add_argument("--all", action="store_true", help="Process all .md files in tailored/")
    parser.add_argument("--output-dir", help="Output directory (default: same as input)")
    args = parser.parse_args()

    if not args.input and not args.all:
        parser.print_help()
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else None

    if args.all:
        md_files = sorted(TAILORED_DIR.glob("*.md"))
        if not md_files:
            print(f"No .md files found in {TAILORED_DIR}")
            sys.exit(1)
        print(f"Found {len(md_files)} .md file(s) to convert...")
        for md_path in md_files:
            print(f"  Converting {md_path.name}...")
            try:
                pdf_path = convert_md_to_pdf(md_path, output_dir)
                size_kb = pdf_path.stat().st_size // 1024
                print(f"    → {pdf_path.name} ({size_kb}KB)")
            except Exception as e:
                print(f"    ERROR: {e}")
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"File not found: {input_path}")
            sys.exit(1)
        print(f"Converting {input_path.name}...")
        try:
            pdf_path = convert_md_to_pdf(input_path, output_dir)
            size_kb = pdf_path.stat().st_size // 1024
            print(f"Done: {pdf_path} ({size_kb}KB)")
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
