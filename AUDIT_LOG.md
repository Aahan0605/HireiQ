# HireIQ — Pre-Launch Audit Log

Severity key: **P0** = breaks the app or leaks data · **P1** = broken feature / monetization gap · **P2** = UX/quality/security-hardening · **P3** = nice-to-have.

Status of each item is one of: **FIXED** (change applied in this pass), **NEEDS OWNER ACTION** (requires dashboard/prod access or a product decision), **OBSERVED** (documented, not yet fixed).

This pass covered **Phase 1 (code/repo audit)** in depth and the security-relevant parts of **Phases 2–3**. Phases 4–5 (competitive research and the visual/3D overhaul) were intentionally not started — the original brief gates them behind Phases 1–3 being fixed and verified, and several Phase 2/3 items still need production access (see `LAUNCH_READINESS.md`).

Backend test suite: **44 passed**, stable across repeated runs (no flakiness observed locally with `TESTING=true`).

---

## P0 — Critical (data leak / security)

### P0-1 · Rate-limit bypass shipped with a hardcoded default key — FIXED
- **File:** `backend/api/core/limiter.py`
- **Root cause:** Both key functions used `os.getenv("BYPASS_RATE_LIMIT_KEY", "super-secret-bypass-key-12345")`. If `BYPASS_RATE_LIMIT_KEY` was ever unset in production, **any external client** could send `X-Bypass-Rate-Limit: super-secret-bypass-key-12345` (a value published in the public repo) to bypass **all** rate limiting — including brute-force protection on `/auth/login`.
- **Fix:** Removed the default. Introduced `_bypass_requested()`; the bypass is honored **only** when `BYPASS_RATE_LIMIT_KEY` is explicitly set to a non-blank value AND the header matches. With the env var unset (the production default), no header can bypass limiting.
- **Owner follow-up:** Ensure `BYPASS_RATE_LIMIT_KEY` is either unset in production, or set to a long random secret used only by internal load tests.

### P0-2 · Valid field-encryption key published in the public repo — FIXED (code) / NEEDS OWNER ACTION (rotation)
- **Files:** `README.md`, `.github/workflows/ci.yml`, `.github/workflows/test.yml`, `backend/tests/conftest.py`
- **Root cause:** A real, valid base64 Fernet key (`L9V8Sba4Nr33J_…`) was documented in the README and used as a hardcoded CI fallback. Candidate resume text is encrypted at rest with `FIELD_ENCRYPTION_KEY`. If production ever used the documented key, **anyone reading the public repo can decrypt all stored candidate PII.**
- **Fix:** README now shows a placeholder plus a `Fernet.generate_key()` command. CI and test config swapped to a fresh, throwaway CI-only key (acceptable to be public since it only encrypts ephemeral test data).
- **Owner follow-up (must do before launch):** If production has **ever** run with the old README key, treat it as compromised: generate a new key, re-encrypt existing rows, and store the key only in Render's secret manager. Never reuse a repo-visible key.

### P0-3 · Email verification token returned in the API response — FIXED
- **File:** `backend/api/routes/auth.py` (`register`)
- **Root cause:** `/auth/register` returned `verification_token` in its JSON body unconditionally. The frontend (`SignIn.jsx`) uses it to render a "dev verify" link. In production this hands the verification token straight to the caller, so **email verification can be bypassed by reading the registration response** — no inbox access needed.
- **Fix:** The token is now included **only** when `ENVIRONMENT=development`. Production responses omit it; the frontend already guards with `if (res && res.verification_token)`, so the dev link simply doesn't render in prod.

---

## P1 — Broken feature / monetization gap

