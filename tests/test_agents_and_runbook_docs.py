from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_agents_md_defines_current_full_stack_contract() -> None:
    agents = read("AGENTS.md")

    assert "AdultGen agent operating guide" in agents
    assert "apps/studio_app" in agents
    assert "Do not restore or copy code" in agents
    assert "append-only backend wallet ledger" in agents
    assert "Backend adult-safety policy remains authoritative" in agents
    assert "ruff check ." in agents
    assert "pytest" in agents
    assert "npm run verify" in agents


def test_frontend_rebuild_document_has_product_and_safety_contracts() -> None:
    rebuild = read("docs/FRONTEND_REBUILD.md")

    assert "Product surface" in rebuild
    assert "Technical decision" in rebuild
    assert "Safety UX" in rebuild
    assert "API boundary" in rebuild
    assert "Verification plan" in rebuild
    assert "GET /api/adult-consent" in rebuild
    assert "POST /api/generations" in rebuild


def test_production_runbook_documents_full_stack_launch() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "AdultGen production deployment runbook" in runbook
    assert "studio:8080" in runbook
    assert "sh deploy/scripts/bootstrap-production.sh" in runbook
    assert "sh deploy/scripts/healthcheck-production.sh" in runbook
    assert "http://127.0.0.1:${HTTP_PORT:-4444}/api/health" in runbook
    assert "backend studio nginx" in runbook


def test_production_runbook_keeps_real_readiness_blockers_visible() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "adult-category approval" in runbook
    assert "Telegram auth" in runbook
    assert "generation callback" in runbook
    assert "payment callback" in runbook
    assert "backup/restore" in runbook
