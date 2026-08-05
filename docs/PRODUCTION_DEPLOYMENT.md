# AdultGen production deployment

This runbook is the production-oriented deployment pack for the web-first AdultGen stack.

It runs:

- `nginx` public gateway on `${HTTP_PORT:-80}`;
- `web` static Vite/React application;
- `backend` FastAPI Core API;
- `postgres` durable application database;
- `redis` durable queue/cache state;
- `minio` S3-compatible object storage;
- one-shot `create-buckets` setup task;
- one-shot `migrate` Alembic task.

## 1. Prepare environment

```bash
cp deploy/env/production.env.example .env.production
chmod 600 .env.production
```

Fill every `change-me-*` / `replace-me-*` value before starting the stack. The helper script refuses to start while placeholders are still present.

Important public callback URLs should point through the gateway `/api` prefix:

```env
BILLING_BASE_URL=https://your-domain.example
KIE_CALLBACK_URL=https://your-domain.example/api/webhooks/kie
```

## 2. One-command bootstrap

```bash
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

This builds images, starts infrastructure, creates buckets, runs migrations, starts the app tier, and verifies public health.

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

Start application tier:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend web nginx
```

## 4. Verify health

```bash
curl -fsS http://127.0.0.1:${HTTP_PORT:-80}/healthz
curl -fsS http://127.0.0.1:${HTTP_PORT:-80}/api/health
```

Expected responses:

```text
ok
{"status":"ok"}
```

## 5. Access paths

- User web app: `/`
- Admin web panel: `/admin`
- Core API through gateway: `/api/*`
- Kie webhook: `/api/webhooks/kie`
- CrocoPay webhook: `/api/webhooks/payments/crocopay`
- MinIO console: `127.0.0.1:${MINIO_CONSOLE_PORT:-9001}` by default.

## 6. Operational rules

- Do not expose `backend`, `postgres`, `redis`, or `minio` ports publicly.
- Keep public ingress through `nginx` only.
- Run `create-buckets` after changing bucket names.
- Run `migrate` before deploying a backend image that changes ORM models or Alembic revisions.
- Keep `ADMIN_API_TOKEN`, `JWT_SECRET`, provider tokens, and payment secrets outside Git.
- Use TLS in front of this stack in real production. This Compose file intentionally binds plain HTTP so it can run behind Caddy, Traefik, Cloudflare Tunnel, an L7 load balancer, or host-level certbot/Nginx.
- For adult content launch, confirm payment/provider/cloud terms in writing before processing real traffic.

## 7. Rollback shape

For an image-tagged release:

```bash
ADULTGEN_IMAGE_TAG=previous-tag docker compose --env-file .env.production -f docker-compose.production.yml up -d backend web nginx
```

Database rollbacks are migration-specific. Do not downgrade blindly if a release wrote new data formats.

## 8. Logs

```bash
sh deploy/scripts/tail-production-logs.sh
sh deploy/scripts/tail-production-logs.sh backend
sh deploy/scripts/tail-production-logs.sh nginx
```

## 9. Backup targets

At minimum back up:

- `postgres-data` volume;
- `minio-data` volume;
- `.env.production` secret file stored separately in a secure vault.

Redis is append-only in this Compose pack, but application truth should still live in Postgres and object storage.
