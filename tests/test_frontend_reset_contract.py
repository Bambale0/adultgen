from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_previous_frontend_implementations_are_absent() -> None:
    assert not (ROOT / "apps").exists()
    assert not (ROOT / "deploy/nginx/web-app.conf").exists()
    assert not (ROOT / "deploy/nginx/adultgen.conf").exists()
    assert not (ROOT / "compose.production.yml").exists()


def test_stale_frontend_plans_are_absent() -> None:
    for path in (
        "docs/FRONTEND_AUDIT_ROADMAP.md",
        "docs/FRONTEND_READINESS_REPORT.md",
        "docs/WEB_APP_PIVOT.md",
        "docs/.tmp-product-polish-marker",
    ):
        assert not (ROOT / path).exists()


def test_repository_is_backend_only_until_replacement_is_approved() -> None:
    ci = read(".github/workflows/ci.yml")
    compose = read("docker-compose.production.yml")
    gateway = read("deploy/nginx/gateway.conf")
    decision = read("docs/FRONTEND_RESET.md")

    assert "backend-test:" in ci
    assert "setup-node" not in ci
    assert "web-build:" not in ci
    assert "  web:" not in compose
    assert "apps/web_app" not in compose
    assert "frontend_not_installed" in gateway
    assert "Remove every existing frontend implementation" in decision
    assert "must not be used as a starting point" in decision
