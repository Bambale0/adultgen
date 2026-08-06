from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_agents_md_defines_backend_first_operating_contract() -> None:
    agents = read("AGENTS.md")

    assert "AdultGen agent operating guide" in agents
    assert "backend-first adult AI media platform" in agents
    assert "Required checks before merge" in agents
    assert "ruff check ." in agents
    assert "pytest" in agents
    assert "Definition of done" in agents
    assert "Do not introduce a second wallet balance" in agents
    assert "Do not bypass adult-safety policy checks" in agents
    assert "Do not restore, copy, or selectively resurrect" in agents


def test_agents_md_points_to_reset_and_runbook_docs() -> None:
    agents = read("AGENTS.md")

    assert "docs/PRODUCTION_DEPLOYMENT.md" in agents
    assert "docs/FRONTEND_RESET.md" in agents
    assert "frontend_not_installed" in agents
    assert "FRONTEND_AUDIT_ROADMAP" not in agents
    assert "FRONTEND_READINESS_REPORT" not in agents


def test_production_runbook_has_backend_launch_path() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "AdultGen production deployment runbook" in runbook
    assert "backend-only production baseline" in runbook
    assert "One-command bootstrap" in runbook
    assert "Backend smoke checklist" in runbook
    assert "Production limitations" in runbook
    assert "HTTP_PORT=4444" in runbook
    assert "sh deploy/scripts/bootstrap-production.sh" in runbook
    assert "sh deploy/scripts/healthcheck-production.sh" in runbook
    assert "http://127.0.0.1:${HTTP_PORT:-4444}/api/health" in runbook
    assert "frontend_not_installed" in runbook


def test_production_runbook_keeps_honest_blockers_visible() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "not ready for full public paid production launch" in runbook
    assert "Kie provider credentials and callback delivery" in runbook
    assert "approved payment provider credentials and webhook delivery" in runbook
    assert "real generated-media import and derivative processing" in runbook
    assert "backup and restore procedures" in runbook
