#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.expanduser("~/anelo"))
os.chdir(os.path.expanduser("~/anelo"))
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/anelo/.env"))
from sheets_logger import get_sheets_service
svc = get_sheets_service()
sid = os.getenv("SHEETS_ID")
svc.spreadsheets().values().clear(spreadsheetId=sid, range="Job Tracker!A2:J5000").execute()
print("Sheet cleared.")
