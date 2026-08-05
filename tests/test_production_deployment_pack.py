from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_backend_dockerfile_is_production_oriented() -> None:
    dockerfile = read("Dockerfile")

    assert "FROM python:3.12-slim AS builder" in dockerfile
    assert "FROM python:3.12-slim AS runtime" in dockerfile
    assert "useradd --system" in dockerfile
    assert "USER adultgen" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "uvicorn adultgen.apps.core_api:app" in dockerfile
    assert "--proxy-headers" in dockerfile


def test_web_app_dockerfile_serves_static_build_with_nginx() -> None:
    dockerfile = read("apps/web_app/Dockerfile")
    nginx_conf = read("deploy/nginx/web-app.conf")

    assert "FROM node:" in dockerfile
    assert "npm run build" in dockerfile
    assert "FROM nginx:" in dockerfile
    assert "COPY --from=build /app/dist /usr/share/nginx/html" in dockerfile
    assert "try_files $uri $uri/ /index.html" in nginx_conf
    assert "location /healthz" in nginx_conf


def test_compose_stack_keeps_stateful_services_private() -> None:
    compose = read("docker-compose.production.yml")

    assert "postgres:" in compose
    assert "redis:" in compose
    assert "minio:" in compose
    assert "backend:" in compose
    assert "web:" in compose
    assert "nginx:" in compose
    assert "internal: true" in compose
    assert "postgres-data:" in compose
    assert "redis-data:" in compose
    assert "minio-data:" in compose
    assert "condition: service_healthy" in compose
    assert "profiles: [\"setup\"]" in compose
    assert "profiles: [\"migrate\"]" in compose


def test_gateway_routes_api_and_web_separately() -> None:
    gateway = read("deploy/nginx/gateway.conf")

    assert "location /api/" in gateway
    assert "proxy_pass http://backend:8000/" in gateway
    assert "proxy_pass http://web:8080" in gateway
    assert "proxy_set_header X-Forwarded-Proto $scheme" in gateway
    assert "client_max_body_size 256m" in gateway
    assert "location = /healthz" in gateway


def test_production_env_template_covers_required_runtime_settings() -> None:
    env = read("deploy/env/production.env.example")

    assert "DATABASE_URL" not in env
    assert "POSTGRES_PASSWORD=change-me" in env
    assert "MINIO_ROOT_PASSWORD=change-me" in env
    assert "JWT_SECRET=change-me" in env
    assert "ADMIN_API_TOKEN=change-me" in env
    assert "KIE_CALLBACK_URL=https://example.com/api/webhooks/kie" in env
    assert "CROCOPAY_CLIENT_SECRET=" in env


def test_ci_runs_backend_and_web_builds() -> None:
    ci = read(".github/workflows/ci.yml")

    assert "backend-test:" in ci
    assert "ruff check ." in ci
    assert "pytest" in ci
    assert "web-build:" in ci
    assert "actions/setup-node@v4" in ci
    assert "working-directory: apps/web_app" in ci
    assert "npm run build" in ci


def test_production_runbook_documents_real_launch_sequence() -> None:
    docs = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "docker compose --env-file .env.production" in docs
    assert "--profile setup run --rm create-buckets" in docs
    assert "--profile migrate run --rm migrate" in docs
    assert "curl -fsS http://127.0.0.1:${HTTP_PORT:-80}/api/health" in docs
    assert "Do not expose `backend`, `postgres`, `redis`, or `minio` ports publicly." in docs
