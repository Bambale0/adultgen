from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_production_compose_declares_expected_service_graph() -> None:
    compose = read("docker-compose.production.yml")

    for service in ("postgres", "redis", "minio", "create-buckets", "migrate", "backend", "web", "nginx"):
        assert f"  {service}:" in compose

    assert "condition: service_healthy" in compose
    assert "profiles: [\"setup\"]" in compose
    assert "profiles: [\"migrate\"]" in compose
    assert "alembic" in compose
    assert "OBJECT_STORAGE_BACKEND: s3" in compose
    assert "S3_ENDPOINT_URL: http://minio:9000" in compose
    assert "127.0.0.1:${MINIO_CONSOLE_PORT:-9001}:9001" in compose
    assert "postgres-data:" in compose
    assert "redis-data:" in compose
    assert "minio-data:" in compose
    assert "internal: true" not in compose


def test_api_and_web_dockerfiles_are_production_oriented() -> None:
    api_dockerfile = read("Dockerfile")
    web_dockerfile = read("apps/web_app/Dockerfile")

    assert "python:3.12-slim AS builder" in api_dockerfile
    assert "python:3.12-slim AS runtime" in api_dockerfile
    assert "useradd --system" in api_dockerfile
    assert "USER adultgen" in api_dockerfile
    assert "HEALTHCHECK" in api_dockerfile
    assert "uvicorn" in api_dockerfile
    assert "--proxy-headers" in api_dockerfile
    assert "node:24-alpine AS build" in web_dockerfile
    assert "nginx:1.27-alpine AS runtime" in web_dockerfile
    assert "npm run build" in web_dockerfile
    assert "VITE_CORE_API_URL=/api" in web_dockerfile


def test_nginx_configs_route_api_and_spa() -> None:
    gateway = read("deploy/nginx/gateway.conf")
    web = read("deploy/nginx/web-app.conf")

    assert "location /api/" in gateway
    assert "proxy_pass http://backend:8000/" in gateway
    assert "proxy_pass http://web:8080" in gateway
    assert "client_max_body_size 256m" in gateway
    assert "proxy_set_header X-Forwarded-Proto" in gateway
    assert "location = /healthz" in gateway
    assert "try_files $uri $uri/ /index.html" in web
    assert "location /healthz" in web


def test_production_env_template_and_scripts_guard_secrets() -> None:
    env_template = read("deploy/env/production.env.example")
    bootstrap = read("deploy/scripts/bootstrap-production.sh")
    healthcheck = read("deploy/scripts/healthcheck-production.sh")
    logs = read("deploy/scripts/tail-production-logs.sh")

    assert "change-me" in env_template
    assert "replace-me" in env_template
    assert "POSTGRES_PASSWORD" in env_template
    assert "MINIO_ROOT_PASSWORD" in env_template
    assert "JWT_SECRET" in env_template
    assert "ADMIN_API_TOKEN" in env_template
    assert "KIE_CALLBACK_URL=https://example.com/api/webhooks/kie" in env_template
    assert "grep -Eiq \"change-me|replace-me\"" in bootstrap
    assert "docker compose --env-file" in bootstrap
    assert "--profile setup run --rm create-buckets" in bootstrap
    assert "--profile migrate run --rm migrate" in bootstrap
    assert "$BASE_URL/api/health" in healthcheck
    assert "docker-compose.production.yml" in logs


def test_ci_runs_backend_and_web_builds() -> None:
    ci = read(".github/workflows/ci.yml")

    assert "backend-test:" in ci
    assert "ruff check ." in ci
    assert "pytest" in ci
    assert "web-build:" in ci
    assert "actions/setup-node@v4" in ci
    assert "working-directory: apps/web_app" in ci
    assert "npm run build" in ci


def test_deployment_runbook_documents_operational_flows() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "docker compose --env-file .env.production" in runbook
    assert "--profile setup run --rm create-buckets" in runbook
    assert "--profile migrate run --rm migrate" in runbook
    assert "curl -fsS http://127.0.0.1:${HTTP_PORT:-80}/api/health" in runbook
    assert "Do not expose `backend`, `postgres`, `redis`, or `minio` ports publicly." in runbook
    assert "For adult content launch" in runbook
