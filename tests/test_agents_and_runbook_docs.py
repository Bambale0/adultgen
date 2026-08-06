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
    assert "Definition of done" in agents
    assert "Do not introduce a second wallet balance" in agents
    assert "Do not bypass adult-safety policy checks" in agents


def test_agents_md_points_to_readiness_and_runbook_docs() -> None:
    agents = read("AGENTS.md")

    assert "docs/PRODUCTION_DEPLOYMENT.md" in agents
    assert "docs/FRONTEND_AUDIT_ROADMAP.md" in agents
    assert "docs/FRONTEND_READINESS_REPORT.md" in agents
    assert "ready for controlled staging/demo iteration" in agents
    assert "not ready for full public paid production launch" in agents


def test_production_runbook_has_demo_launch_path() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "AdultGen production deployment runbook" in runbook
    assert "Before you start" in runbook
    assert "Ubuntu server" in runbook
    assert "One-command bootstrap" in runbook
    assert "Manual smoke checklist" in runbook
    assert "Demo limitations" in runbook
    assert "HTTP_PORT=4444" in runbook
    assert "sh deploy/scripts/bootstrap-production.sh" in runbook
    assert "sh deploy/scripts/healthcheck-production.sh" in runbook
    assert "http://127.0.0.1:4444/admin" in runbook
    assert "http://127.0.0.1:4444/api/health" in runbook


def test_production_runbook_keeps_honest_blockers_visible() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "not ready for full public paid production launch" in runbook
    assert "Kie provider credentials and callback delivery" in runbook
    assert "payment provider credentials and webhook delivery" in runbook
    assert "real blur/thumbnail processor" in runbook
    assert "backup and restore drill" in runbook