### P1-1 · Usage quotas were effectively disabled (no server-side monetization enforcement) — FIXED (defaults) / NEEDS OWNER CONFIRMATION (numbers)
- **File:** `backend/api/core/limits.py`
- **Root cause:** `PLAN_QUOTAS` set `parses/jobs/seats = 999999` for **every** tier including `free`. The enforcement plumbing (`check_cv_upload_limit`, `check_job_creation_limit`, `check_seat_limit`) worked correctly but had nothing to enforce — a free account had identical unlimited usage to a paid one. For a paid launch this means **there is no product reason to upgrade**, and the "enforce quotas server-side" requirement was unmet.
- **Fix:** Set real quotas aligned to the pricing **actually rendered** on the landing page (`Landing.jsx` `pricingPlans`): `free` (Free Trial, "5 resume parses / month"): 5 parses / 2 jobs / 1 seat; `pro` (Recruiter Pro $79, "Unlimited CV uploads"): unlimited; `enterprise`: unlimited. Kept `business` (unlimited) for billing-webhook compatibility.
- **Two conflicting pricing definitions (needs owner decision):** `PricingSection.jsx` advertises `Starter $49 / Pro $149`, but that component is **dead code** (imported nowhere). The landing page inlines a *different* set — `Free Trial $0 / Recruiter Pro $79 / Enterprise`. Quotas are aligned to the live one; delete or reconcile the dead `PricingSection.jsx` so the two don't drift further (see P2-8).
- **Owner follow-up:** `cv_upload_count` is a **lifetime** counter — the "5 resume parses / **month**" copy implies a monthly reset that is **not yet implemented**. Add billing-period reset before advertising monthly quotas.

### P1-2 · Bulk upload had no per-file or total size limit — FIXED
- **File:** `backend/api/routes/candidates.py` (`upload_bulk`)
- **Root cause:** The single-upload endpoint enforced a 10 MB cap, but `upload-bulk` (documented as accepting **1000 files**) had **no size validation at all** and read every file fully into memory as base64. 1000 unbounded files in one request is a straightforward memory-exhaustion / DoS vector.
- **Fix:** Added shared constants (`MAX_RESUME_FILE_SIZE` 10 MB, `MAX_BULK_FILES` 100, `MAX_BULK_TOTAL_BYTES` 200 MB). Each file is now size-checked before any DB write; oversized/empty files are rejected per-file with a clear reason; the batch aborts once the aggregate cap is hit. Batch cap lowered from 1000 → 100 to bound per-request latency/memory.
- **Owner follow-up:** For true large-batch ingest, move parsing to a real queue (Celery/Redis is referenced in docs but not wired into the upload path) rather than FastAPI `BackgroundTasks`.

### P1-3 · Oversized single upload left an orphaned candidate record — FIXED
- **File:** `backend/api/routes/candidates.py` (`upload_resume`)
- **Root cause:** The placeholder candidate row was saved to the DB **before** the file size was validated, so an oversized upload created an "Analyzing" candidate that then 413'd — leaving a stuck orphan row and a confusing UI state.
- **Fix:** Reordered so the file is read and size/empty-validated **before** the placeholder is created. Added an explicit empty-file (0 bytes) rejection.

---

## P2 — Security hardening / quality

### P2-1 · CORS allowed any `*.vercel.app` origin with credentials — FIXED
- **File:** `backend/api/main.py` (`VercelCORSMiddleware`)
- **Root cause:** To support preview deploys, the middleware allowed **any** `https://*.vercel.app` origin while `allow_credentials=True`. An attacker can deploy a malicious site to their own `*.vercel.app` subdomain and make credentialed cross-origin requests against the API.
- **Fix:** The wildcard is now **off by default** and only enabled when `ALLOW_VERCEL_PREVIEWS=true` (intended for staging, never production). An optional `VERCEL_PREVIEW_PREFIX` further constrains which preview subdomains are permitted. Production should keep it disabled and list the exact frontend origin(s) in `ALLOWED_ORIGINS`.

### P2-2 · No rate limiting on `/register`, `/forgot-password`, `/reset-password` — FIXED
- **File:** `backend/api/routes/auth.py`
- **Root cause:** Only `/login` was rate-limited. `/register` was open to signup spam / email bombing; `/forgot-password` to email bombing; `/reset-password` to token brute-forcing.
- **Fix:** Added `@limiter.limit` — `register` 5/hour, `forgot-password` 5/hour, `reset-password` 10/hour (added the required `request: Request` param to each). Limiter stays disabled under tests, so the suite is unaffected.

