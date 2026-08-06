# AdultGen production deployment runbook

This runbook describes the backend-only production baseline.

It runs:

- `nginx` public gateway on `${HTTP_PORT:-4444}`;
- `backend` FastAPI Core API;
- `postgres` durable application database;
- `redis` durable queue/cache state;
- `minio` S3-compatible object storage;
- one-shot `create-buckets` setup task;
- one-shot `migrate` Alembic task.

No frontend is currently deployed. The root path intentionally returns `frontend_not_installed`. See `docs/FRONTEND_RESET.md`.

The backend stack is suitable for controlled staging and integration work. It is not ready for full public paid production launch until provider, payment, safety, media-processing, monitoring, backup, and restore checks are complete.

## 0. Before you start

Requirements:

- Ubuntu or another Linux host with Docker Engine and Compose v2;
- outbound HTTPS access for provider APIs;
- free ports for `${HTTP_PORT:-4444}` and `${MINIO_CONSOLE_PORT:-9001}`;
- persistent disk capacity for Postgres and MinIO.

The default `HTTP_PORT=4444` avoids conflicts with host-level Nginx, Apache, Caddy, and privileged port setup. Put TLS termination in front of this port for public deployment.

## 1. Prepare environment

```bash
cp deploy/env/production.env.example .env.production
chmod 600 .env.production
```

Replace every `change-me-*` and `replace-me-*` value. The bootstrap helper refuses to start with placeholder secrets.

Public callback URLs go through the `/api` prefix:

```env
BILLING_BASE_URL=https://your-domain.example
KIE_CALLBACK_URL=https://your-domain.example/api/webhooks/kie
```

Local smoke values:

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

The helper builds the backend image, starts infrastructure, creates buckets, runs migrations, starts the backend and gateway, and verifies health.

## 3. Manual launch sequence

```bash
docker compose --env-file .env.production -f docker-compose.production.yml build
docker compose --env-file .env.production -f docker-compose.production.yml up -d postgres redis minio
docker compose --env-file .env.production -f docker-compose.production.yml --profile setup run --rm create-buckets
docker compose --env-file .env.production -f docker-compose.production.yml --profile migrate run --rm migrate
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend nginx
```

## 4. Verify health

```bash
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/healthz
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/api/health
```

Expected:

```text
ok
{"status":"ok"}
```

The root path should return HTTP 404 with:

```json
{"detail":"frontend_not_installed"}
```

Inspect failures with:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml ps
docker compose --env-file .env.production -f docker-compose.production.yml logs --tail=120 backend nginx postgres redis minio
```

## 5. Public paths

- Gateway health: `/healthz`
- Core API: `/api/*`
- API health: `/api/health`
- Kie webhook: `/api/webhooks/kie`
- CrocoPay webhook: `/api/webhooks/payments/crocopay`
- All non-API web paths: 404 until a replacement frontend is deployed
- MinIO console: `127.0.0.1:${MINIO_CONSOLE_PORT:-9001}`

## 6. Backend smoke checklist

1. Run the healthcheck helper.
2. Confirm `/api/health` returns `{"status":"ok"}`.
3. Confirm the root path does not serve a stale frontend.
4. Confirm Postgres, Redis, and MinIO are healthy.
5. Confirm all required buckets exist.
6. Exercise Kie and payment callbacks with approved test credentials.
7. Inspect backend and gateway logs.
8. Perform a backup and restore drill before public launch.

## 7. Production limitations

Real launch still requires validation of:

- Kie provider credentials and callback delivery;
- approved payment provider credentials and webhook delivery;
- adult-category approval from payment, provider, cloud, and distribution partners;
- real generated-media import and derivative processing;
- moderation operations and audit trails;
- metrics, tracing, alerting, and error reporting;
- backup and restore procedures;
- a separately approved replacement frontend, if a web client is required.

## 8. Operational rules

- Do not expose `backend`, `postgres`, `redis`, or `minio` publicly.
- Keep public ingress through `nginx` only.
- Run `create-buckets` after changing bucket names.
- Run `migrate` before deploying backend schema changes.
- Keep `ADMIN_API_TOKEN`, `JWT_SECRET`, provider tokens, and payment secrets outside Git.
- Use TLS in front of the gateway in production.
- Confirm payment/provider/cloud terms in writing before processing adult traffic.

## 9. Update and rollback

Update:

```bash
git pull origin main
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

Controlled restart:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml build backend
docker compose --env-file .env.production -f docker-compose.production.yml --profile migrate run --rm migrate
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend nginx
```

Image-tag rollback:

```bash
ADULTGEN_IMAGE_TAG=previous-tag docker compose --env-file .env.production -f docker-compose.production.yml up -d backend nginx
```

Database rollbacks are migration-specific. Do not downgrade blindly after new data formats have been written.

## 10. Backup targets

Back up:

- `postgres-data` volume;
- `minio-data` volume;
- `.env.production` in a separate secure vault.

Redis is append-only in this pack, but application truth should remain in Postgres and object storage.
