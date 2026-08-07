# AdultGen agent operating guide

AdultGen is a web-first adult AI media platform with a FastAPI Core API and a fresh Orbital Web client. The rejected historical frontend was removed and must not be restored.

Use this file as the operating contract for Codex-style agents, AI assistants, and human developers working in this repo.

## Current product shape

- Core API: FastAPI backend under `src/adultgen`.
- Web frontend: fresh React/Vite implementation under `apps/orbital_web`.
- Frontend product brief: `docs/FRONTEND_PRODUCT_BRIEF_V2.md`.
- Admin API: backend endpoints protected by `ADMIN_API_TOKEN`; admin UI remains a separate future surface.
- Storage: local development adapter and S3-compatible production adapter.
- Production pack: `docker-compose.production.yml`, `deploy/`, and `docs/PRODUCTION_DEPLOYMENT.md`.

## Hard rules

1. Keep changes focused and PR-based.
2. Do not push risky rewrites directly into `main`.
3. Do not claim production readiness unless CI is green and blockers are explicitly closed.
4. Do not introduce a second wallet balance. Credits must flow through append-only wallet ledger entries.
5. Do not bypass adult-safety policy checks.
6. Do not implement adult payment/provider workarounds. Payment/provider/cloud usage must follow written approval and terms.
7. Do not store secrets in the repository.
8. Do not expose backend, Postgres, Redis, or MinIO publicly. Public ingress goes through Nginx.
9. Prefer source-level smoke tests for architectural contracts when full integration tests are not yet available.
10. If a PR changes runtime behavior, update the relevant runbook or status doc.
11. Do not restore or copy the rejected `apps/web_app` implementation. New frontend work extends `apps/orbital_web` and the V2 product brief.
12. Anonymous UI must not fetch explicit live feed media before age/session gating.

## Required checks before merge

Every PR should pass:

```bash
ruff check .
pytest
cd apps/orbital_web && npm install && npm run typecheck && npm run build
```

GitHub Actions runs backend and Orbital Web gates. Keep UI changes draft until green CI and visual staging review.

## Branch and PR workflow

1. Create a focused branch from `main`.
2. Make one logical change.
3. Add or update tests.
4. Open draft PR.
5. Wait for CI.
6. Fix Ruff/Pytest/typecheck/build failures.
7. Review visual staging against the approved Orbital reference.
8. Mark ready only after green CI.
9. Merge to `main`.

## Frontend direction

The active visual/product contract is `docs/FRONTEND_PRODUCT_BRIEF_V2.md`.

Keep the supplied Orbital language coherent:

- carbon-black layered surfaces;
- magenta primary action / cyan system status / acid-green secondary status;
- condensed command typography + monospaced data typography;
- 280px desktop sidebar and compact mobile sector navigation;
- tactical panels, scanlines, restrained neon glow, masonry feed;
- feed, deploy studio, telemetry, profile, billing as first-class routes.

Do not collapse the product back into a generic dashboard template.

## Launch workflow for local staging/demo

```bash
cp deploy/env/production.env.example .env.production
chmod 600 .env.production
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

Open:

- web app: `http://127.0.0.1:4444/`
- API health: `http://127.0.0.1:4444/api/health`
- gateway health: `http://127.0.0.1:4444/healthz`
- MinIO console: `http://127.0.0.1:${MINIO_CONSOLE_PORT:-9001}`

## Readiness status

Current expected status:

- backend/API stack is ready for controlled staging/demo validation;
- Orbital Web foundation is review/staging capable, not yet fully production-ready;
- full public paid production launch is blocked until provider/payment approvals and end-to-end callbacks are validated.

Important blockers to keep visible:

- real blur/thumbnail processing is still not production-grade;
- provider/payment written adult-category approval is required before real paid traffic;
- staging must validate webhooks, payment callbacks, media delivery, admin actions, backup/restore;
- visual/mobile/E2E review must be completed for Orbital Web.

## Safety and compliance boundaries

AdultGen must block or route to review content involving minors, non-consensual intimate imagery, sexualized public figures, coercion/exploitation, hidden camera, bestiality, incest, sexual violence, and all other categories defined by backend policy and moderation services.

Do not weaken policy checks for demo convenience.

## Documentation ownership

Update these docs when relevant:

- `AGENTS.md` — contributor/agent operating rules;
- `docs/FRONTEND_PRODUCT_BRIEF_V2.md` — active frontend product/design contract;
- `docs/PRODUCTION_DEPLOYMENT.md` — runtime runbook;
- `docs/FRONTEND_REMOVED.md` — historical record of rejected frontend;
- `.env.example` / `deploy/env/production.env.example` — runtime configuration templates.

## Definition of done

A task is done only when code is merged into `main`, CI is green, runtime/product docs are current, remaining limitations are explicit, no secrets are committed, and no safety/payment/provider policy has been bypassed.