### P2-3 · Seeded demo credentials published in docs / hardcoded in seed script — FIXED
- **Files:** `README.md`, `walkthrough.md`, `backend/scripts/seed_demo.py`
- **Root cause:** README published `demo@hireiq.dev` / `Demo1234!`; `seed_demo.py` hardcoded that password; `walkthrough.md` contained the owner's real email and a real candidate's name/GitHub/LinkedIn (PII).
- **Fix:** `seed_demo.py` now refuses to run outside `ENVIRONMENT=development` and generates a random password printed once to the console. README references the console output instead of a fixed password. All PII scrubbed from `walkthrough.md`.
- **Owner follow-up:** Confirm no `demo@hireiq.dev` (with the old password) or `aahan060505@gmail.com` demo account exists in the **production** database; delete/disable if present.

### P2-4 · Duplicated startup block and duplicate imports in `main.py` — FIXED
- **File:** `backend/api/main.py`
- **Fix:** Removed the duplicated Resend-sandbox startup check and the duplicated `Response, status` import (`from fastapi import FastAPI, Request, Response, status, Response, status`).

### P2-5 · Two toast libraries installed and both in use — OBSERVED
- **Files:** `frontend/package.json`, `frontend/src/App.jsx` (both `sonner` and `react-hot-toast`), plus `sonner` used across `Dashboard/Analyze/Settings/CandidateProfile/Candidates`.
- **Impact:** Two toast systems can render competing/duplicate notifications and add bundle weight. Recommend standardizing on `sonner` (already the majority usage) and removing `react-hot-toast`.
- **Not fixed here:** touches shared UI wiring; fold into the Phase 5 frontend pass.

### P2-6 · Health endpoint leaks raw DB error string to unauthenticated clients — OBSERVED
- **File:** `backend/api/main.py` (`/health`)
- **Impact:** On DB failure, `/health` returns `"error": str(e)` unauthenticated, which can disclose internal connection details. Consider returning a generic message publicly and logging the detail server-side only.

### P2-8 · Dead landing-page components imported nowhere — FIXED (deleted)
- **Files:** `frontend/src/components/HeroSection.jsx`, `FeaturesSection.jsx`, `PricingSection.jsx`
- **Root cause:** The Phase-5 brief names these as the landing-page components to edit, but `Landing.jsx` is a ~650-line monolith that inlines its own hero/features/pricing. These three components (and their pricing numbers) were **not imported anywhere** — editing them would have zero visible effect and they silently drifted from the live copy (they disagreed on both price and quota).
- **Fix:** Deleted all three dead components (verified no dangling references; `MagneticCard`, which they imported, is retained since real pages use it). Added a source-of-truth comment to `Landing.jsx`'s `pricingPlans` tying it to backend `PLAN_QUOTAS`. `Landing.jsx` is now the single, unambiguous source of landing/pricing content.

### P2-9 · Landing PII: real person's name in the public hero mockup — FIXED
- **File:** `frontend/src/pages/Landing.jsx`
- **Root cause:** The hero "candidate card" mockup hard-coded a real individual's name ("Aahan Gajera") and an inferred profile/score, shown to every visitor of the public marketing page.
- **Fix:** Replaced with a clearly fictional demo candidate ("Jordan Rivera"). Verified in-browser that the live hero no longer contains the real name.

### P2-7 · Real Supabase project ref hardcoded in CI workflows — OBSERVED
- **Files:** `.github/workflows/ci.yml`, `test.yml` (`SUPABASE_URL: "https://ndkjiycehjdkcqupphuu.supabase.co"`)
- **Impact:** Minor info disclosure (the project ref, not a secret key). Prefer sourcing from `${{ secrets.* }}` with a dummy fallback, consistent with the other vars.

