#!/usr/bin/env python3
"""
Run once to save your LinkedIn session for job scraping and Easy Apply.
Uses email/password login stored in .env — auto-fills both fields.
If LinkedIn shows a verification/CAPTCHA, complete it in the browser window.
Session saves automatically once you reach the feed.

Usage:
    python save_linkedin_session.py
"""
import json, os, sys, time
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv(Path(__file__).parent / ".env", override=True)

email = os.getenv("LINKEDIN_EMAIL")
password = os.getenv("LINKEDIN_PASSWORD")

if not email or not password:
    print("ERROR: Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env first.")
    sys.exit(1)

SESSION_PATH = Path(__file__).parent / "linkedin_session" / "state.json"
SESSION_PATH.parent.mkdir(exist_ok=True)

LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-infobars",
]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

print(f"Logging into LinkedIn as {email}...")
print("A browser window will open. If you see a verification step, complete it there.")
print("Session saves automatically once you reach the LinkedIn feed.")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=80, args=LAUNCH_ARGS)
    ctx = browser.new_context(user_agent=UA)
    page = ctx.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    page.goto("https://www.linkedin.com/login", timeout=20000)
    page.wait_for_selector('#username', timeout=15000)
    time.sleep(1)
    page.fill('#username', email)
    time.sleep(0.5)
    page.fill('#password', password)
    time.sleep(0.5)
    page.click('button[type="submit"]')
    print("Credentials submitted. Waiting for feed (up to 5 min for any verification)...")

    # Poll for up to 5 minutes
    for i in range(60):
        time.sleep(5)
        url = page.url
        if "/feed" in url and "checkpoint" not in url and "login" not in url:
            print(f"✅ On feed after {(i+1)*5}s")
            break
        if i % 6 == 5:
            print(f"  Still waiting... ({(i+1)*5}s) — current: {url}")
    else:
        print(f"⚠️  Timed out. Saving session anyway from: {page.url}")

    ctx.storage_state(path=str(SESSION_PATH))
    print(f"✅ Session saved to {SESSION_PATH}")
    browser.close()
