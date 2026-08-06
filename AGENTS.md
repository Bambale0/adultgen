# AdultGen agent operating guide

This repository is a backend-first adult AI media platform. Telegram bots and future web clients are replaceable channels around the Core API.

Use this file as the operating contract for Codex-style agents, AI assistants, and human developers working in this repo.

## Current product shape

- Core API: FastAPI backend under `src/adultgen`.
- Telegram gateway: backend channel integration under `src/adultgen/telegram_gateway`.
- Storage: local development adapter and S3-compatible production adapter.
- Production pack: `docker-compose.production.yml`, `deploy/`, and `docs/PRODUCTION_DEPLOYMENT.md`.
- Frontend: intentionally absent after the 2026-08-07 reset. See `docs/FRONTEND_RESET.md`.

## Hard rules

1. Keep changes focused and PR-based.
2. Do not push risky rewrites directly into `main`.
3. Do not claim production readiness unless CI is green and blockers are explicitly closed.
4. Do not introduce a second wallet balance. Credits must flow through append-only wallet ledger entries.
5. Do not bypass adult-safety policy checks.
6. Do not implement adult payment/provider workarounds. Payment/provider/cloud usage must follow written approval and terms.
7. Do not store secrets in the repository.
8. Do not expose the backend, Postgres, Redis, or MinIO publicly. Public ingress goes through Nginx.
9. Do not restore, copy, or selectively resurrect code from the removed `apps/mini_app` or `apps/web_app` implementations.
10. A new frontend requires an approved product brief, route map, state model, API-client boundary, design system, responsive specification, accessibility baseline, and acceptance tests before implementation.

## Required checks before merge

Every PR should pass:

```bash
ruff check .
pytest
```

A future frontend must introduce its own lint, typecheck, unit-test, build, and end-to-end gates in the same PR that adds the client scaffold.

## Branch and PR workflow

1. Create a focused branch from `main`.
2. Make one logical change.
3. Add or update tests.
4. Open a draft PR.
5. Wait for CI.
6. Fix failures.
7. Mark ready only after green CI.
8. Merge to `main`.

## Frontend reset contract

The current absence of frontend code is intentional, not an unfinished deletion.

Before a replacement frontend is created:

1. Confirm the primary product surface: Telegram Mini App, public web app, admin app, or a deliberate combination.
2. Freeze the route and user-flow map.
3. Define authentication, 18+ consent, moderation, billing, upload, generation, publication, and delivery states.
4. Create a small design system and reusable application shell before feature pages.
5. Use typed API adapters generated from or checked against backend contracts.
6. Ship one coherent client implementation, not parallel competing versions.
7. Add visual regression and critical-path E2E tests before calling it production-ready.

## Launch workflow for backend staging

```bash
cp deploy/env/production.env.example .env.production
chmod 600 .env.production
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

Endpoints:

- gateway health: `http://127.0.0.1:${HTTP_PORT:-4444}/healthz`
- Core API health: `http://127.0.0.1:${HTTP_PORT:-4444}/api/health`
- MinIO console: `http://127.0.0.1:${MINIO_CONSOLE_PORT:-9001}`

The root web path intentionally returns `frontend_not_installed` until a new frontend is approved and deployed.

## Safety and compliance boundaries

AdultGen must block or route to review content involving:

- minors or underage indicators;
- non-consensual intimate imagery or real-person sexual identity abuse;
- public figures in sexualized contexts;
- coercion, trafficking, hidden camera, exploitation, bestiality, incest, or violence;
- other categories defined by `src/adultgen/domain/adult_policy.py` and moderation services.

Do not weaken policy checks for demo convenience.

## Documentation ownership

Update these docs when relevant:

- `AGENTS.md` — contributor and agent operating rules;
- `docs/PRODUCTION_DEPLOYMENT.md` — backend deployment runbook;
- `docs/FRONTEND_RESET.md` — frontend baseline and re-entry criteria;
- `.env.example` / `deploy/env/production.env.example` — runtime configuration templates.

## Definition of done

A task is done only when:

- code is merged into `main`;
- CI is green;
- docs are updated if runtime or product behavior changed;
- remaining limitations are explicitly called out;
- no secrets are committed;
- no safety, payment, or provider policy has been bypassed.
