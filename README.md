# AdultGen

Telegram-first AI media generation platform with a backend-first Core API and a responsive AdultGen Studio client.

## Current product surfaces

- `src/adultgen` — FastAPI Core API, domain rules, provider callbacks, billing, moderation and storage.
- `src/adultgen/telegram_gateway` — replaceable Telegram delivery/gateway channel.
- `apps/studio_app` — new responsive web and Telegram Mini App client.
- `docker-compose.production.yml` — Postgres, Redis, MinIO, backend, Studio and Nginx gateway.

The previous frontend was removed and is not used as a base. The current rebuild contract is documented in [`docs/FRONTEND_REBUILD.md`](docs/FRONTEND_REBUILD.md).

## Studio routes

- `/feed`
- `/create`
- `/publication/{id}`
- `/profile/{public_id}`
- `/projects`
- `/billing`

## Local frontend verification

```bash
cd apps/studio_app
npm run verify
```

The Studio package intentionally has no runtime or build dependencies. Node 22 runs syntax checks, unit tests and the deterministic static build.

## Local backend infrastructure

```bash
cp .env.example .env
docker compose up -d
uvicorn adultgen.apps.core_api:app --reload
```

## Production-like launch

```bash
cp deploy/env/production.env.example .env.production
chmod 600 .env.production
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

Default staging URLs:

- Studio: `http://127.0.0.1:4444/`
- API health: `http://127.0.0.1:4444/api/health`
- gateway health: `http://127.0.0.1:4444/healthz`

## Architecture principles

- Telegram bots and web clients are replaceable channels around one Core API.
- Canonical users are keyed independently from a specific bot.
- Credits use an append-only wallet ledger.
- Payment webhooks are captured before processing.
- Temporary generation media expires unless published.
- Adult feed access requires consent and backend moderation.
- Model capability validation and pricing remain authoritative on the backend.

Read `docs/MODEL_CAPABILITIES.md`, `docs/API_CONTRACTS.md` and `docs/SAFETY_COMPLIANCE.md` before changing generation, billing or moderation flows.
