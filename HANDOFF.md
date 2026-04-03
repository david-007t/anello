# Anelo — Session Handoff (2026-04-03)
**Repo:** github.com/david-007t/anello — main branch
**Domain:** anelo.io (Porkbun DNS → Vercel)
**Next session prompt:** "Read HANDOFF.md and continue from there."

---

## 🔴 ACTIVE BUG — UI shows "No digest yet" (root cause identified, NOT fixed yet)

### What's confirmed
- `digest_jobs` table HAS rows — confirmed via Supabase SQL editor (`select * from digest_jobs` returns many rows)
- All rows have correct Clerk user_id format: `user_3BiDX7oXc0OkkXgLwwCIWK4VMu0`
- Email notifications work ✓, ntfy works ✓ — pipeline is running and saving data
- The UI query returns nothing — the page shows "No digest yet" despite rows being in the DB

### Root cause (high confidence)
`web/lib/supabase.ts` — `supabaseAdmin()` reads `SUPABASE_SERVICE_ROLE_KEY` from env:
```ts
export function supabaseAdmin() {
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";
  return createClient(supabaseUrl, serviceKey);
}
```
`SUPABASE_SERVICE_ROLE_KEY` is set in **Railway** but almost certainly **NOT set in Vercel**.
With an empty service key, Supabase connects with no auth → RLS blocks all reads → `data` is `[]`, no error thrown → page renders "No digest yet."

### Fix (do this first)
1. Go to **Vercel → anelo project → Settings → Environment Variables**
2. Add `SUPABASE_SERVICE_ROLE_KEY` = (same value as Railway)
3. Also confirm `NEXT_PUBLIC_SUPABASE_URL` is set in Vercel
4. Redeploy (or trigger a new deploy)
5. Go to `/dashboard/digest` — jobs should appear immediately (they're already in the DB)

### Verify fix worked
Run this in Supabase SQL editor — confirm it returns rows:
```sql
select * from digest_jobs where user_id = 'user_3BiDX7oXc0OkkXgLwwCIWK4VMu0';
```
If rows exist there but UI still shows empty after Vercel env fix → check Vercel function logs for `[digest] supabase error:` output.

---

## What's working

- **Job digest pipeline**: fetches jobs on demand (Run Digest button) + daily at 14:00 UTC + intraday every 3h (no email). Deduplicates by company+role+url, saves to `digest_jobs`.
- **Two job sources**: Adzuna + JSearch (RapidAPI) run in parallel across up to 3 roles
- **Real-time notifications**: `notifier.py` fires per-job — ntfy push + Resend email. 24h freshness gate. Dedup via `job_notifications` table.
- **Digest page** (`/dashboard/digest`): numbered jobs, source badge, Tailor/Apply/Clear/Run buttons
- **Resume tailoring**: broken — Anthropic API credits depleted (top up at console.anthropic.com/billing)
- **Easy Apply**: Playwright for Greenhouse + Lever (JSearch jobs only — direct ATS URLs)
- **validate.py**: pre-apply quality gate + `/validate` endpoint
- **drafter.py**: Claude-powered outreach drafter + `/draft` endpoint (not yet tested end-to-end)
- **RunDigestButton**: polls `/api/pipeline-status` every 3s, guards against stale "complete" with `hasSeenRunning` ref, hard-navigates to `/dashboard/digest` on complete

## Infrastructure

- **Railway**: `https://anelo-production.up.railway.app` — FastAPI uvicorn, port 8000
- **Vercel**: `anelo.io`
- **Supabase**: `nyfpzapdafivahkuktww.supabase.co`
- **Railway env vars**: `ANTHROPIC_API_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ADZUNA_APP_ID`, `ADZUNA_API_KEY`, `RESEND_API_KEY`, `RAPIDAPI_KEY`, `NTFY_TOPIC` ✓
- **Vercel env vars**: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` ✓ — `SUPABASE_SERVICE_ROLE_KEY` likely MISSING (this is the bug)

## Supabase schema

- `preferences`: `role`, `role_2`, `role_3`, `experience_min`, `experience_max`, `location`, `min_salary`, `company_types`, `skills`, `user_id` (text = Clerk ID)
- `digest_jobs`: job matches per user — `user_id` (text), `company`, `role`, `job_url`, `location`, `salary_range`, `source`, `description`, `applied`, `matched_at`
- `job_notifications`: per-job notification log — `user_id` (text), `job_url`, `job_title`, `company`, `notified_at`. Unique on `(user_id, job_url)`.
- `tailored-resumes` bucket: `{userId}/{filename}.pdf`
- All tables RLS-enabled — all server access via service role key

## Remaining work (priority order)

1. **Fix Vercel env var** — add `SUPABASE_SERVICE_ROLE_KEY` to Vercel → UI should show jobs immediately
2. **Top up Anthropic credits** — resume tailoring dead until then (console.anthropic.com/billing)
3. **Test Easy Apply end-to-end** — find JSearch Greenhouse/Lever job, hit Apply, verify `applied=true` in DB
4. **Test drafter.py** — hit `/draft` endpoint, verify LinkedIn message quality
5. **UI revamp** — user planned this

## Key files

| File | Purpose |
|------|---------|
| `pipeline/api.py` | FastAPI — `/tailor`, `/validate`, `/draft`, `/apply`, `/run`, `/status`, `/health` |
| `pipeline/main.py` | Pipeline orchestrator — fetch → score → notify → tailor → save → digest email |
| `pipeline/jobs.py` | Adzuna + JSearch fetch, 3-role parallel, `posted_at` field |
| `pipeline/notifier.py` | Real-time ntfy push + Resend email, 24h freshness gate, dedup via DB |
| `pipeline/scorer.py` | Score + filter, experience range |
| `pipeline/tailor.py` | Resume + cover letter generation (broken — Anthropic credits) |
| `pipeline/apply.py` | Playwright Easy Apply (Greenhouse + Lever) |
| `pipeline/validate.py` | Pre-apply quality gate |
| `pipeline/drafter.py` | Outreach message drafter |
| `web/lib/supabase.ts` | `supabaseAdmin()` — uses `SUPABASE_SERVICE_ROLE_KEY` (must be in Vercel env) |
| `web/app/dashboard/digest/page.tsx` | Digest page — queries `digest_jobs` via `supabaseAdmin()` |
| `web/app/dashboard/digest/RunDigestButton.tsx` | Run + live status polling, hard-nav on complete |
| `web/app/api/run-digest/route.ts` | Proxies POST to Railway `/run` |
| `web/app/api/pipeline-status/route.ts` | Proxies GET to Railway `/status` |
| `web/app/api/clear-digest/route.ts` | Deletes digest_jobs for user |
