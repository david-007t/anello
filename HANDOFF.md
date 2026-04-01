# Anelo — Session Handoff (2026-03-31)
**Repo:** github.com/david-007t/anello — main branch, latest commit `127806f`
**Domain:** anelo.io (Porkbun DNS → Vercel)
**Next session prompt:** "Read HANDOFF.md and continue from there."

---

## What's working

- **Job digest pipeline**: fetches jobs daily at 14:00 UTC across up to 3 roles in parallel, scores/filters (incl. experience range), saves to `digest_jobs`, sends email via Resend
- **Digest page** (`/dashboard/digest`): shows numbered jobs, "Tailor Resume" + "Cover Letter" buttons per job
- **Resume tailoring**: fine-tuned PM/DE/TPM mode-detection prompt (claude-sonnet-4-6), generates both resume PDF + cover letter PDF in one call, numbered filenames (`01-product-manager-fmg-suite.pdf`)
- **Storage**: both PDFs saved to `tailored-resumes` Supabase bucket; 3-resume limit enforced (bypassed for owner `user_3BiDX7oXc0OkkXgLwwCIWK4VMu0`)
- **Resume page** (`/dashboard/resume`): upload master resume, view/download/delete tailored resumes and cover letters in separate sections
- **Preferences page**: 3 role fields (`role`, `role_2`, `role_3`), experience min/max, location, salary, company types, skills
- **Overview stats**: applications sent + jobs in digest today (fixed)

## Infrastructure

- **Railway**: `https://anelo-production.up.railway.app` — FastAPI uvicorn, port 8000
- **Vercel**: `anelo.io`
- **Supabase**: `nyfpzapdafivahkuktww.supabase.co`

## Supabase schema notes

- `preferences` columns: `role`, `role_2`, `role_3`, `experience_min`, `experience_max`, `location`, `min_salary`, `company_types`, `skills`
- `tailored-resumes` bucket: `{userId}/{filename}.pdf` — cover letters end in `-cover-letter.pdf`

## Remaining work (priority order)

1. **apply.py** — Easy Apply automation via Playwright (full session, not started)
   - Target ATS: Greenhouse, Lever, Workday
   - Needs: form detection, field mapping, file upload, confirmation scraping
   - Hook into `digest_jobs`: mark `applied=true` after success

2. **validate.py** — pre-apply quality gate (partially built, not integrated)

3. **Resend domain verification** (`anelo.io`) — digest emails currently send from Resend default domain; needs DNS records added

4. **drafter.py** — message drafter, built but not end-to-end tested

## Key files

| File | Purpose |
|------|---------|
| `pipeline/api.py` | FastAPI — `/tailor`, `/run`, `/health` |
| `pipeline/tailor.py` | Fine-tuned resume + cover letter generation (returns JSON) |
| `pipeline/jobs.py` | Adzuna fetch, 3-role parallel via ThreadPoolExecutor |
| `pipeline/scorer.py` | Score + filter, experience range, 3-role match |
| `pipeline/main.py` | Daily pipeline orchestration |
| `web/app/api/tailor/route.ts` | Tailor proxy + storage limit check |
| `web/app/api/tailored-resumes/route.ts` | List/delete stored PDFs (split resumes vs cover letters) |
| `web/app/dashboard/digest/TailorButton.tsx` | Cached single-call dual-PDF download |
</content>
