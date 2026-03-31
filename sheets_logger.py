"""
Google Sheets logger — append job listings to the Job Tracker sheet.
"""

import os
from datetime import date, datetime
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv(override=True)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "Job Tracker"
COLUMNS = [
    "Date Found", "Title", "Company", "Source",
    "Link", "Salary", "Relevance Score", "Remote", "Status", "Notes", "Easy Apply",
]


def get_sheets_service():
    """Authenticate and return a Sheets API service object."""
    creds = None
    token_path = os.getenv("GMAIL_TOKEN_PATH", os.path.expanduser("~/anelo/token.json"))
    creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", os.path.expanduser("~/anelo/credentials.json"))

    # Sheets needs its own scope — reuse the combined token written by setup_auth.py
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, _all_scopes())

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, _all_scopes())
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)


def _all_scopes():
    return [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/spreadsheets",
    ]


def log_jobs(jobs: list[dict]):
    """
    Append a list of job dicts to the Job Tracker sheet.

    Each dict should have keys matching COLUMNS (snake_case or exact).
    Missing keys default to empty string.
    """
    if not jobs:
        return

    service = get_sheets_service()
    sheet_id = os.getenv("SHEETS_ID")
    if not sheet_id:
        raise ValueError("SHEETS_ID not set in .env")

    rows = []
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    for job in jobs:
        rows.append([
            job.get("date_found", today),
            job.get("title", ""),
            job.get("company", ""),
            job.get("source", ""),
            job.get("link", ""),
            job.get("salary", "Not listed"),
            job.get("relevance_score", ""),
            job.get("remote", ""),
            job.get("status", "Needs Tailor"),
            job.get("notes", ""),
            "TRUE" if job.get("easy_apply") else "",
        ])

    body = {"values": rows}
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()
    print(f"[sheets] Logged {len(rows)} job(s).")


def get_existing_job_keys(days: int = 7) -> set:
    """Return (title_lower, company_lower) tuples logged within the last `days` days.
    Jobs older than that can resurface if still active.
    """
    from datetime import date, timedelta
    cutoff = (date.today() - timedelta(days=days)).isoformat()

    service = get_sheets_service()
    sheet_id = os.getenv("SHEETS_ID")
    if not sheet_id:
        return set()

    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{SHEET_NAME}!A1:K5000",
    ).execute()
    rows = result.get("values", [])
    if not rows or len(rows) < 2:
        return set()

    headers = rows[0]
    col = {h: i for i, h in enumerate(headers)}
    keys = set()
    for row in rows[1:]:
        def get(col_name):
            i = col.get(col_name, -1)
            return row[i] if 0 <= i < len(row) else ""
        date_found = get("Date Found")
        # Only dedup against jobs logged in the last `days` days
        if date_found and date_found < cutoff:
            continue
        title = get("Title").lower().strip()
        company = get("Company").lower().strip()
        if title and company:
            keys.add((title, company))
    return keys


def get_sheet_jobs(status: str = "New", min_score: int = 7) -> list[dict]:
    """Read jobs from the sheet matching status and min score. Returns list of dicts with sheet_row."""
    service = get_sheets_service()
    sheet_id = os.getenv("SHEETS_ID")
    if not sheet_id:
        raise ValueError("SHEETS_ID not set in .env")

    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{SHEET_NAME}!A1:K1000",
    ).execute()
    rows = result.get("values", [])
    if not rows or len(rows) < 2:
        return []

    headers = rows[0]
    col = {h: i for i, h in enumerate(headers)}
    jobs = []
    for row_idx, row in enumerate(rows[1:], start=2):  # row 2 onward (1-indexed, row 1 = header)
        def get(col_name):
            i = col.get(col_name, -1)
            return row[i] if i >= 0 and i < len(row) else ""

        job_status = get("Status")
        score_raw = get("Relevance Score")
        source = get("Source")

        if job_status != status:
            continue
        try:
            score = int(score_raw)
        except (ValueError, TypeError):
            score = 0
        if score < min_score:
            continue

        jobs.append({
            "sheet_row": row_idx,
            "title": get("Title"),
            "company": get("Company"),
            "source": source,
            "link": get("Link"),
            "salary": get("Salary"),
            "relevance_score": score,
            "status": job_status,
            "easy_apply": get("Easy Apply") == "TRUE",
        })

    return jobs


def update_job_status(row: int, new_status: str):
    """Update the Status column for a specific row (1-indexed)."""
    service = get_sheets_service()
    sheet_id = os.getenv("SHEETS_ID")
    if not sheet_id:
        raise ValueError("SHEETS_ID not set in .env")

    # Status is column I (index 8, col letter I)
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{SHEET_NAME}!I{row}",
        valueInputOption="RAW",
        body={"values": [[new_status]]},
    ).execute()


def find_job_row(title: str, company: str) -> Optional[int]:
    """Find the sheet row number for a job by title+company match. Returns 1-indexed row or None."""
    service = get_sheets_service()
    sheet_id = os.getenv("SHEETS_ID")
    if not sheet_id:
        return None
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"{SHEET_NAME}!A1:C2000",
    ).execute()
    rows = result.get("values", [])
    if not rows or len(rows) < 2:
        return None
    headers = rows[0]
    col = {h: i for i, h in enumerate(headers)}
    title_lower = title.lower().strip()
    company_lower = company.lower().strip()
    for row_idx, row in enumerate(rows[1:], start=2):
        def get(col_name):
            i = col.get(col_name, -1)
            return row[i] if 0 <= i < len(row) else ""
        if get("Title").lower().strip() == title_lower and get("Company").lower().strip() == company_lower:
            return row_idx
    return None


def create_sheet_with_headers(sheet_id: str):
    """
    Ensure the 'Job Tracker' sheet exists and has headers in row 1.
    Called once during setup_auth.py.
    """
    service = get_sheets_service()

    # Check existing sheets
    meta = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing = [s["properties"]["title"] for s in meta.get("sheets", [])]

    if SHEET_NAME not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": SHEET_NAME}}}]},
        ).execute()
        print(f"[sheets] Created sheet '{SHEET_NAME}'.")

    # Write headers
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        body={"values": [COLUMNS]},
    ).execute()
    print(f"[sheets] Headers written: {COLUMNS}")
