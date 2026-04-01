"""
validate.py — Pre-apply quality gate for the Anelo job application pipeline.

Evaluates a job dict against user preferences and returns a structured result
indicating whether the job is safe to apply to, has warnings, or should be
skipped entirely. No AI calls — pure deterministic logic.
"""

from scorer import score_job


def validate_job(job: dict, prefs: dict) -> dict:
    """
    Run pre-apply quality checks on a job.

    Returns:
        {
            "valid": bool,
            "score": int,          # 0-100
            "reasons": list[str],  # human-readable pass/fail reasons
            "warnings": list[str], # non-blocking issues
            "gate": str,           # "pass" | "warn" | "fail"
        }
    """
    reasons: list[str] = []
    warnings: list[str] = []

    # --- FAIL gates (hard blockers) ---

    # 1. job_url must be present
    if not job.get("job_url", ""):
        reasons.append("Missing job URL — cannot apply without a link")

    # 2. role (title) must be present
    if not job.get("role", ""):
        reasons.append("Missing job title/role")

    # 3. company must be present
    if not job.get("company", ""):
        reasons.append("Missing company name")

    # 4. already applied
    if job.get("applied") is True:
        reasons.append("Already applied to this job")

    # 5. score gate — scorer expects 'title' key; digest_jobs stores 'role'
    job_for_scoring = {**job, "title": job.get("role", "")}
    score = score_job(job_for_scoring, prefs)
    if score < 25:
        reasons.append(f"Score too low ({score}/100) — job is a poor match for preferences")

    # --- WARN gates (non-blocking) ---

    # 6. description missing or too short to evaluate fit
    description = job.get("description") or ""
    if len(description.strip()) < 50:
        warnings.append("Job description is missing or too short to verify fit")

    # 7. salary unknown when a minimum is expected
    salary_range = job.get("salary_range") or ""
    min_salary = prefs.get("min_salary")
    if not salary_range.strip() and min_salary:
        warnings.append(
            f"Salary not listed — preferred minimum is {min_salary}"
        )

    # --- Determine gate ---
    if reasons:
        gate = "fail"
        valid = False
    elif warnings:
        gate = "warn"
        valid = True
    else:
        gate = "pass"
        valid = True

    return {
        "valid": valid,
        "score": score,
        "reasons": reasons,
        "warnings": warnings,
        "gate": gate,
    }
