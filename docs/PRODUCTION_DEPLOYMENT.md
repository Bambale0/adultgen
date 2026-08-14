# AdultGen production deployment runbook

This runbook is the production-oriented deployment pack for the AdultGen web + API stack.

The rejected frontend remains removed. The new React/Vite frontend is defined by `docs/WEB_PRODUCT_BRIEF.md` and built from `apps/web_app`.

It runs:

- `nginx` public web/API gateway on `${HTTP_PORT:-4444}`;
- `web` static React/Vite application;
- `backend` FastAPI Core API;
- `postgres` durable application database;
- `redis` durable queue/cache state;
- `minio` S3-compatible object storage;
- one-shot `create-buckets` setup task;
- one-shot `migrate` Alembic task.

Current intended status:

- backend/API stack is suitable for controlled staging/demo validation;
- the new frontend is suitable for controlled staging review;
- public paid production launch still requires production-domain auth setup, provider/payment approval, and end-to-end callback validation.

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

Website authentication needs:

```env
GOOGLE_OAUTH_CLIENT_ID=your-web-client.apps.googleusercontent.com
TELEGRAM_LOGIN_BOT_USERNAME=your_bot
TELEGRAM_LOGIN_MAX_AGE_SECONDS=900
```

In Google Cloud, add the production origin to the web client. In BotFather, use `/setdomain` for the Telegram Login Widget. Google Identity Services tokens and Telegram callback hashes are both verified by FastAPI; no provider secret is shipped to the browser.

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

Provider/payment values can be filled with non-placeholder dummy values for a UI/API smoke run. Real generation/payment callbacks require real approved provider credentials.

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

Start web and API tier:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend web nginx
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
- `/` -> AdultGen web app

## 5. Access paths

Current public gateway paths:

- `http://SERVER_IP:4444/healthz`
- `http://SERVER_IP:4444/api/health`
- `http://SERVER_IP:4444/api/*`
- `http://SERVER_IP:4444/` and client-side application routes

MinIO console remains localhost-bound by default:

- `http://127.0.0.1:${MINIO_CONSOLE_PORT:-9001}`

`/admin` opens a locked operational shell. The token remains browser-session local and all protected server calls use Admin API endpoints under `/api/admin/*` with `ADMIN_API_TOKEN`.

## 6. Logs

```bash
sh deploy/scripts/tail-production-logs.sh
```

Or manually:

```bash
docker compose --env-file .env.production -f docker-compose.production.yml logs -f backend web nginx postgres redis minio
```

## 7. Update flow

```bash
git pull origin main
docker compose --env-file .env.production -f docker-compose.production.yml build backend web nginx
docker compose --env-file .env.production -f docker-compose.production.yml --profile migrate run --rm migrate
docker compose --env-file .env.production -f docker-compose.production.yml up -d backend web nginx
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

Do not restore the rejected frontend. The current new implementation must continue through its own PR series, tests, and visible staging review.

## 10. Manual smoke checklist

- Open `http://127.0.0.1:4444/` and verify desktop and mobile navigation.
- Open `http://127.0.0.1:4444/api/health` and verify the backend health response.
- Complete Google and Telegram sign-in on the configured staging domain.
- Accept the recorded 18+ consent gate and submit one safe test generation.
- Verify wallet refresh, media upload, blurred feed preview, and collection save.
- Open `http://127.0.0.1:4444/admin`, unlock with the staging admin token, and confirm audit rows load.

## 11. Demo limitations

AdultGen is not ready for full public paid production launch. The controlled demo still requires:

- Kie provider credentials and callback delivery validated on the deployment domain;
- payment provider credentials and webhook delivery with written adult-category approval;
- a real blur/thumbnail processor rather than the current staging-grade derivative path;
- a completed backup and restore drill;
- end-to-end Google, Telegram, payment, provider, moderation, and media-delivery validation.
