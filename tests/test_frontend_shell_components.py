from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_orbital_app_has_explicit_product_shell_regions() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    for component in [
        "function Sidebar(",
        "function Topbar(",
        "function FeedScreen(",
        "function StudioScreen(",
        "function TelemetryScreen(",
        "function ProfileScreen(",
        "function BillingScreen(",
    ]:
        assert component in app
    assert '<aside className="sidebar">' in app
    assert '<header className="topbar">' in app
    assert '<main className="orbital-main">' in app


def test_sidebar_navigation_is_driven_by_route_metadata() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    assert "const routes:" in app
    assert "routes.map((item)" in app
    assert "onNavigate(item.id)" in app
    assert "route === item.id" in app


def test_shared_tactical_primitives_are_reused() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    assert "function PanelHeader(" in app
    assert "function ParamRow(" in app
    assert "function Kpi(" in app
    assert "function Status(" in app
    assert "function TaskRows(" in app


def test_product_brief_records_local_component_system_decision() -> None:
    brief = read("docs/FRONTEND_PRODUCT_BRIEF_V2.md")

    assert "Component system decision" in brief
    assert "No component framework" in brief
    assert "visual primitives are local CSS/React" in brief
    assert "tactical panel" in brief
