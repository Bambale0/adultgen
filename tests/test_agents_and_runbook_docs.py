from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_agents_md_defines_agent_operating_contract() -> None:
    agents = read("AGENTS.md")

    assert "AdultGen agent operating guide" in agents
    assert "web-first adult AI media platform" in agents
    assert "Required checks before merge" in agents
    assert "ruff check ." in agents
    assert "pytest" in agents
    assert "npm run typecheck" in agents
    assert "npm run build" in agents
    assert "Definition of done" in agents
    assert "Do not introduce a second wallet balance" in agents
    assert "Do not bypass adult-safety policy checks" in agents


def test_agents_md_points_to_active_frontend_and_runbook_docs() -> None:
    agents = read("AGENTS.md")

    assert "docs/PRODUCTION_DEPLOYMENT.md" in agents
    assert "docs/FRONTEND_PRODUCT_BRIEF_V2.md" in agents
    assert "apps/orbital_web" in agents
    assert "controlled staging/demo validation" in agents
    assert "not yet fully production-ready" in agents
    assert "Do not restore or copy the rejected `apps/web_app` implementation" in agents


def test_production_runbook_has_orbital_launch_path() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "AdultGen production deployment runbook" in runbook
    assert "Before you start" in runbook
    assert "One-command bootstrap" in runbook
    assert "Manual launch sequence" in runbook
    assert "HTTP_PORT=4444" in runbook
    assert "sh deploy/scripts/bootstrap-production.sh" in runbook
    assert "sh deploy/scripts/healthcheck-production.sh" in runbook
    assert "http://SERVER_IP:4444/" in runbook
    assert "http://SERVER_IP:4444/studio" in runbook
    assert "http://SERVER_IP:4444/missions" in runbook
    assert "http://SERVER_IP:4444/profile" in runbook
    assert "http://SERVER_IP:4444/billing" in runbook
    assert "http://SERVER_IP:4444/api/*" in runbook


def test_production_runbook_keeps_honest_blockers_visible() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "not yet declared fully production-ready" in runbook
    assert "provider/payment approval" in runbook
    assert "end-to-end callback and media validation" in runbook
    assert "Production readiness still requires visible staging review and green CI" in runbook
