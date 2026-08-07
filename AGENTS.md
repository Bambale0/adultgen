# AdultGen agent operating guide

AdultGen is a backend-first adult AI media platform with one replacement frontend under `apps/studio_app`.

## Current product shape

- Core API: `src/adultgen`.
- Telegram gateway: `src/adultgen/telegram_gateway`.
- Studio web/Mini App: `apps/studio_app`.
- Production ingress: `deploy/nginx/gateway.conf`.
- Frontend architecture and route contract: `docs/FRONTEND_REBUILD.md`.

## Hard rules

1. Keep changes focused and PR-based.
2. Do not restore or copy code from the removed `apps/web_app` implementation.
3. Do not duplicate wallet, pricing, moderation or model-capability business rules in the browser.
4. Credits flow through the append-only backend wallet ledger.
5. Backend adult-safety policy remains authoritative.
6. Do not implement payment/provider workarounds or commit secrets.
7. Do not expose backend, Postgres, Redis or MinIO publicly.
8. Keep the Studio dependency-free unless a framework/library has a documented product need and migration plan.
9. Every visible control must have a real state transition, disabled state, or explicit placeholder label.
10. Runtime changes require CI, source-contract tests and runbook updates in the same PR.

## Required checks

```bash
ruff check .
pytest
cd apps/studio_app && npm run verify
```

## Frontend conventions

- Native ES modules only in the current foundation.
- Pure reusable contracts belong in `src/core.js`.
- Network access belongs in `src/api.js`.
- Do not interpolate untrusted text without `escapeHtml` or safe DOM APIs.
- Use design tokens from `src/styles.css`; do not scatter new hex values across feature code.
- Preserve keyboard focus, reduced motion, semantic landmarks and responsive navigation.
- Keep API paths behind `/api` so Studio and Core share one public origin.
- Demo fixtures must be clearly separated from Core API responses and contain no explicit imagery.

## Delivery workflow

1. Branch from current `main`.
2. Implement one coherent product slice.
3. Add unit/source-contract tests.
4. Run backend and Studio checks.
5. Open a draft PR.
6. Inspect GitHub Actions and fix failures.
7. Perform desktop/mobile visual QA before production signoff.
8. Merge only after green CI and an honest readiness note.

## Safety boundaries

Block or review minors, young-looking subjects, identity abuse, public figures, coercion, trafficking, hidden-camera content, exploitation, bestiality, incest, violence and other categories defined by backend policy.

The 18+ gate is an entry control, not a substitute for moderation.
