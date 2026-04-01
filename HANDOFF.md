# Anelo — Session Handoff (2026-04-01)
**Repo:** github.com/david-007t/anello — main branch, latest commit `dda46e0`
**Domain:** anelo.io (Porkbun DNS → Vercel)
**Next session prompt:** "Read HANDOFF.md and continue from there."

---

## What's working

- **Job digest pipeline**: fetches jobs daily at 14:00 UTC across up to 3 roles in parallel, scores/filters (incl. experience range), deduplicates by company+role, saves to `digest_jobs`, sends email via Resend from `digest@anelo.io` (domain verified)
- **Digest page** (`/dashboard/digest`): numbered jobs (01/02/03), source badge (adzuna), consolidated duplicate postings into one card with all locations + salary range, Tailor Resume + Cover Letter + Easy Apply buttons per job
- **Clear Digest button**: deletes all digest_jobs for user, confirms before delete
- **Run Digest button**: triggers pipeline on demand with live step status (polls /status every 3s)
- **Resume tailoring**: fine-tuned PM/DE/TPM mode-detection prompt (claude-sonnet-4-6), generates both resume PDF + cover letter PDF in one call
- **Storage**: both PDFs saved to `tailored-resumes` Supabase bucket; 3-resume limit enforced (bypassed for owner)
- **Resume page** (`/dashboard/resume`): upload master resume, view/download/delete tailored resumes and cover letters
- **Preferences page**: 3 role fields, experience min/max, location, salary, company types, skills
- **validate.py**: pre-apply quality gate (5 FAIL gates, 2 WARN gates) + `/validate` endpoint
- **drafter.py**: Claude-powered LinkedIn connection/InMail/cold email drafter + `/draft` endpoint
- **apply.py**: Playwright Easy Apply for Greenhouse + Lever, Workday stubbed — `/apply` endpoint wired to UI
- **RLS enabled** on all Supabase tables (users, preferences, resumes, digest_jobs, applications)

## Infrastructure

- **Railway**: `https://anelo-production.up.railway.app` — FastAPI uvicorn, port 8000
- **Vercel**: `anelo.io`
- **Supabase**: `nyfpzapdafivahkuktww.supabase.co`

## Supabase schema notes

- `preferences` columns: `role`, `role_2`, `role_3`, `experience_min`, `experience_max`, `location`, `min_salary`, `company_types`, `skills`
- `tailored-resumes` bucket: `{userId}/{filename}.pdf` — cover letters end in `-cover-letter.pdf`
- RLS enabled on all tables — all access goes through service role key (bypasses RLS)

## Known issue — Easy Apply

`apply.py` currently returns "Manual Only" for all Adzuna-sourced jobs because:
- Adzuna `redirect_url` lands on `adzuna.com/land/ad/{id}` (their own job page)
- Playwright tries to find an employer apply link on that page but Adzuna blocks headless browsers with cookie walls before rendering the apply button

**Fix**: Add JSearch as a second job source. JSearch returns direct employer ATS URLs (Greenhouse, Lever, etc.) — no Adzuna intermediate page. Auto-apply will work immediately for those jobs.

## Next session priority

1. **Add JSearch (RapidAPI)** as a second job source alongside Adzuna
   - User needs to: sign up at rapidapi.com → subscribe to JSearch free plan → copy API key → add `RAPIDAPI_KEY` to Railway
   - Code: add `jsearch.py` fetcher to `pipeline/jobs.py`, run in parallel with Adzuna, deduplicate by URL
   - JSearch returns direct ATS URLs → auto-apply will work end-to-end
2. **Test auto-apply** against a real Greenhouse/Lever job from JSearch results
3. **drafter.py** — not yet tested end-to-end, needs a test run

## Key files

| File | Purpose |
|------|---------|
| `pipeline/api.py` | FastAPI — `/tailor`, `/validate`, `/draft`, `/apply`, `/run`, `/status`, `/health` |
| `pipeline/tailor.py` | Fine-tuned resume + cover letter generation |
| `pipeline/jobs.py` | Adzuna fetch, 3-role parallel via ThreadPoolExecutor |
| `pipeline/scorer.py` | Score + filter, experience range, 3-role match |
| `pipeline/main.py` | Daily pipeline orchestration with on_step callback |
| `pipeline/validate.py` | Pre-apply quality gate |
| `pipeline/drafter.py` | Outreach message drafter |
| `pipeline/apply.py` | Playwright Easy Apply (Greenhouse + Lever) |
| `web/app/api/tailor/route.ts` | Tailor proxy + storage limit check |
| `web/app/api/apply/route.ts` | Apply proxy to Railway |
| `web/app/api/clear-digest/route.ts` | Delete digest_jobs for user |
| `web/app/api/run-digest/route.ts` | Trigger pipeline run |
| `web/app/api/pipeline-status/route.ts` | Poll pipeline run state |
| `web/app/dashboard/digest/page.tsx` | Digest page — grouped jobs, numbered |
| `web/app/dashboard/digest/TailorButton.tsx` | Cached dual-PDF download |
| `web/app/dashboard/digest/ApplyButton.tsx` | Easy Apply button |
| `web/app/dashboard/digest/RunDigestButton.tsx` | Run + live status polling |
| `web/app/dashboard/digest/ClearDigestButton.tsx` | Clear digest with confirm |
