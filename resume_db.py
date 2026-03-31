#!/usr/bin/env python3
"""resume_db.py — CLI for managing resume_db.json"""

import argparse
import json
import os
import sys
from collections import Counter

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resume_db.json")


def load_db():
    with open(DB_PATH, "r") as f:
        return json.load(f)


def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)
    print(f"Saved to {DB_PATH}")


def fmt_date(d):
    if not d:
        return "Present"
    return d[:7]  # YYYY-MM


# ── list ──────────────────────────────────────────────────────────────────────

def cmd_list(args):
    db = load_db()
    sections = args.section.split(",") if args.section else ["experience", "skills", "projects", "education", "awards", "publications"]

    for section in sections:
        section = section.strip()
        if section not in db:
            print(f"[WARN] Unknown section: {section}")
            continue

        print(f"\n=== {section.upper()} ===")
        items = db[section]

        if section == "experience":
            for e in items:
                end = fmt_date(e.get("end_date"))
                start = fmt_date(e.get("start_date"))
                n = len(e.get("bullets", []))
                print(f"  [{e['id']}] {e['role']} @ {e['company']} ({start} → {end}) — {n} bullets")

        elif section == "skills":
            for s in items:
                name = s.get("name", "?")
                prof = s.get("proficiency", "?")
                # use a slug-like id derived from name
                slug = name.lower().replace(" ", "-").replace("/", "-")
                print(f"  [{slug}] {name} — {prof}")

        elif section == "projects":
            for p in items:
                print(f"  [{p['id']}] {p['name']}")

        elif section == "education":
            for e in items:
                print(f"  {e['degree']} {e['field']} @ {e['institution']} ({fmt_date(e.get('graduation_date'))})")

        elif section == "awards":
            for a in items:
                print(f"  {a['name']} — {a['issuer']} ({fmt_date(a.get('date'))})")

        elif section == "publications":
            for p in items:
                print(f"  {p['title']} [{p['venue']}] ({fmt_date(p.get('date'))})")


# ── show ──────────────────────────────────────────────────────────────────────

def cmd_show(args):
    db = load_db()
    entry_id = args.id

    # Search experience first (primary use case), then projects
    found = None
    for section in ("experience", "projects"):
        for item in db.get(section, []):
            if item.get("id") == entry_id:
                found = (section, item)
                break
        if found:
            break

    if not found:
        print(f"No entry found with id: {entry_id}")
        sys.exit(1)

    section, e = found

    if section == "experience":
        end = fmt_date(e.get("end_date"))
        start = fmt_date(e.get("start_date"))
        print(f"\n{e['role']} @ {e['company']}")
        print(f"Dates     : {start} → {end}")
        print(f"Role types: {', '.join(e.get('role_types', []))}")
        print(f"Seniority : {', '.join(e.get('seniority', []))}")
        print(f"Industry  : {', '.join(e.get('industry', []))}")
        print(f"Skills    : {', '.join(e.get('skills', []))}")
        print(f"\nBullets ({len(e.get('bullets', []))}):")
        for i, b in enumerate(e.get("bullets", []), 1):
            metric = f" [{b.get('impact_metric')}]" if b.get("impact_metric") else ""
            print(f"\n  {i}. {b['text']}{metric}")
            print(f"     impact_type : {b.get('impact_type', '?')}")
            print(f"     tags        : {', '.join(b.get('tags', []))}")

    elif section == "projects":
        print(f"\n{e['name']}")
        print(f"Description: {e.get('description', '')}")
        print(f"Outcome    : {e.get('outcome', '')}")
        print(f"Skills     : {', '.join(e.get('skills', []))}")
        print(f"Role types : {', '.join(e.get('role_types', []))}")
        print(f"Tags       : {', '.join(e.get('tags', []))}")


# ── validate ──────────────────────────────────────────────────────────────────

REQUIRED_EXPERIENCE_FIELDS = {"id", "role", "company", "start_date", "bullets", "role_types"}
REQUIRED_BULLET_FIELDS = {"text", "tags", "impact_type"}

