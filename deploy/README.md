# AdultGen production deployment

This deployment pack is a single-host production baseline for AdultGen. It is intentionally explicit: every stateful dependency has a named volume, public ingress goes through one edge container, and runtime configuration comes from `.env.production`.

## Topology

```text
Internet
  ↓
edge nginx :80
  ├─ /, /admin → web nginx :8080
  ├─ /api/* → Core API :8000
  ├─ /media/* → Core API :8000
  └─ /webhooks/* → Core API :8000

Core API
  ├─ Postgres
  ├─ Redis
  └─ MinIO/S3-compatible storage
```

## Files

- `compose.production.yml` — production service graph.
- `Dockerfile.api` — Python/FastAPI API image.
- `apps/web_app/Dockerfile` — Vite build + nginx runtime image.
- `deploy/nginx/adultgen.conf` — edge reverse proxy.
- `deploy/nginx/web-app.conf` — SPA runtime config.
- `.env.production.example` — required production environment template.
- `deploy/scripts/bootstrap-production.sh` — build, migrate, and start.
- `deploy/scripts/healthcheck-production.sh` — public and container health verification.
- `deploy/scripts/tail-production-logs.sh` — log helper.

## First deploy

```bash
cp .env.production.example .env.production
nano .env.production
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

The bootstrap script refuses to start while `.env.production` contains `CHANGE_ME` placeholders.

## Required public URLs

Set these to the production public domain:

```bash
KIE_CALLBACK_URL=https://your-domain.example/webhooks/kie
BILLING_BASE_URL=https://your-domain.example
```

The web app is built with `VITE_CORE_API_URL=/api`, so browser requests stay behind the same edge origin.

## Updating

```bash
git pull
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

The `migrate` service runs `alembic upgrade head` before API/web/edge are started.

## Logs

```bash
sh deploy/scripts/tail-production-logs.sh
sh deploy/scripts/tail-production-logs.sh api
sh deploy/scripts/tail-production-logs.sh edge
```

## Backup minimum

At minimum, back up:

- `postgres_data` volume;
- `minio_data` volume;
- `.env.production` in a secure secrets vault, not in Git.

Example logical database backup:

```bash
docker compose --env-file .env.production -f compose.production.yml exec postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > adultgen-$(date +%F).sql
```

For MinIO, use `mc mirror` from an operator machine or a dedicated backup container pointed at the MinIO service.

## Security notes

- Do not expose Postgres or Redis ports publicly.
- The MinIO console is bound to `127.0.0.1` by default.
- Rotate `JWT_SECRET`, `ADMIN_API_TOKEN`, provider keys, and payment webhook secrets before launch.
- Do not launch adult billing until the payment provider has explicitly approved the category in writing.
- Put TLS termination in front of `edge` using a host reverse proxy, load balancer, or a managed ingress.
