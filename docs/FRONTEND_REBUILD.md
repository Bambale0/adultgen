# AdultGen Studio frontend rebuild

Status: first production-oriented frontend foundation.

The uploaded Stitch package is treated as an approved art-direction reference, not source code to copy. The replacement client lives in `apps/studio_app` and starts from the API-only baseline merged in PR #56.

## Product surface

The primary client is a responsive web application that also runs inside Telegram Mini Apps.

Initial routes:

- `/feed` — public 18+ feed with search and live/trending/following modes;
- `/create` — image/video generation composer;
- `/publication/{id}` — publication detail and remix entrypoint;
- `/profile/{public_id}` — creator profile and archive;
- `/projects` — reserved route for the next project/scene slice;
- `/billing` — reserved credit surface.

## Product states

- unauthenticated demo fallback;
- Telegram Mini App authentication through `/api/auth/telegram-mini-app`;
- accepted/not-accepted adult consent;
- Core API online/offline fallback;
- image/video composer modes;
- reference/no-reference generation modes;
- queued/success/error launch feedback;
- desktop sidebar and mobile bottom navigation.

## Technical decision

The first client is dependency-free browser JavaScript with native ES modules, semantic HTML and tokenized CSS.

Reasons:

- no runtime framework or package-manager supply-chain dependency;
- small Docker image and deterministic build;
- fast Telegram WebView startup;
- clear API boundary in `src/api.js`;
- testable pure contracts in `src/core.js`;
- easy migration to a framework later if product complexity justifies it.

The client must not duplicate backend business rules. Model codes and generation operation payloads are mapped to the existing Core API contracts, while pricing and policy enforcement remain authoritative on the backend.

## Design system

Direction: technical dark interface with restrained cyberpunk/HUD influence.

- deep carbon surfaces;
- pink primary action and cyan system state;
- Archivo Narrow for display, JetBrains Mono for data, Space Grotesk for controls;
- industrial square controls, restrained 12px card radius;
- scanline texture as a non-interactive visual layer;
- visible focus states and reduced-motion support;
- mobile navigation at 880px and below.

## Safety UX

The first entry is blocked by a required 18+ confirmation. The copy explicitly prohibits minors, coercion, exploitation, violence, and identity abuse. After Core authentication the acceptance is synchronized through `/api/adult-consent/accept`.

The UI does not attempt to bypass or replace backend moderation. Backend policy decisions remain authoritative.

## API boundary

Implemented calls:

- `POST /api/auth/telegram-mini-app`;
- `POST /api/auth/web-session`;
- `POST /api/adult-consent/accept`;
- `GET /api/feed`;
- `GET /api/profiles/{public_id}`;
- `GET /api/profiles/me`;
- `GET /api/generations`;
- `POST /api/generations`.

When Telegram/Core auth is unavailable, the app remains usable as an explicit demo with bundled non-explicit media fixtures.

## Verification plan

Current automated gates:

- Node syntax validation for every browser module;
- pure unit tests for routing, API path normalization, feed filtering, escaping, and generation payload mapping;
- deterministic static build with required-output checks;
- backend Ruff/Pytest suite;
- production Compose/source contract tests.

Next PR before production readiness:

1. Playwright desktop/mobile smoke in CI.
2. Telegram WebView device matrix.
3. Real auth + consent smoke.
4. Real generation queue/status flow.
5. Media upload to S3 through presigned contracts.
6. Billing checkout and callback validation.
7. Visual regression snapshots for feed/create/detail/profile.
