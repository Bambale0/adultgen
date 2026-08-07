# AdultGen production deployment runbook

This single-host baseline runs the AdultGen Studio, Core API and stateful dependencies behind one Nginx gateway.

## Topology

```text
Internet → nginx :${HTTP_PORT:-4444}
  ├─ /api/* → backend:8000
  └─ /*      → studio:8080

backend → Postgres + Redis + MinIO
```

## First launch

```bash
cp deploy/env/production.env.example .env.production
chmod 600 .env.production
# replace every change-me / replace-me value
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

The bootstrap sequence:

1. builds backend and Studio images;
2. starts Postgres, Redis and MinIO;
3. creates private buckets;
4. runs Alembic migrations;
5. starts backend, Studio and gateway.

## Manual commands

```bash
docker compose --env-file .env.production -f docker-compose.production.yml build
docker compose --env-file .env.production -f docker-compose.production.yml up -d postgres redis minio
docker compose --env-file .env.production -f docker-compose.production.yml --profile setup run --rm create-buckets
docker compose --env-file .env.production -f docker-compose.production.yml --profile migrate run --rm migrate
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend studio nginx
```

## Health and URLs

```bash
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/healthz
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/api/health
curl -fsS http://127.0.0.1:${HTTP_PORT:-4444}/ | grep "AdultGen Studio"
```

Routes:

- `/` and `/feed` — Studio feed;
- `/create` — generation composer;
- `/api/health` — Core API health;
- `/healthz` — gateway health;
- MinIO console — `127.0.0.1:${MINIO_CONSOLE_PORT:-9001}`.

## Logs

```bash
sh deploy/scripts/tail-production-logs.sh
sh deploy/scripts/tail-production-logs.sh backend
sh deploy/scripts/tail-production-logs.sh studio
sh deploy/scripts/tail-production-logs.sh nginx
```

## Update

```bash
git pull origin main
sh deploy/scripts/bootstrap-production.sh
sh deploy/scripts/healthcheck-production.sh
```

## Security and readiness

- Expose only Nginx publicly.
- Keep Postgres, Redis, backend and MinIO on private networks.
- Terminate TLS in front of this HTTP baseline.
- Store `.env.production` outside Git and rotate secrets before launch.
- Confirm adult-category approval from provider/payment/cloud vendors in writing.
- Run real Telegram auth, generation callback, payment callback, media delivery and backup/restore drills before paid production traffic.
- The bundled feed data is a non-explicit demo fallback. Real user content must come from Core API and moderation.
