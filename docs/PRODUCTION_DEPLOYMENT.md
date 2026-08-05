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

Fill every `change-me-*` / `replace-me-*` value before starting the stack.

Important public callback URLs should point through the gateway `/api` prefix:

```env
BILLING_BASE_URL=https://your-domain.example
KIE_CALLBACK_URL=https://your-domain.example/api/webhooks/kie
```

## 2. Build images

```bash
docker compose --env-file .env.production -f docker-compose.production.yml build
```

## 3. Start infrastructure

```bash
docker compose --env-file .env.production -f docker-compose.production.yml up -d postgres redis minio
```

Wait until all infra services are healthy:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml ps
```

## 4. Create object-storage buckets

```bash
docker compose --env-file .env.production -f docker-compose.production.yml --profile setup run --rm create-buckets
```

This creates the temporary, published, references, and webhook archive buckets and keeps them private.

## 5. Run migrations

```bash
docker compose --env-file .env.production -f docker-compose.production.yml --profile migrate run --rm migrate
```

## 6. Start application tier

```bash
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend web nginx
```

## 7. Verify health

```bash
curl -fsS http://127.0.0.1:${HTTP_PORT:-80}/healthz
curl -fsS http://127.0.0.1:${HTTP_PORT:-80}/api/health
```

Expected responses:

```text
ok
{"status":"ok"}
```

## 8. Access paths

- User web app: `/`
- Admin web panel: `/admin`
- Core API through gateway: `/api/*`
- Kie webhook: `/api/webhooks/kie`
- CrocoPay webhook: `/api/webhooks/payments/crocopay`

## 9. Operational rules

- Do not expose `backend`, `postgres`, `redis`, or `minio` ports publicly.
- Run `create-buckets` after changing bucket names.
- Run `migrate` before deploying a backend image that changes ORM models or Alembic revisions.
- Keep `ADMIN_API_TOKEN`, `JWT_SECRET`, provider tokens, and payment secrets outside Git.
- Use TLS in front of this stack in real production. This Compose file intentionally binds plain HTTP so it can run behind Caddy, Traefik, Cloudflare Tunnel, an L7 load balancer, or host-level certbot/Nginx.
- For adult content launch, confirm payment/provider/cloud terms in writing before processing real traffic.

## 10. Rollback shape

For an image-tagged release:

```bash
ADULTGEN_IMAGE_TAG=previous-tag docker compose --env-file .env.production -f docker-compose.production.yml up -d backend web nginx
```

Database rollbacks are migration-specific. Do not downgrade blindly if a release wrote new data formats.

## 11. Logs

```bash
docker compose --env-file .env.production -f docker-compose.production.yml logs -f nginx backend web
```

## 12. Backup targets

At minimum back up:

- `postgres-data` volume;
- `minio-data` volume;
- `.env.production` secret file stored separately in a secure vault.

Redis is append-only in this Compose pack, but application truth should still live in Postgres and object storage.
