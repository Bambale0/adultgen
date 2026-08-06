# AdultGen

Telegram-first AI media generation platform with a backend-first architecture: multi-reference cinematic workflows, internal credits, partner payouts, moderation, public feed APIs, and replaceable Telegram bot channels.

## Frontend status

All previous frontend implementations were removed on 2026-08-07. The former `apps/mini_app` and `apps/web_app` codebases are not accepted as a foundation for further work.

The repository currently contains **no production frontend**. A replacement client must be designed and implemented as a new product surface against the existing API contracts. See [`docs/FRONTEND_RESET.md`](docs/FRONTEND_RESET.md).

## Documentation languages

- English documentation entrypoint: [`docs/en/README.md`](docs/en/README.md)
- Русская документация: [`docs/ru/README.md`](docs/ru/README.md)

Canonical detailed English documents currently live in the root `docs/` directory. Russian companion documents live in `docs/ru/` and must be updated together with the English docs when architecture, model capabilities, billing, safety, or API contracts change.

## Architecture direction

AdultGen is designed as a backend-first platform:

- Telegram bots and future web clients are replaceable gateway clients.
- Canonical users are keyed by `telegram_user_id`, not by bot.
- Wallets use an append-only ledger.
- Payment webhooks are captured as immutable raw records before processing.
- Temporary generation media expires after 24 hours unless published.
- Published profile/feed media is stored permanently until user/admin deletion.
- Adult feed access requires 18+ consent and admin-controlled moderation.
- Model capabilities are explicit: Seedream and Seedance payloads are selected through scenario-specific provider capability rules, not a single generic generation form.

## Backend product scope

- FastAPI Core API.
- Telegram gateway contracts.
- Project, scene, profile, collection, publication, moderation, billing, wallet, and subscription APIs.
- Seedream/Seedance provider payload and callback infrastructure.
- S3-compatible media storage.
- Production Docker Compose baseline for API, Postgres, Redis, MinIO, and Nginx.

## Repository structure

```text
docs/                         architecture, contracts, runbooks and ADRs
src/adultgen/                 backend application and domain code
tests/                        backend and repository-contract tests
deploy/                       API-only production deployment pack
Dockerfile                    production Core API image
docker-compose.production.yml canonical production service graph
```

There is intentionally no `apps/` frontend directory in the current baseline.

## Local infrastructure

```bash
cp .env.example .env
docker compose up -d
```

Run Core API after installing dependencies:

```bash
python -m pip install -e ".[dev]"
uvicorn adultgen.apps.core_api:app --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

## Required checks

```bash
ruff check .
pytest
```

## Development status

The backend baseline remains active. Frontend work is paused until a new information architecture, UX flow, design system, API-client boundary, and acceptance criteria are approved. Do not restore deleted frontend files from repository history.
