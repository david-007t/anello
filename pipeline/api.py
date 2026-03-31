"""
api.py — FastAPI HTTP server for on-demand pipeline operations.
Endpoints:
  POST /tailor  — tailor resume for a specific job, return PDF download URL
  POST /run     — trigger full pipeline run (for cron)
  GET  /health  — health check
"""
import os
import logging
import tempfile
import base64
import httpx
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
from apscheduler.schedulers.background import BackgroundScheduler

from tailor import tailor_resume
from resume_to_pdf import parse_resume_md, md_to_html_resume
from cover_letter import generate_cover_letter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI()

# Daily pipeline run at 14:00 UTC (replaces railway.toml cronSchedule)
_scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    from main import run
    _scheduler.add_job(run, "cron", hour=14, minute=0, timezone="UTC")
    _scheduler.start()
    logger.info("Scheduler started — pipeline will run daily at 14:00 UTC")

@app.on_event("shutdown")
def stop_scheduler():
    _scheduler.shutdown(wait=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


def get_db():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


class TailorRequest(BaseModel):
    job_id: str
    user_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tailor")
def tailor_endpoint(req: TailorRequest):
    db = get_db()

    # 1. Fetch job from digest_jobs
    job_res = db.table("digest_jobs").select("*").eq("id", req.job_id).limit(1).execute()
    if not job_res.data:
        raise HTTPException(status_code=404, detail="Job not found")
    job = job_res.data[0]

    # Map digest_jobs columns to what tailor_resume expects
    job_for_tailor = {
        "title": job.get("role", ""),
        "company": job.get("company", ""),
        "description": job.get("description", ""),
    }

    # 2. Fetch user's latest resume from Supabase storage
    resume_res = (
        db.table("resumes")
        .select("file_path,file_name")
        .eq("user_id", req.user_id)
        .order("uploaded_at", desc=True)
        .limit(1)
        .execute()
    )
    if not resume_res.data:
        raise HTTPException(status_code=404, detail="No resume found for user")

    resume_path = resume_res.data[0]["file_path"]
    try:
        file_bytes = db.storage.from_("resumes").download(resume_path)
        # Extract text from PDF bytes
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load resume: {e}")

    # 3. Tailor resume text via Anthropic
    tailored_text = tailor_resume(resume_text, job_for_tailor)

    # 4. Generate PDF from tailored text using Playwright
    try:
        from playwright.sync_api import sync_playwright

        parsed = parse_resume_md(tailored_text)
        html = md_to_html_resume(parsed)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            page.pdf(path=tmp_path, format="A4", print_background=True, scale=0.88)
            browser.close()

        pdf_bytes = Path(tmp_path).read_bytes()
        Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    # 5. Save to Supabase storage via REST API directly (supabase-py upload returns 400)
    role_slug = (job.get("role") or "resume").replace(" ", "-").lower()
    company_slug = (job.get("company") or "company").replace(" ", "-").lower()
    filename = f"{role_slug}-{company_slug}.pdf"
    storage_path = f"{req.user_id}/{filename}"

    try:
        storage_url = f"{SUPABASE_URL}/storage/v1/object/tailored-resumes/{storage_path}"
        upload_res = httpx.put(
            storage_url,
            content=pdf_bytes,
            headers={
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/pdf",
                "x-upsert": "true",
            },
            timeout=30,
        )
        if upload_res.status_code not in (200, 201):
            logger.error(f"Storage upload failed: {upload_res.status_code} {upload_res.text}")
    except Exception as e:
        logger.error(f"Storage upload error: {e}")

    # Always return PDF as base64 for immediate download
    return {
        "pdf_base64": base64.b64encode(pdf_bytes).decode("utf-8"),
        "filename": filename,
        "job_id": req.job_id,
    }


class CoverLetterRequest(BaseModel):
    job_id: str
    user_id: str


@app.post("/cover-letter")
def cover_letter_endpoint(req: CoverLetterRequest):
    db = get_db()

    # 1. Fetch job
    job_res = db.table("digest_jobs").select("*").eq("id", req.job_id).limit(1).execute()
    if not job_res.data:
        raise HTTPException(status_code=404, detail="Job not found")
    job = job_res.data[0]

    job_for_gen = {
        "title": job.get("role", ""),
        "company": job.get("company", ""),
        "description": job.get("description", ""),
    }

    # 2. Fetch user's resume
    resume_res = (
        db.table("resumes")
        .select("file_path,file_name")
        .eq("user_id", req.user_id)
        .order("uploaded_at", desc=True)
        .limit(1)
        .execute()
    )
    if not resume_res.data:
        raise HTTPException(status_code=404, detail="No resume found for user")

    resume_path = resume_res.data[0]["file_path"]
    try:
        file_bytes = db.storage.from_("resumes").download(resume_path)
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load resume: {e}")

    # 3. Generate cover letter
    text = generate_cover_letter(resume_text, job_for_gen)

    return {
        "cover_letter": text,
        "job_id": req.job_id,
        "role": job.get("role", ""),
        "company": job.get("company", ""),
    }


@app.post("/run")
def run_pipeline():
    """Trigger full pipeline run. Called by Railway cron."""
    try:
        from main import run
        run()
        return {"status": "complete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
