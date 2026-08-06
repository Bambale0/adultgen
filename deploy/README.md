# AdultGen production deployment

This deployment pack is the backend-only single-host baseline for AdultGen. Every stateful dependency has a named volume, public ingress goes through one Nginx container, and runtime configuration comes from `.env.production`.

## Topology

```text
Internet
  ↓
nginx :80
  ├─ /healthz → gateway health
  ├─ /api/*   → Core API :8000
  └─ /*        → 404 frontend_not_installed

Core API
  ├─ Postgres
  ├─ Redis
  └─ MinIO/S3-compatible storage
```

## Canonical files

- `docker-compose.production.yml` — production service graph.
- `Dockerfile` — Python/FastAPI API image.
- `deploy/nginx/gateway.conf` — API-only public gateway.
- `deploy/env/production.env.example` — required environment template.
- `deploy/scripts/bootstrap-production.sh` — build, migrate, and start.
- `deploy/scripts/healthcheck-production.sh` — public and container health verification.
- `deploy/scripts/tail-production-logs.sh` — log helper.

The former frontend image and SPA Nginx configuration were removed. See `docs/FRONTEND_RESET.md`.

## First deploy

```bash
cp deploy/env/production.env.example .env.production
chmod 600 .env.production
nano .env.production
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

The bootstrap script refuses to start while `.env.production` contains `change-me` or `replace-me` placeholders.

## Required public URLs

```bash
KIE_CALLBACK_URL=https://your-domain.example/api/webhooks/kie
BILLING_BASE_URL=https://your-domain.example
```

## Updating

```bash
git pull
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

The migration profile runs `alembic upgrade head` before the backend and gateway are started.

## Logs

```bash
sh deploy/scripts/tail-production-logs.sh
sh deploy/scripts/tail-production-logs.sh backend
sh deploy/scripts/tail-production-logs.sh nginx
```

## Backup minimum

Back up:

- `postgres-data` volume;
- `minio-data` volume;
- `.env.production` in a secure secrets vault, not in Git.

## Security notes

- Do not expose Postgres, Redis, MinIO, or the backend container publicly.
- The MinIO console is bound to `127.0.0.1` by default.
- Rotate `JWT_SECRET`, `ADMIN_API_TOKEN`, provider keys, and payment webhook secrets before launch.
- Do not launch adult billing until the payment provider has explicitly approved the category in writing.
- Put TLS termination in front of the gateway using a host reverse proxy, load balancer, or managed ingress.
