# Frontend reset decision

Date: 2026-08-07
Status: accepted

## Decision

Remove every existing frontend implementation from the repository and return AdultGen to a backend-first baseline.

Deleted implementations:

- `apps/mini_app`
- `apps/web_app`
- their UI tests, build jobs, Docker images, Nginx SPA configuration, readiness reports, audit roadmaps, and pivot notes

The deleted code must not be used as a starting point for a replacement client.

## Why

The repository accumulated two competing frontend directions, duplicated deployment configuration, oversized page components, source-inspection tests instead of product-level tests, and multiple incremental visual rewrites without a stable product contract. Continuing to patch those implementations would preserve the wrong architecture and increase rework.

## What remains

- Core API and domain model
- Telegram gateway contracts
- authentication and 18+ consent APIs
- generation, media, profile, collection, publication, moderation, billing, wallet, subscription, and admin APIs
- backend tests
- API-only production deployment

## Replacement frontend entry criteria

No implementation work should begin until the following are approved:

1. Primary surface and scope: Mini App, public web, admin, or an explicit multi-client plan.
2. Route map and critical user journeys.
3. Authentication, Telegram init-data, session, and 18+ consent state machine.
4. Generation workflow states, error states, retries, and result delivery.
5. Media upload, profile, collection, publication, feed, report, and moderation flows.
6. Billing and subscription UX with exact backend contracts.
7. Design tokens, typography, spacing, component primitives, responsive breakpoints, and accessibility rules.
8. Typed API client boundary and server-state strategy.
9. Unit, integration, visual-regression, and critical-path E2E test plan.
10. Deployment topology and observability.

## Implementation rules for the next client

- Build one coherent frontend direction at a time.
- Start with the application shell, navigation, state model, and API adapters.
- Keep feature modules isolated from transport and Telegram-specific globals.
- Avoid monolithic page components and CSS override layers.
- Do not use `latest` dependency versions in production manifests.
- Lock dependencies and commit the lockfile.
- Add CI gates with the scaffold, not later.
- Do not claim readiness from static source assertions; validate behavior.

## Current runtime behavior

The production gateway continues to expose `/api/*` and `/healthz`. All other web paths return:

```json
{"detail":"frontend_not_installed"}
```
