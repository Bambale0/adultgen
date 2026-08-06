# Frontend removed

Status: intentionally removed from the repository.

The previous `apps/web_app` implementation was removed because it was not acceptable as a product UI. The repository now keeps the backend/core API, admin API surface, media/generation/payment/domain logic, storage adapters, and production API deployment stack.

## What was removed

- React/Vite web app under `apps/web_app`.
- Frontend Docker image and static nginx config.
- Frontend CI jobs for typecheck/lint/test/build.
- Obsolete frontend audit/readiness docs.

## What remains

- Core FastAPI backend.
- Admin API endpoints.
- Telegram/provider/payment/media domain code.
- Production Compose stack for backend dependencies and API gateway.
- API gateway route: `/api/*`.

## Current launch surface

The production gateway is API-only until a new frontend is designed and approved.

- `/healthz` returns gateway health.
- `/api/health` returns backend health through the gateway.
- `/` returns a plain text notice that the frontend is removed.

## Next frontend rebuild rule

Do not reintroduce a frontend by iterating on the removed UI. Start a new UI package from a clear product brief, design system, and approved reference direction.

Required before adding a new frontend:

1. Product flow map.
2. Wireframes for public feed, generation composer, auth/18+ gate, billing, profile, and admin.
3. Component system decision.
4. E2E test plan.
5. Separate PR series with visible staging review before production docs claim frontend readiness.
