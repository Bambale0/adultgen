# AdultGen production deployment runbook

This runbook is the production-oriented deployment pack for the current API-only AdultGen stack.

The previous React/Vite frontend has been intentionally removed from the repository. See `docs/FRONTEND_REMOVED.md`.

It runs:

- `nginx` public API gateway on `${HTTP_PORT:-4444}`;
- `backend` FastAPI Core API;
- `postgres` durable application database;
- `redis` durable queue/cache state;
- `minio` S3-compatible object storage;
- one-shot `create-buckets` setup task;
- one-shot `migrate` Alembic task.

Current intended status:

- backend/API stack is suitable for controlled staging/demo validation;
- there is no production frontend in this repository;
- public paid production launch still requires a new approved frontend, provider/payment approval, and end-to-end callback validation.

## 0. Before you start

Requirements on the host:

- Ubuntu server or another Linux host with Docker Engine and Compose v2;
- outbound HTTPS access from the host/container network for provider APIs;
- free local ports for `${HTTP_PORT:-4444}` and `${MINIO_CONSOLE_PORT:-9001}`;
- enough disk space for Postgres and MinIO volumes.

Port note for Ubuntu:

- `127.0.0.1` without a port means port `80`.
- This stack defaults to `HTTP_PORT=4444` for local/staging smoke tests to avoid conflicts with host Nginx/Apache/Caddy and privileged-port setup.
- For real public production behind host-level TLS, set `HTTP_PORT=80` or put Caddy/Nginx/Cloudflare Tunnel in front of `127.0.0.1:4444`.

From repository root, confirm the deployment files exist:

```bash
ls docker-compose.production.yml
ls deploy/env/production.env.example
ls deploy/scripts/bootstrap-production.sh
ls deploy/scripts/healthcheck-production.sh
```

## 1. Prepare environment

```bash
cp deploy/env/production.env.example .env.production
chmod 600 .env.production
```

Fill every `change-me-*` / `replace-me-*` value before starting the stack. The helper script refuses to start while placeholders are still present.

Public callback URLs should point through the gateway `/api` prefix:

```env
BILLING_BASE_URL=https://your-domain.example
KIE_CALLBACK_URL=https://your-domain.example/api/webhooks/kie
```

For a local smoke/demo run on Ubuntu, use localhost values with the default demo port:

```env
HTTP_PORT=4444
BILLING_BASE_URL=http://127.0.0.1:4444
KIE_CALLBACK_URL=http://127.0.0.1:4444/api/webhooks/kie
```

Provider/payment values can be filled with non-placeholder dummy values for an API-only smoke run. Real generation/payment callbacks require real approved provider credentials.

## 2. One-command bootstrap

```bash
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

This builds the backend image, starts infrastructure, creates buckets, runs migrations, starts the API tier, and verifies gateway/API health.

## 3. Manual launch sequence

Build images:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml build
```

Start infrastructure:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml up -d postgres redis minio
```

Create object-storage buckets:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml --profile setup run --rm create-buckets
```

Run migrations:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml --profile migrate run --rm migrate
```

Start API tier:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend nginx
```

## 4. Verify health

```bash
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/healthz
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/api/health
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/
```

Expected responses:

- `/healthz` -> `ok`
- `/api/health` -> backend health response
- `/` -> plain text notice that the frontend has been removed

## 5. Access paths

Current public gateway paths:

- `http://SERVER_IP:4444/healthz`
- `http://SERVER_IP:4444/api/health`
- `http://SERVER_IP:4444/api/*`

MinIO console remains localhost-bound by default:

- `http://127.0.0.1:${MINIO_CONSOLE_PORT:-9001}`

There is intentionally no web UI route. `/admin` is also unavailable because the previous admin web panel was part of the removed frontend. Use Admin API endpoints under `/api/admin/*` with `ADMIN_API_TOKEN`.

## 6. Logs

```bash
sh deploy/scripts/tail-production-logs.sh
```

Or manually:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml logs -f backend nginx postgres redis minio
```

## 7. Update flow

```bash
git pull origin main
docker compose --env-file .env.production -f docker-compose.production.yml build backend nginx
docker compose --env-file .env.production -f docker-compose.production.yml --profile migrate run --rm migrate
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend nginx
sh deploy/scripts/healthcheck-production.sh
```

## 8. Backup and restore baseline

Back up Postgres and MinIO volumes before destructive changes.

Minimum Postgres dump:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml exec postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > adultgen-postgres.sql
```

Minimum object-storage backup should copy the MinIO bucket data or use `mc mirror` from a trusted admin host.

## 9. Frontend rebuild rule

Do not reintroduce the removed frontend by restoring old files. A new UI must start as a new product/design implementation with its own PR series, tests, and staging review.
