"""
api.py — FastAPI HTTP server for on-demand pipeline operations.
Endpoints:
  POST /tailor  — tailor resume + cover letter for a specific job, return PDF downloads
  POST /run     — trigger full pipeline run (for cron)
  GET  /health  — health check
"""
import os
import logging
import tempfile
import base64
import html as html_lib
import httpx
import threading
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
from apscheduler.schedulers.background import BackgroundScheduler

from tailor import tailor_job, tailor_resume
from resume_to_pdf import parse_resume_md, md_to_html_resume
from validate import validate_job
from drafter import draft_message
from apply import detect_ats, apply_to_job

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI()

# Pipeline state — updated by background thread, read by /status
_pipeline_state: dict = {
    "status": "idle",   # idle | running | complete | error
    "step": "",
    "started_at": None,
    "finished_at": None,
    "error": None,
}

# Daily pipeline run at 14:00 UTC (replaces railway.toml cronSchedule)
_scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    from main import run
    # Intraday polls every 3 hours — fetch fresh jobs + fire notifications, no batch email
    _scheduler.add_job(lambda: run(send_digest_email=False), "interval", hours=3, timezone="UTC")
    # Daily digest at 14:00 UTC — full run including batch digest email + prune stale rows
    _scheduler.add_job(lambda: run(send_digest_email=True), "cron", hour=14, minute=0, timezone="UTC")
    _scheduler.start()
    logger.info("Scheduler started — intraday polls every 3h · daily digest at 14:00 UTC")

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


def _cover_letter_to_html(text: str) -> str:
    escaped = html_lib.escape(text)
    # Preserve paragraphs
    paragraphs = escaped.split("\n\n")
    paras_html = "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in paragraphs if p.strip())
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Georgia', serif; font-size: 11pt; line-height: 1.7; color: #1a1a1a; max-width: 680px; margin: 60px auto; padding: 0 40px; }}
  p {{ margin: 0 0 1.2em 0; }}
