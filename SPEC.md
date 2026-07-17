# Technical Specification: YumNom — Walmart Meal Planner App

**Version:** 1.0 (Polished)
**Date:** July 17, 2026
**App Name:** YumNom

## 1. Overview

- **Purpose:** Free mobile app that generates practical weekly meal plans for working parents using current Walmart inventory and pricing data along with silent Grok (xAI) intelligence.
- **Core Principles:** Frictionless UX, 100% free for users, revenue via affiliate commissions, data minimization, graceful degradation.

## 2. Tech Stack

- **Mobile App:** Flutter (cross-platform iOS/Android).
- **Backend:** Python + FastAPI.
- **Database:** SQLite (local-first) + optional Supabase/Firebase for minimal sync.
- **Walmart Integration:** Walmart Affiliate Marketing API.
- **AI Engine:** xAI Grok API (silent backend only).
- **Hosting:** Render / Railway / Vercel.

## 3. System Architecture

- **Frontend:** Flutter app (UI + local storage).
- **Backend:** FastAPI service for orchestration.
- **Data Flow:** User profile (local) → Generate Plan → Walmart query → Grok prompt → formatted response → UI.

## 4. Location & Store Selection

- On first use/profile setup: Request location permission with clear explanation ("To find your nearest Walmart for accurate stock").
- Default behavior: Use device GPS (lat/lon) → call Walmart `/stores` endpoint to find nearest stores.
- Always display active store clearly on home screen with easy "Change Store / Enter ZIP" option.
- Store chosen location locally.
- Graceful fallback: Permission denied or inaccurate GPS → manual ZIP entry.

## 5. Key Features & Implementation

- Quick profile setup.
- One-tap plan generation using current Walmart data.
- Grok-generated smart plans with substitutions.
- Shopping list + one-tap cart/delivery links.
- Soft Walmart+ pitch after consistent use.

## 6. Error Handling & Graceful Degradation

- Walmart unavailable → Use cached data or general suggestions.
- Grok failure → Rule-based fallback templates.
- Offline → Load last saved plan.
- User-friendly messages.

## 7. Caching & Rate-Limit Strategy

- Cache Walmart results per zip (TTL 30-60 min).
- Grok response caching for identical inputs.
- Exponential backoff on rate limits.

## 8. Analytics / Instrumentation (Privacy-First)

- Aggregated metrics: plans generated, cart conversion, reported savings.
- No personal tracking or PII.

## 9. Prompt Engineering & Evaluation

- Versioned prompts stored in code.
- JSON-mode for consistent output.
- Automated test cases + manual review.

## 10. Cost Monitoring & Budget Guardrails for Grok

- Log token usage per request.
- Per-user daily limits + alerts.
- Hard daily spend cap.

## 11. Security / Data Minimization

- Local-first: Most data stays on device.
- Only anonymized data (budget, prefs, zip) sent to APIs.
- No PII in Grok prompts.

## 12. Cart / Deep Link Flow

- Use affiliate deep links to pre-populate Walmart cart.
- Success: Redirect to Walmart app/site.
- Failure (user not logged in): Helpful message + copyable list fallback.

## 13. Flutter Specifics

- **State Management:** Riverpod.
- **Permissions:** permission_handler package.
- **Deep Linking:** app_links package.

## 14. Backend Endpoints (Key Examples)

- `POST /generate-plan`
- `POST /update-profile`
- `GET /stores?lat=...&lon=...`

## 15. Walmart API Edge Cases

- Rate limits: Handled with caching/backoff.
- Excluded categories: Skip gracefully.
- Unavailable items: Grok suggests in-stock alternatives.

## 16. Testing Strategy

- Unit, integration (mocked APIs), end-to-end tests.

## 17. Deployment & Observability

- Backend on Render/Railway.
- Basic logging and usage dashboard.

## 18. Non-Functional Requirements

- **Performance:** Plan generation < 5 seconds when online.
- **Offline Support:** Cached plans available.
- **Scalability:** Designed to grow from small restricted base to larger user numbers as revenue permits.
