# AdultGen agent operating guide

This repository is currently an API-first adult AI media platform backend. The previous web frontend was intentionally removed because it was not acceptable as a product UI.

Use this file as the operating contract for Codex-style agents, AI assistants, and human developers working in this repo.

## Current product shape

- Core API: FastAPI backend under `src/adultgen`.
- Admin API: backend endpoints protected by `ADMIN_API_TOKEN`.
- Web frontend: intentionally removed. See `docs/FRONTEND_REMOVED.md`.
- Storage: local development adapter and S3-compatible production adapter.
- Production pack: API-only `docker-compose.production.yml`, `deploy/`, and `docs/PRODUCTION_DEPLOYMENT.md`.

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

## Future frontend rebuild rule

The old frontend is not a base for further iteration.

Before adding a new frontend, create and approve:

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
- frontend removal notice: `http://127.0.0.1:4444/`
- MinIO console: `http://127.0.0.1:${MINIO_CONSOLE_PORT:-9001}`

There is no user web app or admin web panel in this repo until a new frontend is built.

## Readiness status

Current expected status:

- backend/API stack is ready for controlled staging/demo validation;
- frontend is intentionally removed and not ready;
- full public paid production launch is blocked until a new UI, provider/payment approvals, and end-to-end callbacks are validated.

Important blockers to keep visible:

- no production frontend exists;
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

---

## Shared Engineering Baseline — Start + AuRoom

This shared baseline supplements repository-specific rules; it never replaces stricter local architecture, release, security, channel, or product constraints.

### Engineering playbook and task flow
- Treat `Bambale0/skills` as the primary engineering playbook. Also inspect relevant safe guidance from `Bambale0/claw` and `anthropics/skills`.
- Do not use deprecated skills. Use in-progress skills only when they fit and account for their experimental status.
- Large ambiguous work: use a wayfinder-style flow.
- Feature development where applicable: `grill-with-docs → to-spec → to-tickets → implement → tdd → code-review`.
- Debugging: diagnose from evidence first (logs, telemetry, DB/runtime state, reproducible behavior), then patch.
- Never claim tests, CI, deploy, or production state that was not actually verified.

### Mandatory feature preflight and CONTEXT ledger
Before implementing any material feature or cross-cutting refactor, perform a fresh audit of the current repository state. Inspect relevant docs/specs/ADRs, code, schemas/migrations, auth, admin/config surfaces, tests, CI, integrations, and runtime telemetry when available.

Maintain `CONTEXT.md` as a live execution ledger for active work. Record baseline commit/SHA, current state, what exists/partial/missing/reusable, risks/dependencies, migrations/integrations/permissions/rollout impact, intended user outcome and acceptance criteria, no-hardcode/configuration decisions, observability plan, test seams, numbered steps with progress evidence, final verification, and follow-ups. Do not reconstruct it only at the end.

### No hardcode and control plane
Mutable business/runtime behavior must not require source edits, manual SQL, or redeploys. Prices, tariffs, categories, statuses, SLA, prompts, provider/model selection, routing, thresholds, schedules, feature availability, notification templates, retry/fallback policy, permissions, and integration mappings should normally be typed, validated, database-backed, scoped, auditable, and manageable through the appropriate authenticated admin/control plane.

Secrets are not business configuration. Never expose plaintext secrets in frontend bundles, logs, API responses, Git, or ordinary database settings.

### Architecture and integrations
- Prefer a modular monolith with explicit module interfaces and seams unless scaling, security, reliability, or ownership evidence justifies extraction.
- Important cross-module state changes should use explicit, typed, versionable, traceable, retry-safe/idempotent events where eventing is appropriate.
- Keep provider-specific HTTP payload handling behind typed integration adapters/ports.
- External integrations must define auth, finite timeouts, bounded retries/backoff, rate-limit behavior, idempotency, webhook verification where supported, reconciliation, data ownership/sync direction, observability, and failure semantics.
- Avoid parallel sources of truth.

### Security and AI authority
Authorization is enforced server-side. UI hiding is never sufficient. Preserve ownership/tenant boundaries where applicable and treat data leakage as a release blocker.

AI may classify, summarize, extract, recommend, and execute only explicitly permitted workflows. It must not bypass authorization, approvals, deterministic validation, financial controls, legal signing, or tenant/data isolation. Low-confidence or high-impact actions should fail closed or escalate.

### Observability first
Logging and telemetry are part of the implementation. Critical paths should expose what happened, when, for which actor/entity/scope, through which provider, duration, retries, failure reason, and user-visible effect. Propagate useful request/trace/correlation IDs. Never log secrets or unnecessary personal data.

### Test-first vertical slices and completion gate
Prefer `failing behavior test → minimal implementation → focused checks → next slice`.

For every material feature, explicitly cover where applicable: unit/domain behavior, DB/repository integration and migrations, authorization/ownership/tenant isolation, provider contracts, workflow/idempotency/retry, API integration, browser/bot E2E, smoke/deployability, observability/audit, and admin configurability/no-hardcode.

Regression fixes should get regression tests when feasible. Do not mark work complete until applicable acceptance criteria and checks pass, CI is green for the exact commit, review against repository standards and the originating spec is complete, and no unresolved high-severity finding remains.

### Delivery
Final engineering reports should state what changed; important files/components; skills/flows used; exact tests/checks and results; migrations/config/admin changes; risks/follow-ups; and PR/commit/deploy SHA when applicable.