def cmd_validate(args):
    db = load_db()
    issues = []
    tag_counter = Counter()

    for e in db.get("experience", []):
        eid = e.get("id", "<no-id>")

        missing = REQUIRED_EXPERIENCE_FIELDS - set(e.keys())
        if missing:
            issues.append(f"[{eid}] Missing fields: {', '.join(sorted(missing))}")

        bullets = e.get("bullets", [])
        if not isinstance(bullets, list):
            issues.append(f"[{eid}] 'bullets' is not a list")
            continue

        for i, b in enumerate(bullets):
            bmissing = REQUIRED_BULLET_FIELDS - set(b.keys())
            if bmissing:
                issues.append(f"[{eid}] bullet {i+1}: missing fields: {', '.join(sorted(bmissing))}")
            for tag in b.get("tags", []):
                tag_counter[tag] += 1

    # Check for likely typos: tags that differ only by _ vs -
    all_tags = list(tag_counter.keys())
    typo_suspects = []
    for t in all_tags:
        normalized = t.replace("-", "_")
        for other in all_tags:
            if other != t and other.replace("-", "_") == normalized:
                pair = tuple(sorted([t, other]))
                if pair not in [tuple(sorted(x)) for x in typo_suspects]:
                    typo_suspects.append([t, other])

    print("\n=== VALIDATE ===")

    if issues:
        print(f"\nISSUES ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nStructure: PASS")

    print(f"\nTag frequency (top 30):")
    for tag, count in tag_counter.most_common(30):
        print(f"  {count:3d}  {tag}")

    if typo_suspects:
        print(f"\nPossible tag typos (hyphen vs underscore):")
        for pair in typo_suspects:
            print(f"  '{pair[0]}' vs '{pair[1]}'")
    else:
        print("\nNo tag typos detected.")

    if not issues:
        print("\nResult: PASS")
    else:
        print(f"\nResult: FAIL — {len(issues)} issue(s) found")


# ── add-bullet ────────────────────────────────────────────────────────────────

def cmd_add_bullet(args):
    db = load_db()
    experience = db.get("experience", [])

    print("\nExperience entries:")
    for i, e in enumerate(experience, 1):
        end = fmt_date(e.get("end_date"))
        start = fmt_date(e.get("start_date"))
        print(f"  {i}. [{e['id']}] {e['role']} @ {e['company']} ({start} → {end})")

    entry_id = input("\nEnter entry ID: ").strip()
    target = next((e for e in experience if e["id"] == entry_id), None)
    if not target:
        print(f"No entry found with id: {entry_id}")
        sys.exit(1)

    text = input("Bullet text: ").strip()
    if not text:
        print("Bullet text cannot be empty.")
        sys.exit(1)

    metric_raw = input("Impact metric (or press Enter to skip): ").strip()
    impact_metric = metric_raw if metric_raw else None

    impact_type = input("Impact type [quantified/qualitative]: ").strip().lower()
    if impact_type not in ("quantified", "qualitative"):
        print(f"Invalid impact_type '{impact_type}'. Must be 'quantified' or 'qualitative'.")
        sys.exit(1)

    tags_raw = input("Tags (comma-separated, e.g. data-eng,sql,etl): ").strip()
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    bullet = {
        "text": text,
        "impact_metric": impact_metric,
        "impact_type": impact_type,
        "tags": tags,
    }

    target["bullets"].append(bullet)
    save_db(db)
    print(f"\nAdded bullet to [{entry_id}]:")
    print(f"  {text}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Resume DB CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="Print all entries by section")
    p_list.add_argument(
        "--section",
        help="Filter by section(s): experience,skills,projects,education,awards,publications",
        default=None,
    )
    p_list.set_defaults(func=cmd_list)

    # show
    p_show = sub.add_parser("show", help="Show full detail for an entry by id")
    p_show.add_argument("id", help="Entry id slug (e.g. nutanix-de2)")
    p_show.set_defaults(func=cmd_show)

    # validate
    p_val = sub.add_parser("validate", help="Validate structure and report tag frequency")
    p_val.set_defaults(func=cmd_validate)

    # add-bullet
    p_add = sub.add_parser("add-bullet", help="Interactively add a bullet to an experience entry")
    p_add.set_defaults(func=cmd_add_bullet)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
