# HireIQ — Launch Readiness

Snapshot after the first hardening pass (Phase 1 code/repo audit + security-relevant Phase 2/3 items). See `AUDIT_LOG.md` for the itemized findings and fixes.

---

## ✅ Safe to charge real money for (with the owner follow-ups below done)
- **Authentication**: bcrypt hashing, JWT with startup-validated secret, login lockout after 5 failures, email-verification enforced, anti-enumeration on password reset. Now rate-limited on register / login / forgot / reset.
- **Billing**: real Stripe hosted Checkout + signature-verified, idempotent webhooks. No raw card data touches the app (PCI-appropriate).
- **Tenant isolation**: covered by `test_tenant_isolation.py` and enforced via `require_tenant`; 44/44 backend tests pass, stable across runs.
- **Uploads**: single + bulk resume uploads now have enforced size/type/empty/batch limits.

## ⚠️ Must be done before launch (owner action — needs prod/dashboard access I don't have)
1. **Rotate `FIELD_ENCRYPTION_KEY`** if production ever used the key that was published in the README (P0-2). Re-encrypt existing candidate rows and store the new key only in Render secrets.
2. **Confirm no public demo account** (`demo@hireiq.dev` / old password, or `aahan060505@gmail.com`) exists in the **production** DB; disable if present (P2-3).
3. **Set real Stripe price IDs** (`STRIPE_PRICE_PRO`, `STRIPE_PRICE_BUSINESS`) in prod env — they currently default to `price_1Mock…` placeholders.
4. **Confirm the new quota numbers** in `backend/api/core/limits.py` match `PricingSection.jsx`, and decide on **monthly quota reset** (currently `cv_upload_count` is a lifetime counter — quotas won't reset each billing period).
5. **Verify prod env vars** against `render.yaml` / `.env.production.example`: `BYPASS_RATE_LIMIT_KEY` unset-or-random, `ALLOW_VERCEL_PREVIEWS` unset/false in prod, `ALLOWED_ORIGINS` = the real frontend origin only, `FROM_EMAIL` not on the Resend sandbox domain.

## 🚧 Still mocked / unfinished — do NOT market as real yet
- **"Up to 1000 resumes at once"**: batch cap is now **100** with in-request processing via `BackgroundTasks`. True 1000-file async ingest needs the referenced Celery/Redis queue, which is not wired into the upload path. Market the current, honest limit.
- **Quota reset / billing-period accounting**: not implemented (see item 4).
- **LinkedIn import**: already a "coming soon" stub per git history — keep it labeled as such.

## ✅ Done in the Phase 2–5 pass
- **Frontend runtime verified locally**: dev server runs clean — no console errors, routing/ProtectedRoute/NotFound all correct, error boundary not tripped.
- **Landing PII removed** (real name in the public hero → fictional demo), verified in-browser (P2-9).
- **Performance**: routes code-split; initial JS bundle **1.83 MB → 384 KB** (recharts loads only on chart pages) — makes the Lighthouse-90 landing target realistic. Toast libraries consolidated to `sonner` (P2-5). framer-motion + React Router deprecation warnings cleared.
- **Edge security headers** added to `vercel.json` (P2-11).
- **Landing polish**: deleted the 3 dead landing components so `Landing.jsx` is the single source of truth. (An animated hero network graph was trialled then removed at the owner's request — didn't fit the aesthetic.) Instead: elevated the "Recruiter Pro" pricing card so it's clearly the recommended tier (raised, emerald glow, solid badge, hover-lift), added hover-lift micro-interactions to feature cards, and added `focus-visible` keyboard rings to pricing CTAs. All reduced-motion safe; verified in-browser with a clean console.
- **Competitive research** delivered in `COMPETITIVE_NOTES.md` (Phase 4) with a concrete Phase-5 direction.
- **CI integrity**: confirmed `ci_test_runner.py` propagates the pytest exit code (failures do fail CI — genuinely fixed, not quieted). Flagged that failed CI runs pollute the Supabase candidates table (P2-10).
- **Data-viz polish**: shared dark-theme `ChartTooltip` wired into the CandidateProfile and CompareView radars (which had none) and the two default-styled Dashboard bar charts; BiasReport donut arcs now draw in on load (reduced-motion safe).
- **Micro-interactions**: `CelebrationBurst` particle effect + celebratory toast when a candidate is moved to Hired (single and bulk); reduced-motion safe.
- **Landing consistency**: FAQ section now scroll-reveals like every other section; testimonials labelled "Illustrative examples" so the fictional quotes don't read as fabricated endorsements. Mobile (375px) verified — no horizontal overflow.

## 📋 Prioritized punch list (remaining, not yet done)
1. Resolve the **two conflicting pricing definitions** (dead `PricingSection.jsx` vs live `Landing.jsx`) — delete the dead one or wire it up (P2-8).
2. Implement **monthly quota reset** — "5 parses/month" copy vs. lifetime `cv_upload_count` (P1-1).
3. Point **CI at a test Supabase project** (or drop the DB log upload) so failures don't write to prod (P2-10).
4. Wire resume parsing to a durable queue + reconcile candidates stuck in `Analyzing` (P3-2).
5. `/health` should stop returning raw DB error strings to unauthenticated callers (P2-6).
6. Migrate `datetime.utcnow()` → timezone-aware (P3-1).
7. **Phase 2 dynamic flows** — still need a running backend + real data to exercise end-to-end: signup→verify→login→reset against a live email provider; corrupted/scanned/non-English resume failure paths; Kanban drag persistence across refresh; filters/GitHub sync/Blind Review/scheduler/CSV+PDF export correctness; mobile breakpoints; full a11y (keyboard nav, `--mint`-on-`--bg` contrast).
8. **Phase 5 remaining polish** — chart tooltips/entry animations, FAQ reveal, testimonials label, and the Hired celebration are all done. Left: source **real testimonials** (currently illustrative), and optionally a WebGL hero (the SVG network graph was trialled and removed at the owner's request; a lazy R3F version could slot into the hero if desired). Skeleton loaders already exist per prior commits; a final sweep to confirm every async page uses them is a nice-to-have.

## What this pass did NOT verify (be aware)
- Anything requiring the **live site, production database, or Vercel/Render dashboards** — no credentials in this environment. All "NEEDS OWNER ACTION" items fall here, plus: live console/network errors on hirei-q.vercel.app, env-var drift, live CI run status (gh not authed), keep-alive necessity, Docker-build-from-scratch, and prod header verification.
- Real **email deliverability** (Resend/SMTP) — code paths reviewed, not live sends.
- **Dynamic app flows** — the frontend was run, but authenticated flows (upload, kanban, exports) need a live backend + DB to exercise.
