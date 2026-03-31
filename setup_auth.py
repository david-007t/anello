#!/usr/bin/env python3
"""
One-time setup script.

Handles:
1. Google OAuth flow (Gmail + Sheets combined token)
2. Creates a new "Job Tracker" Google Sheet and saves the ID to .env
3. Writes headers to the sheet

Run once after placing credentials.json in ~/anelo/:
    python setup_auth.py
"""

import os
import re
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv, set_key

load_dotenv(override=True)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",  # needed to create sheets
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", os.path.join(BASE_DIR, "token.json"))
CREDS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", os.path.join(BASE_DIR, "credentials.json"))

SHEET_COLUMNS = [
    "Date Found", "Title", "Company", "Source",
    "Link", "Salary", "Relevance Score", "Remote", "Status", "Notes",
]


def run_oauth() -> Credentials:
    print("\n[1/3] Running Google OAuth...")

    if not os.path.exists(CREDS_PATH):
        print(f"\n  ERROR: credentials.json not found at {CREDS_PATH}")
        print("  Please download it from Google Cloud Console and place it there.")
        sys.exit(1)

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    print("  OAuth complete. Token saved.")
    return creds


def create_sheet(creds: Credentials) -> str:
    print("\n[2/3] Creating 'Job Tracker' Google Sheet...")

    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    # Check if SHEETS_ID already set
    existing_id = os.getenv("SHEETS_ID", "").strip()
    if existing_id:
        print(f"  SHEETS_ID already set: {existing_id}. Skipping creation.")
        return existing_id

    # Create new spreadsheet
    spreadsheet = {
        "properties": {"title": "Job Tracker"},
        "sheets": [{"properties": {"title": "Job Tracker"}}],
    }
    result = sheets_service.spreadsheets().create(body=spreadsheet).execute()
    sheet_id = result["spreadsheetId"]
    tab_id = result["sheets"][0]["properties"]["sheetId"]
    sheet_url = result.get("spreadsheetUrl", f"https://docs.google.com/spreadsheets/d/{sheet_id}")

    print(f"  Created: {sheet_url}")

    # Write headers
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range="Job Tracker!A1",
        valueInputOption="RAW",
        body={"values": [SHEET_COLUMNS]},
    ).execute()
    print(f"  Headers written: {SHEET_COLUMNS}")

    # Format header row — bold + freeze
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={
            "requests": [
                {
                    "repeatCell": {
                        "range": {"sheetId": tab_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat.bold",
                    }
                },
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": tab_id, "gridProperties": {"frozenRowCount": 1}},
                        "fields": "gridProperties.frozenRowCount",
                    }
                },
            ]
        },
    ).execute()

    return sheet_id


def save_sheet_id_to_env(sheet_id: str):
    print(f"\n[3/3] Saving SHEETS_ID to .env...")
    set_key(ENV_PATH, "SHEETS_ID", sheet_id)
    print(f"  SHEETS_ID={sheet_id}")


def main():
    print("=" * 60)
    print("  Anelo — One-Time Setup")
    print("=" * 60)

    creds = run_oauth()
    sheet_id = create_sheet(creds)
    save_sheet_id_to_env(sheet_id)

    print("\n" + "=" * 60)
    print("  Setup complete!")
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{sheet_id}")
    print()
    print("  Next steps:")
    print("  1. Add your ANTHROPIC_API_KEY to ~/anelo/.env")
    print("  2. Run: python digest.py   (test the digest)")
    print("  3. Run: python watcher.py  (test the watcher)")
    print("  4. Run: python drafter.py  (test the drafter)")
    print("=" * 60)


if __name__ == "__main__":
    main()