### P2-10 · Failed CI runs write pytest logs into the Supabase candidates table — OBSERVED
- **File:** `backend/scripts/ci_test_runner.py` (`upload_log`)
- **Root cause:** On any test failure the runner inserts a candidate row (`full_name: "CI Run Log"`, the full pytest output in `raw_text`/`insights.log`) linked to the first real recruiter it finds. Since CI's `SUPABASE_URL` is a real project ref, if a real `SUPABASE_KEY` is configured in Actions secrets, **every failed CI run pollutes the production candidates table** with fake records containing internal stack traces — and attaches them to a real recruiter's tenant.
- **Recommendation:** Point CI at a dedicated test/staging Supabase project, or drop the DB upload entirely (the `GITHUB_STEP_SUMMARY` write already surfaces logs on the Actions page). Confirm the exit code is still propagated (it is — `sys.exit(exit_code)`).

### P2-11 · Frontend served without security headers at the Vercel edge — FIXED
- **File:** `frontend/vercel.json`
- **Root cause:** The backend set `X-Frame-Options`/HSTS/etc. on API responses, but the static frontend HTML (marketing + app shell) served by Vercel had no such headers — leaving the app clickjackable and without edge HSTS.
- **Fix:** Added a `headers` block to `vercel.json` applying `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Strict-Transport-Security`, and a restrictive `Permissions-Policy` to all routes.

### P3-3 · Production runs on Render free tier with ENVIRONMENT=staging — OBSERVED
- **File:** `render.yaml`
- **Impact:** `plan: free` means the backend cold-starts after 15 min idle (30–60s first-request hang) — a real churn risk for paying users, currently papered over by the `keep_alive.yml` cron. For a paid launch, upgrade to a paid Render instance (removes cold starts and the keep-alive hack). Also `ENVIRONMENT: staging` on what may be the production service is a smell — set it to `production` so prod-only guards behave as intended. (Blueprint secrets are correctly `sync: false`, i.e. not committed — good.)

---

## P3 — Nice-to-have

### P3-1 · `datetime.utcnow()` deprecation throughout — OBSERVED
- Widespread `datetime.utcnow()` usage (auth, candidates, main, conftest) raises `DeprecationWarning` and is scheduled for removal. Migrate to timezone-aware `datetime.now(timezone.utc)`. Non-blocking but noisy (128+ warnings per test run).

### P3-2 · `BackgroundTasks` for resume processing won't survive restarts — OBSERVED
- Resume parsing runs in FastAPI `BackgroundTasks`. If the worker restarts mid-parse (common on Render free tier cold-cycles), the candidate is stuck in `Analyzing`. The referenced Celery/Redis path is the correct home for this. Consider a reconciliation job that re-queues candidates stuck in `Analyzing` beyond N minutes.

---

## Verified good (no change needed)
- **Stripe billing is real, not mocked:** `backend/api/routes/billing.py` implements a signature-verified webhook (`stripe.Webhook.construct_event`) with idempotency via a `stripe_webhook_events` table, and `create-checkout-session` uses hosted Stripe Checkout (no raw card handling — PCI-appropriate). Price IDs still default to `price_1Mock…` placeholders → set real ones in prod env.
- **Anti-enumeration:** `/forgot-password` always returns 200.
- **Login lockout:** 5 failed attempts → 15-minute lock, with graceful fallback if the columns are missing.
- **JWT startup validation:** requires `JWT_SECRET_KEY` ≥ 32 chars and fails fast if core env vars are missing.
- **CORS `*` guard:** startup raises if `*` is combined with `allow_credentials=True`.
- **Sentry PII scrubbing:** strips auth headers, cookies, and password/token/resume fields in `before_send`.
- **`scratch/` dirs are gitignored and not tracked**, and are not imported by production code — they won't ship.
- **Tracked `.env.*.example` files contain only placeholders** (`sk_test_...`, `re_YourResendAPIKeyHere`, etc.), no real secrets.