</style>
</head>
<body>{paras_html}</body>
</html>"""


def _inject_summary(resume_markdown: str, fit_summary: str) -> str:
    """Inject fit_summary after the second non-empty line (contact line), before WORK EXPERIENCE."""
    lines = resume_markdown.split("\n")
    non_empty_count = 0
    insert_idx = len(lines)
    for i, line in enumerate(lines):
        if line.strip():
            non_empty_count += 1
            if non_empty_count == 2:
                insert_idx = i + 1
                break
    lines.insert(insert_idx, f"\nSUMMARY: {fit_summary}\n")
    return "\n".join(lines)


class TailorRequest(BaseModel):
    job_id: str
    user_id: str
    job_number: int = 0


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

    # Map digest_jobs columns to what tailor_job expects
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
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load resume: {e}")

    # 3. Tailor resume + cover letter via Anthropic
    tailor_result = tailor_job(resume_text, job_for_tailor)
    resume_markdown = tailor_result.get("resume_markdown", resume_text)
    cover_letter = tailor_result.get("cover_letter", "")
    fit_summary = tailor_result.get("fit_summary", "")

    # Inject fit_summary into resume markdown
    if fit_summary:
        resume_markdown = _inject_summary(resume_markdown, fit_summary)

    # 4. Build filenames
    role_slug = (job.get("role") or "resume").replace(" ", "-").lower()
    company_slug = (job.get("company") or "company").replace(" ", "-").lower()
    if req.job_number > 0:
        base_name = f"{req.job_number:02d}-{role_slug}-{company_slug}"
    else:
        base_name = f"{role_slug}-{company_slug}"
    resume_filename = f"{base_name}.pdf"
    cover_letter_filename = f"{base_name}-cover-letter.pdf"

    # 5. Generate resume PDF via Playwright
    try:
        from playwright.sync_api import sync_playwright

        parsed = parse_resume_md(resume_markdown)
        html = md_to_html_resume(parsed)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            resume_tmp_path = tmp.name

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            page.pdf(path=resume_tmp_path, format="A4", print_background=True, scale=0.88)
            browser.close()

        resume_pdf_bytes = Path(resume_tmp_path).read_bytes()
        Path(resume_tmp_path).unlink(missing_ok=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume PDF generation failed: {e}")

    # 6. Generate cover letter PDF via Playwright
    try:
        from playwright.sync_api import sync_playwright

        cover_html = _cover_letter_to_html(cover_letter)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            cover_tmp_path = tmp.name

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(cover_html, wait_until="networkidle")
            page.pdf(path=cover_tmp_path, format="A4", print_background=True, scale=0.88)
            browser.close()

        cover_pdf_bytes = Path(cover_tmp_path).read_bytes()
        Path(cover_tmp_path).unlink(missing_ok=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover letter PDF generation failed: {e}")

    # 7. Save both PDFs to Supabase storage via REST API
    for pdf_bytes, filename in [
        (resume_pdf_bytes, resume_filename),
        (cover_pdf_bytes, cover_letter_filename),
    ]:
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
                logger.error(f"Storage upload failed for {filename}: {upload_res.status_code} {upload_res.text}")
        except Exception as e:
            logger.error(f"Storage upload error for {filename}: {e}")

    # 8. Return both PDFs as base64
    return {
        "resume_pdf_base64": base64.b64encode(resume_pdf_bytes).decode("utf-8"),
        "cover_letter_pdf_base64": base64.b64encode(cover_pdf_bytes).decode("utf-8"),
        "resume_filename": resume_filename,
        "cover_letter_filename": cover_letter_filename,
        "job_id": req.job_id,
    }


class DraftRequest(BaseModel):
    job_id: str
    user_id: str
    message_type: str = "linkedin_connection"  # linkedin_connection | linkedin_inmail | cold_email


@app.post("/draft")
def draft_endpoint(req: DraftRequest):
    db = get_db()

    # 1. Fetch job from digest_jobs
    job_res = db.table("digest_jobs").select("*").eq("id", req.job_id).limit(1).execute()
    if not job_res.data:
        raise HTTPException(status_code=404, detail="Job not found")
    job = job_res.data[0]

    job_for_draft = {
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
        import io
        from pypdf import PdfReader
        file_bytes = db.storage.from_("resumes").download(resume_path)
        reader = PdfReader(io.BytesIO(file_bytes))
        resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not load resume: {e}")

    # 3. Draft message via Anthropic
    try:
        result = draft_message(resume_text, job_for_draft, req.message_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Message drafting failed: {e}")

    return {**result, "job_id": req.job_id}


class ApplyRequest(BaseModel):
    job_id: str
    user_id: str


@app.post("/apply")
def apply_endpoint(req: ApplyRequest):
    """Attempt Easy Apply via Playwright for Greenhouse or Lever jobs."""
    db = get_db()

    # 1. Fetch job
    job_res = db.table("digest_jobs").select("*").eq("id", req.job_id).limit(1).execute()
    if not job_res.data:
        raise HTTPException(status_code=404, detail="Job not found")
    job = job_res.data[0]
    job["url"] = job.get("job_url", "")

    # 1b. Fetch user preferences and run validation gate
    prefs_res = (
        db.table("preferences")
        .select("*")
        .eq("user_id", req.user_id)
        .limit(1)
        .execute()
    )
    prefs = prefs_res.data[0] if prefs_res.data else {}
    validation = validate_job(job, prefs)
    validate_warnings: list = []
    if validation.get("gate") == "fail":
        raise HTTPException(
            status_code=422,
            detail={
                "gate": "fail",
                "reasons": validation.get("reasons", []),
                "score": validation.get("score", 0),
            },
        )
    if validation.get("gate") == "warn":
        validate_warnings = validation.get("warnings", [])

    # 2. Fetch user info
    user_res = (
        db.table("users")
        .select("email,first_name,last_name")
        .eq("id", req.user_id)
        .limit(1)
        .execute()
    )
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_res.data[0]
    applicant = {
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "email": user.get("email", ""),
        "phone": "",
        "linkedin_url": "",
    }

    # 3. Download resume PDF to temp file
    resume_res = (
        db.table("resumes")
        .select("file_path")
        .eq("user_id", req.user_id)
        .order("uploaded_at", desc=True)
        .limit(1)
        .execute()
    )
    if not resume_res.data:
        raise HTTPException(status_code=404, detail="No resume found for user")

    resume_tmp_path = ""
    cover_tmp_path = ""
    try:
        import io
        resume_bytes = db.storage.from_("resumes").download(resume_res.data[0]["file_path"])
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(resume_bytes)
            resume_tmp_path = tmp.name

        # 4. Find latest cover letter in tailored-resumes bucket
        try:
            bucket_files = db.storage.from_("tailored-resumes").list(path=req.user_id)
            cover_files = [
                f for f in (bucket_files or [])
                if (f.get("name") or "").endswith("-cover-letter.pdf")
            ]
            if cover_files:
                cover_files.sort(key=lambda f: f.get("updated_at") or f.get("created_at") or "", reverse=True)
                cover_path = f"{req.user_id}/{cover_files[0]['name']}"
                cover_bytes = db.storage.from_("tailored-resumes").download(cover_path)
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(cover_bytes)
                    cover_tmp_path = tmp.name
        except Exception as e:
            logger.warning(f"Could not fetch cover letter: {e}")

        # 5. Run automation
        result = apply_to_job(job, applicant, resume_tmp_path, cover_tmp_path)

        # 6. Mark applied if successful
        if result.get("success"):
            db.table("digest_jobs").update({"applied": True}).eq("id", req.job_id).execute()

        return {**result, "job_id": req.job_id, "validate_warnings": validate_warnings}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for path in [resume_tmp_path, cover_tmp_path]:
            if path:
                Path(path).unlink(missing_ok=True)


@app.get("/status")
def pipeline_status():
    """Return current pipeline run state."""
    return _pipeline_state


@app.post("/run")
def run_pipeline():
    """Trigger full pipeline run in background. Returns immediately."""
    if _pipeline_state["status"] == "running":
        return {"status": "already_running"}

    def _run():
        _pipeline_state.update({
            "status": "running",
            "step": "Starting…",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "error": None,
        })
        try:
            from main import run
            run(on_step=lambda msg: _pipeline_state.update({"step": msg}), send_digest_email=True)
            _pipeline_state.update({
                "status": "complete",
                "step": "Done",
                "finished_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            _pipeline_state.update({
                "status": "error",
                "step": str(e),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            })

    threading.Thread(target=_run, daemon=True).start()
    return {"status": "started"}


class ValidateRequest(BaseModel):
    job_id: str
    user_id: str


@app.post("/validate")
def validate_endpoint(req: ValidateRequest):
    """Run pre-apply quality gate for a specific job."""
    db = get_db()

    # Fetch job from digest_jobs
    job_res = db.table("digest_jobs").select("*").eq("id", req.job_id).limit(1).execute()
    if not job_res.data:
        raise HTTPException(status_code=404, detail="Job not found")
    job = job_res.data[0]

    # Fetch user preferences
    prefs_res = (
        db.table("preferences")
        .select("*")
        .eq("user_id", req.user_id)
        .limit(1)
        .execute()
    )
    prefs = prefs_res.data[0] if prefs_res.data else {}

    return validate_job(job, prefs)
