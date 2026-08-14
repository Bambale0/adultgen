# AdultGen agent operating guide

This repository contains a web-first adult AI media platform backed by a FastAPI service and a new staging web implementation. The previous frontend was intentionally removed because it was not acceptable as a product UI; it remains removed.

Use this file as the operating contract for Codex-style agents, AI assistants, and human developers working in this repo.

## Current product shape

- Core API: FastAPI backend under `src/adultgen`.
- Admin API: backend endpoints protected by `ADMIN_API_TOKEN`.
- Web frontend: new React/Vite implementation under `apps/web_app`; see `docs/WEB_PRODUCT_BRIEF.md`.
- Storage: local development adapter and S3-compatible production adapter.
- Production pack: web + API `docker-compose.production.yml`, `deploy/`, and `docs/PRODUCTION_DEPLOYMENT.md`.

## Hard rules

1. Keep changes small and PR-based.
2. Do not push risky rewrites directly into `main`.
3. Do not claim production readiness unless CI is green and blockers are explicitly closed.
4. Do not introduce a second wallet balance. Credits must flow through append-only wallet ledger entries.
5. Do not bypass adult-safety policy checks.
6. Do not implement adult payment/provider workarounds. Payment/provider/cloud usage must follow written approval and terms.
7. Do not store secrets in the repository.
8. Do not expose backend, Postgres, Redis, or MinIO publicly. Public ingress goes through Nginx.
9. Prefer source-level smoke tests for architectural contracts when full integration tests are not yet available.
10. If a PR changes runtime behavior, update the relevant runbook or status doc.
11. Do not restore the removed frontend or copy it back. A future UI must start as a new implementation from an approved product brief.

## Required checks before merge

Every PR should pass:

```bash
ruff check .
pytest
cd apps/web_app && npm run typecheck && npm test && npm run build
```

GitHub Actions runs these backend gates. A PR should stay draft until they pass.

## Branch and PR workflow

1. Create a focused branch from `main`.
2. Make one logical change.
3. Add or update tests.
4. Open draft PR.
5. Wait for CI.
6. Fix Ruff/Pytest failures.
7. Mark ready only after green CI.
8. Merge to `main`.

## Frontend rebuild rule

The old frontend is not a base for further iteration.

The rebuild was authorized against the approved reference direction and must retain:

1. Product flow map.
2. Wireframes for public feed, generation composer, auth/18+ gate, billing, profile, and admin.
3. Component system decision.
4. E2E test plan.
5. Separate PR series with visible staging review before production docs claim frontend readiness.

## Launch workflow for local staging/demo

Use the production-like Compose pack from the repository root:

```bash
cp deploy/env/production.env.example .env.production
chmod 600 .env.production
```

Edit `.env.production` and replace all `change-me` / `replace-me` values.

Then run:

```bash
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

Open:

- gateway health: `http://127.0.0.1:4444/healthz`
- API health: `http://127.0.0.1:4444/api/health`
- web app: `http://127.0.0.1:4444/`
- MinIO console: `http://127.0.0.1:${MINIO_CONSOLE_PORT:-9001}`

The user web app and locked admin shell are included for staging validation.

## Readiness status

Current expected status:

- backend/API stack and the new web implementation are ready for controlled staging/demo iteration;
- new frontend is implemented for staging review, not yet an unconditional public paid launch;
- AdultGen is not ready for full public paid production launch until provider/payment approvals and end-to-end callbacks are validated.

Important blockers to keep visible:

- Google OAuth and Telegram website login must be configured and validated on the production domain;
- real blur/thumbnail processing is still not production-grade;
- provider/payment written adult-category approval is required before real paid traffic;
- staging must validate webhooks, payment callbacks, media delivery, admin actions, backup/restore.

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

- `AGENTS.md` — contributor/agent operating rules;
- `docs/PRODUCTION_DEPLOYMENT.md` — runbook for running the stack;
- `docs/FRONTEND_AUDIT_ROADMAP.md` — historical audit and rebuild boundary;
- `docs/FRONTEND_READINESS_REPORT.md` — current frontend staging status;
- `docs/FRONTEND_REMOVED.md` — status of removed frontend and rebuild rules;
- `.env.example` / `deploy/env/production.env.example` — runtime configuration templates.

## Definition of done

A task is done only when:

- code is merged into `main`;
- CI is green;
- docs are updated if runtime/product behavior changed;
- remaining limitations are explicitly called out;
- no secrets are committed;
- no safety/payment/provider policy has been bypassed.
