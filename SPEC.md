# Technical Specification: YumNom — Walmart Meal Planner App

**Version:** 1.1
**Date:** July 17, 2026
**App Name:** YumNom

## 1. Overview

- **Purpose:** Free mobile app that generates practical weekly meal plans for working parents using current Walmart availability and pricing data along with silent Grok (xAI) intelligence.
- **Core Principles:** Frictionless UX, 100% free for users, data minimization, graceful degradation.
- **Revenue model:** Primary — Walmart+ referral bounties via a first-class, measured funnel (§5, §9). Secondary — grocery affiliate commissions (~1% and sometimes excluded; treated as upside, not the business case).

## 2. Tech Stack

- **Mobile App:** Flutter (cross-platform iOS/Android).
- **Backend:** Python + FastAPI.
- **Database:** SQLite (local-only for v1; cross-device sync explicitly deferred).
- **Walmart Integration:** Walmart Affiliate Marketing API (walmart.io Content Provider API).
- **AI Engine:** xAI Grok API (silent backend only; structured outputs / JSON schema).
- **Hosting:** Render (single choice; supports long-lived streaming responses).

## 3. System Architecture

- **Frontend:** Flutter app (UI + local storage).
- **Backend:** FastAPI service for orchestration.
- **Shared Product Cache (architectural component, not an optimization):** server-side cache keyed by `(store-or-zip, canonical ingredient)` that sits between all users and the Walmart API. All product lookups go through it. Rationale: the affiliate API's default limit is 5,000 calls/day — at ~20 uncached lookups per plan, that is only ~250 uncached plans/day. The cache turns per-user lookups into per-region lookups. A rate-limit raise is requested from Walmart in parallel (see `spikes/1-walmart-affiliate-application.md`).
- **Data Flow:** User profile (local) → Generate Plan (authenticated, §13) → cached Walmart availability → Grok prompt → SKU matching (§6) → streamed formatted response → UI.

## 4. Location & Store Selection

- **Baseline (v1):** ZIP-level walmart.com availability and pricing. This requires no special API approval and is the mode the app must fully work in.
- **Enhancement (pending approval):** store-level (`storeId`) stock lookups require additional approval from Walmart's business team. Apply immediately (longest lead time); wire in as a progressive enhancement when granted.
- On first use/profile setup: request location permission with clear explanation ("To find your nearest Walmart for accurate stock").
- Default behavior: device GPS (lat/lon) → Walmart `/stores` endpoint to find nearest stores.
- Always display active store clearly on home screen with easy "Change Store / Enter ZIP" option.
- Store chosen location locally.
- Graceful fallback: permission denied or inaccurate GPS → manual ZIP entry.

## 5. Key Features & Implementation

- Quick profile setup.
- One-tap plan generation using current Walmart data (streamed progressively, §21).
- Grok-generated smart plans with substitutions.
- Shopping list + one-tap cart/delivery links.
- **Walmart+ referral funnel (first-class feature):** contextual pitch surfaces (e.g., "free delivery on this $142 cart"), an in-app savings explainer, and a tracked referral link. Instrumented end-to-end (§9) — this is the primary revenue driver, not an afterthought.

## 6. Ingredient → SKU Matching (new in v1.1)

The hardest problem in the app: mapping recipe ingredients ("2 cups flour") to specific, purchasable Walmart products with sensible package sizes — 30–60 ingredients per weekly plan, under a constrained API budget.

- **Pipeline:** canonical-ingredient normalization → shared product cache lookup (§3) → on miss, Walmart search API → candidate ranking (price-per-unit, package size vs. needed quantity, brand tier) → Grok disambiguation only for ambiguous cases.
- **Canonical ingredient table:** curated mapping of common ingredient names → search terms + preferred SKU candidates, cached per store/zip with TTL.
- **Quality metric (release gate):** ≥90% of plan ingredients matched to purchasable SKUs; unmatched items degrade gracefully to a plain-text shopping-list line, never a broken cart link.
- Validated by `spikes/3-sku-matching/` before app code is written.

## 7. Error Handling & Graceful Degradation

- Walmart unavailable → use cached data or general suggestions.
- Grok failure → rule-based fallback templates.
- Offline → load last saved plan.
- User-friendly messages.

## 8. Caching & Rate-Limit Strategy

- **Hard architectural requirement**, not an optimization (see §3 budget math).
- Cache Walmart results per zip/store (TTL 30–60 min for prices/availability; longer for product metadata).
- Grok response caching for identical inputs.
- Exponential backoff on rate limits.
- Request an affiliate API rate-limit raise from Walmart early, with business justification.

## 9. Analytics / Instrumentation (Privacy-First)

