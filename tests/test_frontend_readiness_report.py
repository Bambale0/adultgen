from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_frontend_readiness_report_exists_and_is_honest() -> None:
    report = read("docs/FRONTEND_READINESS_REPORT.md")

    assert "# Frontend Readiness Report" in report
    assert "controlled staging demo" in report
    assert "not yet ready for full public paid production launch" in report
    assert "Frontend is not yet ready for full public paid production launch." in report


def test_frontend_readiness_report_lists_confirmed_ready_areas() -> None:
    report = read("docs/FRONTEND_READINESS_REPORT.md")

    for section in [
        "Quality gates",
        "App entry separation",
        "Routing foundation",
        "Shell component contracts",
        "Product surface currently available in frontend",
    ]:
        assert section in report


def test_frontend_readiness_report_lists_blockers_and_next_order() -> None:
    report = read("docs/FRONTEND_READINESS_REPORT.md")

    for blocker in [
        "legacy `App.tsx` is still too large",
        "no frontend unit/component test runner yet",
        "no E2E browser flow yet",
        "Real blur/thumbnail processing",
        "Adult-category payment/provider approval",
    ]:
        assert blocker in report

    assert "Recommended next PR order" in report
    assert "Replace inline `sidebar/topbar` in `App.tsx`" in report
