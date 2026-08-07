# AdultGen production deployment runbook

This runbook is the production-oriented deployment pack for AdultGen Core API plus the new Orbital Web frontend.

The rejected historical `apps/web_app` UI remains deleted. The current web surface is a fresh implementation under `apps/orbital_web`, based on the approved Orbital product brief in `docs/FRONTEND_PRODUCT_BRIEF_V2.md`.

It runs:

- `nginx` public gateway on `${HTTP_PORT:-4444}`;
- `web` static Orbital Web container;
- `backend` FastAPI Core API;
- `postgres` durable application database;
- `redis` durable queue/cache state;
- `minio` S3-compatible object storage;
- one-shot `create-buckets` setup task;
- one-shot `migrate` Alembic task.

Current intended status:

- backend/API stack is suitable for controlled staging/demo validation;
- Orbital Web is suitable for UI staging/review, not yet declared fully production-ready;
- public paid launch still requires provider/payment approval plus end-to-end callback and media validation.

## 0. Before you start

Requirements on the host:

- Linux host with Docker Engine and Compose v2;
- outbound HTTPS access for provider APIs and Google Fonts (or self-host fonts later);
- free local ports for `${HTTP_PORT:-4444}` and `${MINIO_CONSOLE_PORT:-9001}`;
- enough disk for Postgres and MinIO volumes.

## 1. Prepare environment

```bash
cp deploy/env/production.env.example .env.production
chmod 600 .env.production
```

Fill every `change-me-*` / `replace-me-*` value before starting the stack. The helper script refuses to start while placeholders are still present.

Public callback URLs continue to point through `/api`:

```env
BILLING_BASE_URL=https://your-domain.example
KIE_CALLBACK_URL=https://your-domain.example/api/webhooks/kie
```

For a local smoke run:

```env
HTTP_PORT=4444
BILLING_BASE_URL=http://127.0.0.1:4444
KIE_CALLBACK_URL=http://127.0.0.1:4444/api/webhooks/kie
```

## 2. One-command bootstrap

```bash
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

The script builds backend + Orbital Web, starts infrastructure, creates buckets, runs migrations, then starts `backend web nginx`.

## 3. Manual launch sequence

```bash
docker compose --env-file .env.production -f docker-compose.production.yml build
docker compose --env-file .env.production -f docker-compose.production.yml up -d postgres redis minio
docker compose --env-file .env.production -f docker-compose.production.yml --profile setup run --rm create-buckets
docker compose --env-file .env.production -f docker-compose.production.yml --profile migrate run --rm migrate
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend web nginx
```

## 4. Verify health

```bash
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/healthz
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/api/health
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/
```

Expected:

- `/healthz` -> gateway `ok`;
- `/api/health` -> Core API health;
- `/` -> Orbital Web HTML.

## 5. Access paths

- Orbital Web: `http://SERVER_IP:4444/`
- Deploy Studio: `http://SERVER_IP:4444/studio`
- Telemetry: `http://SERVER_IP:4444/missions`
- Operator profile: `http://SERVER_IP:4444/profile`
- Credits: `http://SERVER_IP:4444/billing`
- Core API: `http://SERVER_IP:4444/api/*`
- Gateway health: `http://SERVER_IP:4444/healthz`

MinIO console remains localhost-bound by default at `http://127.0.0.1:${MINIO_CONSOLE_PORT:-9001}`.

Admin remains API-only in this foundation PR. Use `/api/admin/*` with the backend admin authorization contract; a privileged Orbital admin surface should be delivered separately.

## 6. Local frontend development

Run Core API locally, then:

```bash
cd apps/orbital_web
npm install
npm run dev
```

Vite proxies local `/api` requests to `http://127.0.0.1:8000`. Production builds use same-origin `/api` through gateway Nginx.

## 7. Logs

```bash
sh deploy/scripts/tail-production-logs.sh
```

Or:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml logs -f backend web nginx postgres redis minio
```

## 8. Update flow

```bash
git pull origin main
docker compose --env-file .env.production -f docker-compose.production.yml build backend web
docker compose --env-file .env.production -f docker-compose.production.yml --profile migrate run --rm migrate
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend web nginx
sh deploy/scripts/healthcheck-production.sh
```

## 9. Backup and restore baseline

Back up Postgres and MinIO volumes before destructive changes.

```bash
docker compose --env-file .env.production -f docker-compose.production.yml exec postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > adultgen-postgres.sql
```

Object-storage backup should mirror trusted MinIO bucket data from an admin host.

## 10. Frontend rebuild rule

Do not restore `apps/web_app` or copy its UI back. The accepted frontend line begins at `apps/orbital_web` and `docs/FRONTEND_PRODUCT_BRIEF_V2.md`. Production readiness still requires visible staging review and green CI.
