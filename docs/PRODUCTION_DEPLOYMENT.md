# AdultGen production deployment runbook

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

Current intended status:

- ready for controlled staging/demo iteration;
- not ready for full public paid production launch until readiness blockers in `docs/FRONTEND_READINESS_REPORT.md` are closed.

## 0. Before you start

Requirements on the host:

- Docker Engine with Compose v2;
- outbound HTTPS access from the host/container network for provider APIs;
- free local ports for `${HTTP_PORT:-80}` and `${MINIO_CONSOLE_PORT:-9001}`;
- enough disk space for Postgres and MinIO volumes.

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

Important public callback URLs should point through the gateway `/api` prefix:

```env
BILLING_BASE_URL=https://your-domain.example
KIE_CALLBACK_URL=https://your-domain.example/api/webhooks/kie
```

For a local smoke/demo run, use localhost values:

```env
BILLING_BASE_URL=http://127.0.0.1
KIE_CALLBACK_URL=http://127.0.0.1/api/webhooks/kie
```

Provider/payment values can be filled with non-placeholder dummy values for a UI-only demo, but real generation/payment callbacks require real approved provider credentials.

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

Or use the helper:

```bash
sh deploy/scripts/healthcheck-production.sh
```

If the check fails, inspect service status:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml ps
docker compose --env-file .env.production -f docker-compose.production.yml logs --tail=120 backend nginx web postgres redis minio
```

## 5. Access paths

- User web app: `/`
- Admin web panel: `/admin`
- Core API through gateway: `/api/*`
- API health: `/api/health`
- Kie webhook: `/api/webhooks/kie`
- CrocoPay webhook: `/api/webhooks/payments/crocopay`
- Gateway health: `/healthz`
- MinIO console: `127.0.0.1:${MINIO_CONSOLE_PORT:-9001}` by default.

Local URLs with default ports:

```text
http://127.0.0.1/
http://127.0.0.1/admin
http://127.0.0.1/api/health
http://127.0.0.1:9001
```

## 6. Manual smoke checklist

After bootstrap, check the web product manually:

1. Open `/` and confirm the user app renders.
2. Open `/admin` and confirm the admin panel renders.
3. Use the admin token from `.env.production` only in a private/local browser session.
4. Check `/billing` loads credit packages.
5. Check `/studio` routes to auth/18+ flow if no session exists.
6. Check `/api/health` returns `{"status":"ok"}`.
7. Check MinIO console opens locally and buckets exist.
8. Inspect logs for boot errors.

Commands:

```bash
sh deploy/scripts/healthcheck-production.sh
sh deploy/scripts/tail-production-logs.sh
sh deploy/scripts/tail-production-logs.sh backend
sh deploy/scripts/tail-production-logs.sh nginx
```

## 7. Demo limitations

A local UI/demo run can validate:

- web shell;
- admin shell;
- static frontend build;
- backend API health;
- database boot;
- Redis boot;
- MinIO boot;
- gateway routing;
- migrations;
- bucket setup.

It does not fully validate real production behavior unless the following are configured and exercised:

- Kie provider credentials and callback delivery;
- CrocoPay or other approved payment provider credentials and webhook delivery;
- real S3/MinIO import of generated media;
- adult-content provider/payment/cloud approval;
- real blur/thumbnail processor instead of placeholder derivative copy;
- backup and restore drill.

## 8. Operational rules

- Do not expose `backend`, `postgres`, `redis`, or `minio` ports publicly.
- Keep public ingress through `nginx` only.
- Run `create-buckets` after changing bucket names.
- Run `migrate` before deploying a backend image that changes ORM models or Alembic revisions.
- Keep `ADMIN_API_TOKEN`, `JWT_SECRET`, provider tokens, and payment secrets outside Git.
- Use TLS in front of this stack in real production. This Compose file intentionally binds plain HTTP so it can run behind Caddy, Traefik, Cloudflare Tunnel, an L7 load balancer, or host-level certbot/Nginx.
- For adult content launch, confirm payment/provider/cloud terms in writing before processing real traffic.

## 9. Update existing deployment

Pull latest code, then rebuild and restart:

```bash
git pull origin main
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

For a more controlled update:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml build backend web nginx
docker compose --env-file .env.production -f docker-compose.production.yml --profile migrate run --rm migrate
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend web nginx
sh deploy/scripts/healthcheck-production.sh
```

## 10. Rollback shape

For an image-tagged release:

```bash
ADULTGEN_IMAGE_TAG=previous-tag docker compose --env-file .env.production -f docker-compose.production.yml up -d backend web nginx
```

Database rollbacks are migration-specific. Do not downgrade blindly if a release wrote new data formats.

## 11. Logs

```bash
sh deploy/scripts/tail-production-logs.sh
sh deploy/scripts/tail-production-logs.sh backend
sh deploy/scripts/tail-production-logs.sh nginx
```

## 12. Backup targets

At minimum back up:

- `postgres-data` volume;
- `minio-data` volume;
- `.env.production` secret file stored separately in a secure vault.

Redis is append-only in this Compose pack, but application truth should still live in Postgres and object storage.

Suggested first restore drill before public launch:

1. Stop the stack.
2. Restore Postgres volume from backup.
3. Restore MinIO volume from backup.
4. Restore `.env.production` from secure storage.
5. Start stack.
6. Run healthcheck.
7. Open user app/admin panel and verify media/publication records still resolve.