- Aggregated metrics: plans generated, cart-link taps, cart conversion, SKU match rate, **budget adherence** (plan total vs. user's stated weekly budget — replaces the undefined "reported savings" metric from v1.0).
- **Walmart+ funnel metrics:** pitch impressions → taps → referral completions.
- No personal tracking or PII.

## 10. Prompt Engineering & Evaluation

- Versioned prompts stored in code.
- JSON schema (structured outputs) for consistent output.
- **Golden-set LLM evals, run on every prompt-version change:** fixed set of profiles → generated plans, scored on JSON validity, constraint adherence (budget, allergies, servings), and SKU match rate.
- Automated test cases + manual review.

## 11. Cost Monitoring & Budget Guardrails for Grok

- Log token usage per request.
- Per-device daily limits (enforced via §13) + alerts.
- Hard daily spend cap.

## 12. Security / Data Minimization

- Local-first: most data stays on device.
- Only anonymized data (budget, prefs, zip) sent to APIs.
- No PII in Grok prompts.
- **Allergy safety is deterministic, not prompt-based:** allergens are enforced by a code-level ingredient blocklist check on Grok's output (regenerate or substitute on violation), plus a visible disclaimer. The LLM prompt also states the allergy, but the guarantee lives in code.
- **Prompt-injection hygiene:** profile preferences are enumerations where possible; any free-text field is length-capped and sanitized before inclusion in prompts (low stakes, cheap to handle).

## 13. Device-Bound Anonymous Auth (new in v1.1)

Anonymous ≠ unauthenticated. All backend endpoints require a device-bound anonymous key:

- On first launch, the app requests a key from `POST /register-device`; the backend issues an opaque token bound to that install.
- All subsequent calls send the token; per-device rate limits and Grok spend caps (§11) key off it.
- Platform attestation (Play Integrity / Apple DeviceCheck or App Check) gates key issuance to real devices, blocking scripted abuse of the free LLM-backed endpoint.
- No accounts, no PII — the token identifies an install, not a person.

## 14. Cart / Deep Link Flow

- Use affiliate deep links (`affil.walmart.com` add-to-cart / buynow) to pre-populate the Walmart cart.
- Success: redirect to Walmart app/site.
- Failure (user not logged in, link rejected): helpful message + copyable list fallback.
- **Prices shown in-app are labeled "estimated"** — affiliate API prices are walmart.com prices and may differ from local store prices, especially before storeId approval.
- Multi-item grocery link behavior and in-app attribution validated by `spikes/2-cart-deeplink-test.md` before this flow is built.

## 15. Flutter Specifics

- **State Management:** Riverpod.
- **Permissions:** permission_handler package.
- **Deep Linking:** app_links package.

## 16. Backend Endpoints (Key Examples)

- `POST /register-device` — issues device-bound anonymous key (§13).
- `POST /generate-plan` — authenticated; streams the plan progressively.
- `POST /update-profile` — authenticated.
- `GET /stores?lat=...&lon=...` — authenticated.

## 17. Walmart API Edge Cases

- Rate limits: handled with shared cache (§3) + backoff.
- Excluded categories: skip gracefully.
- Unavailable items: Grok suggests available alternatives.

## 18. Testing Strategy

- Unit, integration (mocked APIs), end-to-end tests.
- Golden-set LLM evals (§10) as a release gate for prompt changes.
- SKU match-rate regression tests against recorded Walmart API fixtures.

## 19. Deployment & Observability

- Backend on Render.
- Basic logging and usage dashboard (token spend, API budget consumption, funnel metrics).

## 20. App Store & Program Compliance (new in v1.1)

- Location-permission purpose strings (iOS `NSLocationWhenInUseUsageDescription`, Android rationale dialog).
- Apple privacy "nutrition label" + Google Play data-safety form; hosted privacy policy.
- Confirm meal-planner use case with Walmart affiliate ops (affilops@wal-mart.com) — API terms license use "solely for advertising Walmart.com products online."
- Affiliate trademark rules: "Walmart" must not appear in app name/branding (YumNom is safe); review marketing copy.
- Allergy/nutrition disclaimer surfaced in-app (§12).

## 21. Non-Functional Requirements

- **Performance:** *time-to-first-content* < 5 seconds — the plan streams progressively (day 1 visible in ~3–5 s over a skeleton UI; full 7-day plan completes in the background, typically 10–30 s). Full-plan latency is measured but not the headline target.
- **Pre-generation:** for returning users, next week's plan is generated overnight so the common case is instant.
- **Offline Support:** cached plans available.
- **Scalability:** designed to grow from a small restricted base to larger user numbers as revenue permits; scaling is gated on the Walmart API budget (§3, §8).

## 22. Changelog

**v1.0 → v1.1** (per approved spec review):
1. ZIP-level availability is the baseline; store-level stock is an approval-gated enhancement (§4).
2. New §6: Ingredient → SKU matching design + ≥90% match-rate release gate.
3. Walmart+ referral funnel promoted to primary revenue feature with funnel metrics (§1, §5, §9).
4. New §13: device-bound anonymous auth for all endpoints.
5. NFR changed from "<5 s plan generation" to streaming time-to-first-content + overnight pre-generation (§21).
6. Shared server-side product cache promoted to an architectural component with 5k/day budget math (§3, §8).
7. Hosting narrowed to Render; sync deferred — SQLite local-only for v1 (§2).
8. Deterministic allergy filtering + disclaimers (§12); "reported savings" replaced with defined budget-adherence metric (§9). Added compliance checklist (§20) and LLM evals (§10, §18).
