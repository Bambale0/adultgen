from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_production_compose_declares_backend_only_service_graph() -> None:
    compose = read("docker-compose.production.yml")

    for service in ("postgres", "redis", "minio", "create-buckets", "migrate", "backend", "nginx"):
        assert f"  {service}:" in compose

    assert "  web:" not in compose
    assert "apps/web_app" not in compose
    assert "condition: service_healthy" in compose
    assert 'profiles: ["setup"]' in compose
    assert 'profiles: ["migrate"]' in compose
    assert "OBJECT_STORAGE_BACKEND: s3" in compose
    assert "S3_ENDPOINT_URL: http://minio:9000" in compose
    assert '127.0.0.1:${MINIO_CONSOLE_PORT:-9001}:9001' in compose
    assert '"${HTTP_PORT:-4444}:80"' in compose
    assert "postgres-data:" in compose
    assert "redis-data:" in compose
    assert "minio-data:" in compose


def test_api_dockerfile_is_production_oriented() -> None:
    dockerfile = read("Dockerfile")

    assert "python:3.12-slim AS builder" in dockerfile
    assert "python:3.12-slim AS runtime" in dockerfile
    assert "useradd --system" in dockerfile
    assert "USER adultgen" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "uvicorn" in dockerfile
    assert "--proxy-headers" in dockerfile


def test_gateway_routes_api_and_rejects_stale_frontend_paths() -> None:
    gateway = read("deploy/nginx/gateway.conf")

    assert "location /api/" in gateway
    assert "proxy_pass http://backend:8000/" in gateway
    assert "client_max_body_size 256m" in gateway
    assert "proxy_set_header X-Forwarded-Proto" in gateway
    assert "location = /healthz" in gateway
    assert "frontend_not_installed" in gateway
    assert "http://web" not in gateway


def test_production_env_template_and_scripts_guard_secrets() -> None:
    env_template = read("deploy/env/production.env.example")
    bootstrap = read("deploy/scripts/bootstrap-production.sh")
    healthcheck = read("deploy/scripts/healthcheck-production.sh")
    logs = read("deploy/scripts/tail-production-logs.sh")

    assert "change-me" in env_template
    assert "replace-me" in env_template
    assert "HTTP_PORT=4444" in env_template
    assert "POSTGRES_PASSWORD" in env_template
    assert "MINIO_ROOT_PASSWORD" in env_template
    assert "JWT_SECRET" in env_template
    assert "ADMIN_API_TOKEN" in env_template
    assert "KIE_CALLBACK_URL=http://127.0.0.1:4444/api/webhooks/kie" in env_template
    assert 'grep -Eiq "change-me|replace-me"' in bootstrap
    assert "--profile setup run --rm create-buckets" in bootstrap
    assert "--profile migrate run --rm migrate" in bootstrap
    assert "up -d backend nginx" in bootstrap
    assert "up -d backend web nginx" not in bootstrap
    assert '. "$ENV_FILE"' in healthcheck
    assert "$BASE_URL/api/health" in healthcheck
    assert "docker-compose.production.yml" in logs


def test_ci_runs_backend_checks_only() -> None:
    ci = read(".github/workflows/ci.yml")

    assert "backend-test:" in ci
    assert "ruff check ." in ci
    assert "pytest" in ci
    assert "web-build:" not in ci
    assert "actions/setup-node" not in ci
    assert "apps/web_app" not in ci


def test_deployment_runbook_documents_backend_only_operation() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "backend-only production baseline" in runbook
    assert "docker compose --env-file .env.production" in runbook
    assert "--profile setup run --rm create-buckets" in runbook
    assert "--profile migrate run --rm migrate" in runbook
    assert "up -d backend nginx" in runbook
    assert "frontend_not_installed" in runbook
    assert "Do not expose `backend`, `postgres`, `redis`, or `minio` publicly." in runbook
    assert "Confirm payment/provider/cloud terms in writing" in runbook
