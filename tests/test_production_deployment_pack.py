from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_production_compose_declares_full_service_graph() -> None:
    compose = read("docker-compose.production.yml")

    for service in ("postgres", "redis", "minio", "create-buckets", "migrate", "backend", "studio", "nginx"):
        assert f"  {service}:" in compose

    assert "context: ./apps/studio_app" in compose
    assert "image: adultgen-studio" in compose
    assert "condition: service_healthy" in compose
    assert "profiles: [\"setup\"]" in compose
    assert "profiles: [\"migrate\"]" in compose
    assert "OBJECT_STORAGE_BACKEND: s3" in compose
    assert '"${HTTP_PORT:-4444}:80"' in compose
    assert "postgres-data:" in compose
    assert "redis-data:" in compose
    assert "minio-data:" in compose


def test_studio_package_is_new_dependency_free_implementation() -> None:
    package = read("apps/studio_app/package.json")
    dockerfile = read("apps/studio_app/Dockerfile")
    app = read("apps/studio_app/src/app.js")
    core = read("apps/studio_app/src/core.js")

    assert '"dependencies"' not in package
    assert '"build": "node scripts/build.mjs"' in package
    assert '"test": "node --test tests/*.test.mjs"' in package
    assert "node:22-alpine AS build" in dockerfile
    assert "nginx:1.27-alpine AS runtime" in dockerfile
    assert "adultgen.age-confirmed" in app
    assert "/adult-consent/accept" in read("apps/studio_app/src/api.js")
    assert "seedance-2.0" in core
    assert "seedream-5-pro-text-to-image" in core


def test_gateway_routes_api_and_studio() -> None:
    gateway = read("deploy/nginx/gateway.conf")

    assert "location /api/" in gateway
    assert "proxy_pass http://backend:8000/" in gateway
    assert "proxy_pass http://studio:8080" in gateway
    assert "client_max_body_size 256m" in gateway
    assert "location = /healthz" in gateway


def test_production_scripts_start_and_verify_studio() -> None:
    bootstrap = read("deploy/scripts/bootstrap-production.sh")
    healthcheck = read("deploy/scripts/healthcheck-production.sh")

    assert "up -d backend studio nginx" in bootstrap
    assert "$BASE_URL/api/health" in healthcheck
    assert 'grep -q "AdultGen Studio"' in healthcheck


def test_ci_runs_backend_and_studio_gates() -> None:
    ci = read(".github/workflows/ci.yml")

    assert "backend-test:" in ci
    assert "ruff check ." in ci
    assert "pytest" in ci
    assert "studio-app:" in ci
    assert "actions/setup-node@v4" in ci
    assert "working-directory: apps/studio_app" in ci
    assert "npm run verify" in ci


def test_frontend_rebuild_contract_is_documented() -> None:
    rebuild = read("docs/FRONTEND_REBUILD.md")
    agents = read("AGENTS.md")

    assert "first production-oriented frontend foundation" in rebuild
    assert "Product surface" in rebuild
    assert "Safety UX" in rebuild
    assert "Verification plan" in rebuild
    assert "apps/studio_app" in agents
    assert "Do not restore or copy code" in agents
