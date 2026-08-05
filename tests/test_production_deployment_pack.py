from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_production_compose_declares_expected_service_graph() -> None:
    compose = read("compose.production.yml")

    for service in ("postgres", "redis", "minio", "minio-init", "migrate", "api", "web", "edge"):
        assert f"  {service}:" in compose

    assert "condition: service_healthy" in compose
    assert "condition: service_completed_successfully" in compose
    assert "alembic" in compose
    assert "OBJECT_STORAGE_BACKEND: s3" in compose
    assert "S3_ENDPOINT_URL: http://minio:9000" in compose
    assert "127.0.0.1:${MINIO_CONSOLE_PORT:-9001}:9001" in compose
    assert "postgres_data:" in compose
    assert "redis_data:" in compose
    assert "minio_data:" in compose
    assert "internal: true" not in compose


def test_api_and_web_dockerfiles_are_production_oriented() -> None:
    api_dockerfile = read("Dockerfile.api")
    web_dockerfile = read("apps/web_app/Dockerfile")

    assert "python:3.12-slim" in api_dockerfile
    assert "adduser --system" in api_dockerfile
    assert "USER adultgen" in api_dockerfile
    assert "HEALTHCHECK" in api_dockerfile
    assert "uvicorn" in api_dockerfile
    assert "--proxy-headers" in api_dockerfile
    assert "node:24-alpine AS build" in web_dockerfile
    assert "nginx:1.27-alpine AS runtime" in web_dockerfile
    assert "npm run build" in web_dockerfile
    assert "VITE_CORE_API_URL=/api" in web_dockerfile


def test_nginx_configs_route_api_webhooks_media_admin_and_spa() -> None:
    edge = read("deploy/nginx/adultgen.conf")
    web = read("deploy/nginx/web-app.conf")

    assert "location /api/" in edge
    assert "proxy_pass http://adultgen_api/" in edge
    assert "location /webhooks/" in edge
    assert "location /media/" in edge
    assert "location /admin/" in edge
    assert "client_max_body_size 100m" in edge
    assert "proxy_set_header X-Forwarded-Proto" in edge
    assert "try_files $uri $uri/ /index.html" in web
    assert "location /healthz" in web


def test_production_env_template_and_scripts_guard_secrets() -> None:
    env_template = read(".env.production.example")
    bootstrap = read("deploy/scripts/bootstrap-production.sh")
    healthcheck = read("deploy/scripts/healthcheck-production.sh")

    assert "CHANGE_ME" in env_template
    assert "POSTGRES_PASSWORD" in env_template
    assert "MINIO_ROOT_PASSWORD" in env_template
    assert "JWT_SECRET" in env_template
    assert "ADMIN_API_TOKEN" in env_template
    assert "KIE_CALLBACK_URL=https://example.com/webhooks/kie" in env_template
    assert "grep -q \"CHANGE_ME\"" in bootstrap
    assert "docker compose --env-file" in bootstrap
    assert "--exit-code-from migrate" in bootstrap
    assert "$BASE_URL/api/health" in healthcheck


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
    runbook = read("deploy/README.md")

    assert "First deploy" in runbook
    assert "bootstrap-production.sh" in runbook
    assert "healthcheck-production.sh" in runbook
    assert "KIE_CALLBACK_URL" in runbook
    assert "BILLING_BASE_URL" in runbook
    assert "Backup minimum" in runbook
    assert "Do not launch adult billing" in runbook
