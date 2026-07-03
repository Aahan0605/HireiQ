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

## 📋 Prioritized punch list (remaining, not yet done)
1. Wire resume parsing to a durable queue + add a reconciliation job for candidates stuck in `Analyzing` (P3-2).
2. Consolidate to a single toast library — remove `react-hot-toast`, keep `sonner` (P2-5).
3. Make `/health` stop returning raw DB error strings to unauthenticated callers (P2-6).
4. Migrate `datetime.utcnow()` → timezone-aware (P3-1).
5. **Phase 2 (product walk-through)** — not yet executed end-to-end: signup→verify→login→reset email flows against a real provider; single + corrupted/scanned/non-English resume failure paths; Kanban drag persistence across refresh; filters/GitHub sync/Blind Review/scheduler/exports correctness; mobile/responsive + accessibility (keyboard, contrast on `--mint`/`--bg`).
6. **Phase 3 (live deployment audit)** — needs Vercel/Render dashboard access: console/network errors on the live site, env-var drift, CI green-vs-skipping verification, keep-alive necessity, Docker builds from scratch, security headers/HSTS/CSP in prod, Sentry wired both ends.
7. **Phase 4 (competitive research)** and **Phase 5 (visual/3D overhaul)** — intentionally not started; gated behind 1–3 being fixed *and verified in production*.

## What this pass did NOT verify (be aware)
- Anything requiring the **live site, production database, or Vercel/Render dashboards** — I don't have those credentials in this environment. All "NEEDS OWNER ACTION" items above fall here.
- Real **email deliverability** (Resend/SMTP) — only the code paths were reviewed, not live sends.
- **Frontend runtime** — no dev server was run; frontend findings are from static review only.
