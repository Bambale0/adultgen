# AdultGen agent operating guide

This repository is a web-first adult AI media platform. Telegram is a companion channel, not the primary product surface.

Use this file as the operating contract for Codex-style agents, AI assistants, and human developers working in this repo.

## Current product shape

- Core API: FastAPI backend under `src/adultgen`.
- Web app: Vite/React frontend under `apps/web_app`.
- Admin panel: standalone `/admin` frontend entry using `ADMIN_API_TOKEN`.
- Storage: local development adapter and S3-compatible production adapter.
- Production pack: `docker-compose.production.yml`, `deploy/`, and `docs/PRODUCTION_DEPLOYMENT.md`.

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
10. If a PR changes runtime behavior, update the relevant runbook or readiness doc.

## Required checks before merge

Every PR should pass:

```bash
ruff check .
pytest
cd apps/web_app && npm run typecheck && npm run lint && npm run build
```

GitHub Actions already runs these gates. A PR should stay draft until they pass.

## Branch and PR workflow

1. Create a focused branch from `main`.
2. Make one logical change.
3. Add or update tests.
4. Open draft PR.
5. Wait for CI.
6. Fix Ruff/Pytest/typecheck/build failures.
7. Mark ready only after green CI.
8. Merge to `main`.

Preferred PR order for frontend hardening:

1. Replace inline `App.tsx` shell with `AppShell`, `Sidebar`, `TopBar`.
2. Extract `Studio` feature module.
3. Extract `Billing` feature module.
4. Extract `Feed/Profile/Collection` feature modules.
5. Add shared UI primitives.
6. Add Vitest/React Testing Library.
7. Add Playwright smoke E2E.
8. Improve safety UX and report flows.
9. Add frontend observability hooks.
10. Run staging checklist.

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

- user app: `http://127.0.0.1/`
- admin panel: `http://127.0.0.1/admin`
- API health: `http://127.0.0.1/api/health`
- MinIO console: `http://127.0.0.1:${MINIO_CONSOLE_PORT:-9001}`

## Readiness status

The latest frontend readiness report lives at:

- `docs/FRONTEND_READINESS_REPORT.md`

Current expected status:

- ready for controlled staging/demo iteration;
- not ready for full public paid production launch until blockers are closed.

Important blockers to keep visible:

- real blur/thumbnail processing is still not production-grade;
- provider/payment written adult-category approval is required before real paid traffic;
- frontend still needs feature extraction, UI test coverage, and E2E smoke tests;
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
- `docs/FRONTEND_AUDIT_ROADMAP.md` — frontend improvement plan;
- `docs/FRONTEND_READINESS_REPORT.md` — honest readiness status;
- `.env.example` / `deploy/env/production.env.example` — runtime configuration templates.

## Definition of done

A task is done only when:

- code is merged into `main`;
- CI is green;
- docs are updated if runtime/product behavior changed;
- remaining limitations are explicitly called out;
- no secrets are committed;
- no safety/payment/provider policy has been bypassed.
