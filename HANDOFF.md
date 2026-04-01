# Anelo — Session Handoff (2026-04-01)
**Repo:** github.com/david-007t/anello — main branch, latest commit `00c3c6d`
**Domain:** anelo.io (Porkbun DNS → Vercel)
**Next session prompt:** "Read HANDOFF.md and continue from there."

---

## What's working

- **Job digest pipeline**: fetches jobs daily at 14:00 UTC, deduplicates by company+role, saves to `digest_jobs`, sends email via Resend from `digest@anelo.io`
- **Two job sources**: Adzuna + JSearch (RapidAPI) run in parallel across up to 3 roles. JSearch returns direct employer ATS URLs; Adzuna returns Adzuna redirect pages.
- **Digest page** (`/dashboard/digest`): numbered jobs (01/02/03), source badge (adzuna/jsearch), consolidated duplicate postings, Tailor Resume + Cover Letter + Easy Apply buttons, Clear Digest + Run Digest buttons with live status
- **Resume tailoring**: PM/DE/TPM mode-detection prompt, dual PDF (resume + cover letter), saved to Supabase storage
- **Easy Apply**: Playwright automation for Greenhouse + Lever. Works on JSearch jobs (direct ATS URLs). Adzuna jobs return "Manual Only" (Adzuna blocks headless browsers before showing employer link).
- **validate.py**: pre-apply quality gate + `/validate` endpoint
- **drafter.py**: Claude-powered LinkedIn/InMail/cold email drafter + `/draft` endpoint (not yet tested end-to-end)
- **RLS enabled** on all Supabase tables

## Infrastructure

- **Railway**: `https://anelo-production.up.railway.app` — FastAPI uvicorn, port 8000
- **Vercel**: `anelo.io`
- **Supabase**: `nyfpzapdafivahkuktww.supabase.co`
- **Railway env vars**: `ANTHROPIC_API_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ADZUNA_APP_ID`, `ADZUNA_API_KEY`, `RESEND_API_KEY`, `RAPIDAPI_KEY` ✓

## Open decision — Adzuna vs JSearch only

JSearch returns direct ATS URLs (auto-apply works). Adzuna returns Adzuna redirect pages (auto-apply blocked). Question: drop Adzuna entirely once JSearch volume is confirmed sufficient, or keep both for manual-apply fallback?

**Next step**: run one digest with both active, count how many JSearch jobs come back. If 15+, drop Adzuna. If fewer, keep both.

## Supabase schema

- `preferences`: `role`, `role_2`, `role_3`, `experience_min`, `experience_max`, `location`, `min_salary`, `company_types`, `skills`
- `tailored-resumes` bucket: `{userId}/{filename}.pdf` — cover letters end in `-cover-letter.pdf`
- All tables have RLS enabled — all access via service role key (bypasses RLS)

## Remaining work (priority order)

1. **Evaluate JSearch volume** — run digest, count jsearch-sourced jobs, decide whether to drop Adzuna
2. **Test Easy Apply end-to-end** — find a JSearch job that lands on Greenhouse/Lever, hit Apply, verify `applied=true` gets set in DB
3. **Test drafter.py** — hit `/draft` endpoint, verify LinkedIn connection message quality
4. **validate.py integration** — currently built + endpoint exists but not called automatically before apply; consider calling it in the `/apply` flow
5. **Add more roles/sources if needed** — The Muse (free API, startup-focused) is easy to add if JSearch volume is low for certain role types

## Key files

| File | Purpose |
|------|---------|
| `pipeline/api.py` | FastAPI — `/tailor`, `/validate`, `/draft`, `/apply`, `/run`, `/status`, `/health` |
| `pipeline/jobs.py` | Adzuna + JSearch fetch, 3-role parallel, dedup by URL |
| `pipeline/apply.py` | Playwright Easy Apply (Greenhouse + Lever), ATS detection via redirect resolution |
| `pipeline/tailor.py` | Resume + cover letter generation |
| `pipeline/scorer.py` | Score + filter, experience range |
| `pipeline/main.py` | Daily pipeline with on_step callback for live status |
| `pipeline/validate.py` | Pre-apply quality gate |
| `pipeline/drafter.py` | Outreach message drafter |
| `web/app/dashboard/digest/page.tsx` | Digest — grouped, numbered, source-badged |
| `web/app/dashboard/digest/ApplyButton.tsx` | Easy Apply button |
| `web/app/dashboard/digest/RunDigestButton.tsx` | Run + live status polling |
| `web/app/dashboard/digest/ClearDigestButton.tsx` | Clear digest |
| `web/app/api/apply/route.ts` | Apply proxy to Railway |
| `web/app/api/run-digest/route.ts` | Run pipeline proxy |
| `web/app/api/pipeline-status/route.ts` | Status polling proxy |
| `web/app/api/clear-digest/route.ts` | Delete digest_jobs for user |
