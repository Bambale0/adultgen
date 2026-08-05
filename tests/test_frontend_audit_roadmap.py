from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_frontend_audit_documents_current_risks_and_ordered_epics() -> None:
    roadmap = read("docs/FRONTEND_AUDIT_ROADMAP.md")

    assert "AdultGen Frontend Audit and Implementation Roadmap" in roadmap
    assert "god component" in roadmap
    assert "API client layer" in roadmap
    assert "Async UX" in roadmap
    assert "Accessibility" in roadmap
    assert "Frontend quality gates" in roadmap
    assert "Epic FE-01" in roadmap
    assert "Epic FE-02" in roadmap
    assert "Epic FE-10" in roadmap


def test_web_package_exposes_quality_scripts() -> None:
    package_json = read("apps/web_app/package.json")

    assert '"typecheck": "tsc -p tsconfig.json --noEmit"' in package_json
    assert '"lint": "npm run typecheck"' in package_json
    assert '"build": "npm run typecheck && vite build"' in package_json


def test_ci_has_separate_frontend_quality_steps() -> None:
    ci = read(".github/workflows/ci.yml")

    assert "Typecheck web app" in ci
    assert "npm run typecheck" in ci
    assert "Lint web app" in ci
    assert "npm run lint" in ci
    assert "Build web app" in ci
    assert "npm run build" in ci


def test_frontend_roadmap_keeps_admin_and_user_apps_separate() -> None:
    roadmap = read("docs/FRONTEND_AUDIT_ROADMAP.md")
    main = read("apps/web_app/src/main.tsx")

    assert "Admin panel is correctly separated from user app" in roadmap
    assert "window.location.pathname" in main
    assert "AdminPanel" in main
    assert "App" in main
    assert "rootComponent" in main
