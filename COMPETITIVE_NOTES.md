# HireIQ — Competitive Notes (AI‑ATS / recruiting tech)

Research to inform the Phase 5 landing-page and dashboard overhaul. Focus: how established players present themselves to buyers, and what "premium but trustworthy" looks like for a B2B HR audience (who are not gamers — animation should read as confident and fast, not flashy).

Sources are the vendors' public marketing sites and product tours as of the knowledge cutoff; treat specific claims as directional, not quoted. Verify any competitor pricing/wording before echoing it in copy.

---

## Competitors surveyed

### 1. Ashby (ashbyhq.com) — the closest aesthetic reference
- **Leads with:** "All‑in‑one recruiting" + analytics as the wedge. Hero is a crisp product screenshot (real dashboard, not an abstract illustration) on a light, high-contrast background.
- **Density:** Very data-dense dashboards shown proudly — pipeline funnels, conversion analytics. They sell *sophistication*, so they show it.
- **Motion:** Minimal. Subtle fade/slide on scroll, no gratuitous 3D. Trust comes from showing the real product.
- **Takeaway for HireIQ:** A real, legible dashboard screenshot in the hero converts better for this audience than pure abstract particles. HireIQ's current hero is mostly constellation + a small mock card — lead with a bigger, believable product view.

### 2. Greenhouse (greenhouse.io) — enterprise trust
- **Leads with:** Outcomes and social proof — "hire for what's next," logos of known companies, analyst mentions, structured-hiring/DEI messaging.
- **Pricing:** Not public ("request a demo") — classic enterprise motion.
- **Motion:** Conservative, corporate. Lots of whitespace, photography of people.
- **Takeaway:** Social proof (logos, testimonials, quantified outcomes) is doing the heavy lifting. HireIQ has testimonials but they're clearly fictional placeholders — either get real ones or soften the specificity so they don't read as fabricated.

### 3. Lever (lever.co) — CRM + ATS
- **Leads with:** Relationship/nurture angle, "complete talent acquisition suite." Warm, approachable brand.
- **Density:** Moderate; emphasizes candidate relationship timelines.
- **Takeaway:** Clear feature naming beats clever naming. HireIQ's "Greedy Scheduling" is accurate-but-jargony for a recruiter; consider "Conflict-free interview scheduling."

### 4. Workable (workable.com) — SMB volume, AI-forward
- **Leads with:** Speed and breadth — "find, hire, onboard." Prominent AI sourcing/screening claims, free-trial CTA up top (product-led).
- **Pricing:** Public, transparent tiers with a clear "most popular" — exactly the pattern HireIQ should use.
- **Takeaway:** For a self-serve/paid launch, HireIQ is closer to Workable than Greenhouse. Public pricing + free trial + a highlighted middle tier is the right conversion pattern. HireIQ already highlights "Recruiter Pro" — keep that, make the value gap obvious.

### 5. Manatal / Teamtailor — design-forward, mid-market
- **Manatal:** Affordable, AI-scoring-forward; clean cards, candidate scoring shown as a headline feature (directly comparable to HireIQ's match score).
- **Teamtailor:** The most *design-led* of the set — employer-branding focus, tasteful motion, strong typography. Closest to the "make people want to come back" brief.
- **Takeaway:** HireIQ's dark glassmorphism is a genuine differentiator in a category that's mostly light/corporate — lean into it as brand, but keep contrast/legibility high (see accessibility note).

---

## Patterns that recur across winners
1. **Real product > abstract art in the hero.** Every serious ATS shows an actual dashboard. Particles/gradients are accents, not the main visual.
2. **Public, tiered pricing with one highlighted plan** for self-serve products; "request demo" only for enterprise.
3. **Quantified social proof** ("cut time-to-hire 40%," named logos). Fabricated-looking testimonials erode trust fast in B2B.
4. **Analytics shown as the premium wedge** — funnels, conversion, scoring. This is HireIQ's actual strength (match scores, bias audit, GitHub signals); surface it more.
5. **Restrained motion.** Fast, subtle, purposeful. Scroll-reveals and hover elevation, yes; spinning 3D that delays first paint, no.

---

## What this means for HireIQ's Phase 5
- **Hero:** Keep the constellation as *background texture*, but promote a larger, believable dashboard/kanban preview as the focal product visual. A React Three Fiber "skills → matches" graph can work **as an accent** if lazy-loaded with a static fallback and it doesn't block LCP — but a polished product screenshot is the safer conversion bet. Recommend: static/CSS-driven hero first (protects the Lighthouse 90+ target, now achievable since the JS bundle dropped 1.83MB→384KB), add optional WebGL flourish behind `prefers-reduced-motion` and a device check.
- **Pricing:** Resolve the two conflicting pricing definitions (dead `PricingSection.jsx` vs live `Landing.jsx`) before polishing — see AUDIT_LOG P2-8. Make the Pro value gap unmistakable.
- **Social proof:** Replace fabricated-looking testimonials with real ones or clearly-labeled illustrative examples; add logo/stat proof if any real usage exists.
- **Motion budget:** Match the category — confident and fast. Every animation needs a `prefers-reduced-motion` fallback (the codebase already threads `usePrefersReducedMotion` through Landing.jsx, which is the right foundation).
- **Differentiator to amplify:** The dark, analytics-heavy aesthetic + bias/blind-review + GitHub signals is genuinely distinct in this category. That's the brand — elevate it, don't neutralize it.
