# Anelo — Handoff Document
**Date:** March 31, 2026
**Repo:** github.com/david-007t/anello
**Domain:** anelo.io (Porkbun DNS → Vercel)
**Next session prompt:** "Read HANDOFF.md and continue from there."

---

## What Anelo Is
AI job hunting SaaS. Users upload a master resume, set job preferences, and Anelo finds jobs, tailors the resume per job, and auto-applies — every day on autopilot.

---

## Repo Structure
```
jobauto/               ← GitHub repo (david-007t/anello)
├── web/               ← Next.js 16 frontend (Vercel)
├── pipeline/          ← Multi-user Python pipeline (Railway)
├── personal/          ← Original single-user pipeline (NOT deployed, reference only)
├── requirements.txt   ← Root-level (required for Railway/Nixpacks Python detection)
├── railway.toml       ← Railway config
└── vercel.json        ← Vercel config (framework: nextjs)
```

Personal pipeline also preserved at: `/Users/ohsay22/Developer/personal-jobauto/`

---

## Infrastructure

| Service | Status | Notes |
|---------|--------|-------|
| **Vercel** | ✅ Live | Project ID: `prj_TyC2KTwyvu1qOc2QhdFRqtcJL3Zw`, team: `david-007ts-projects`. Root dir: `web`. **GitHub auto-deploy is BROKEN** — must deploy via CLI. |
| **Railway** | ⚠️ Needs redeploy | Redeploy manually after latest push (added root requirements.txt). Cron: `0 14 * * *` (7am PDT). |
| **Supabase** | ✅ Connected | Schema run. Storage bucket `resumes` created (private). |
| **Clerk** | ✅ Auth working | Webhook NOT yet configured (critical — see below). |
| **Resend** | ✅ Working | Waitlist capture working. |
| **Adzuna** | ✅ Keys set | `ADZUNA_APP_ID` + `ADZUNA_API_KEY` in Railway shared vars. |

---

## Environment Variables

### Vercel (all set)
```
RESEND_API_KEY
WAITLIST_NOTIFY_EMAIL
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
```

### Railway Shared Vars (all set)
```
ANTHROPIC_API_KEY
NEXT_PUBLIC_SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
PIPELINE_HOUR=14
ADZUNA_APP_ID
ADZUNA_API_KEY
```

---

## What's Built

### Frontend (`web/`)
- Landing page — hero, how it works, features, pricing, waitlist form
- Auth — Clerk sign-in / sign-up pages
- Dashboard layout — sidebar nav (Overview, Digest, Applications, Resume, Preferences)
- Dashboard overview — stat cards (hardcoded "—", needs real Supabase data)
- Resume page — drag & drop upload → `/api/resume/upload` → Supabase Storage
- Preferences page — form saves to Supabase via `/api/preferences`
- Digest page — empty state stub (needs real data wired)
- Applications page — empty state stub (needs real data wired)

### API Routes
- `POST /api/waitlist` — email capture → Resend
- `GET|POST /api/preferences` — read/write user prefs to Supabase
- `GET /api/resume` — get current resume filename
- `POST /api/resume/upload` — upload file → Supabase Storage `resumes` bucket
- `POST /api/webhooks/clerk` — syncs Clerk user events → Supabase `users` table

### Pipeline (`pipeline/`)
- `jobs.py` — fetches jobs from Adzuna API per user preferences
- `scorer.py` — scores/ranks jobs against user skills
- `tailor.py` — tailors resume per job via Anthropic Haiku
- `digest.py` — sends daily digest email via Resend
- `main.py` — orchestrates full pipeline for all users from Supabase

### Supabase Schema (`web/supabase/schema.sql`)
Tables: `users`, `preferences`, `resumes`, `jobs`, `applications`

---

## What's NOT Done (priority order)

### 1. Clerk Webhook → CRITICAL
Without this, signups don't save to Supabase so pipeline can't email anyone.

**Steps (owner does this):**
1. Clerk dashboard → Webhooks → Add Endpoint
2. URL: `https://anelo.io/api/webhooks/clerk`
3. Events: `user.created`, `user.updated`, `user.deleted`
4. Copy the **Signing Secret** → add to Vercel env vars as `CLERK_WEBHOOK_SECRET`

**Then (Claude does this):** Add svix signature verification to `/api/webhooks/clerk/route.ts`

### 2. Railway Redeploy
Just hit Redeploy in Railway dashboard. Picks up latest commit with root `requirements.txt`.

### 3. Wire Digest + Applications to Real Data
Both pages show empty stubs. Need to query Supabase `jobs` and `applications` tables per logged-in user.

### 4. Dashboard Stats
Overview page shows "—" for all counts. Wire to Supabase for real application/job counts.

### 5. Fix Vercel Auto-Deploy
GitHub webhook is broken — new pushes don't trigger Vercel deploys.
Fix: Vercel project settings → Git → disconnect + reconnect GitHub repo.

---

## How to Deploy Correctly

### RULE: Always build locally before pushing
```bash
cd web
PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH" npm run build
# Must show "Compiled successfully" before pushing
```

### Deploy to Vercel (until webhook is fixed)
```bash
# From web/ directory — .vercel/project.json points to correct project
cd web
PATH="$HOME/.nvm/versions/node/v18.13.0/bin:$PATH" vercel --prod --yes
```

### Deploy to Railway
Push to GitHub main → Railway auto-deploys (or hit Redeploy manually).

---

## Known Gotchas
1. **Vercel "Redeploy" button** pulls the last attempted commit, not latest. Don't use it — always deploy via CLI.
2. **Active production deployment**: `dpl_DQEd4ygEhPLEF6Tc2UAcv9nTYcw4` (commit `5895936`). Don't touch it.
3. **Clerk `UserButton`**: `afterSignOutUrl` goes on `<ClerkProvider>`, not `<UserButton>`. Caused multiple failed builds.
4. **Railway Nixpacks**: needs `requirements.txt` at repo root, not just in `pipeline/`.
5. **Node version**: use v20 for building (`~/.nvm/versions/node/v20.20.2/bin`), v18 for Vercel CLI.
6. **Domain**: anelo.io (one L). GitHub repo is `anello` (two L's). Cosmetic inconsistency, not urgent.
