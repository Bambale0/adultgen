from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_app_shell_components_are_extracted_from_legacy_app_shape() -> None:
    shell = read("apps/web_app/src/components/AppShell.tsx")

    assert "export function AppShell" in shell
    assert "export function Sidebar" in shell
    assert "export function TopBar" in shell
    assert "className=\"web-shell\"" in shell
    assert "className=\"sidebar\"" in shell
    assert "className=\"topbar\"" in shell
    assert "aria-label=\"Основная навигация сайта\"" in shell
    assert "aria-label=\"Route selector\"" in shell
    assert "aria-live=\"polite\"" in shell


def test_shell_components_depend_on_route_metadata_not_magic_labels() -> None:
    shell = read("apps/web_app/src/components/AppShell.tsx")

    assert "type SidebarRoute = Pick<WebAppRoute, 'id' | 'title'>" in shell
    assert "activeRoute.id" in shell
    assert "routeResolver" in shell
    assert "routes.map" in shell
    assert "onNavigate" in shell


def test_routed_user_app_has_shell_migration_boundary() -> None:
    routed = read("apps/web_app/src/RoutedUserApp.tsx")

    assert "import { AppShell, Sidebar, TopBar } from './components/AppShell';" in routed
    assert "type ShellExtractionStage" in routed
    assert "getShellExtractionStage" in routed
    assert "ShellContractHarness" in routed
    assert "primaryWebAppRoutes" in routed
    assert "webAppRoutes" in routed
    assert "<App key={activeRoute.path} />" in routed


def test_frontend_roadmap_requires_app_shell_sidebar_topbar_extraction() -> None:
    roadmap = read("docs/FRONTEND_AUDIT_ROADMAP.md")

    assert "`AppShell`/`Sidebar`/`TopBar` extraction" in roadmap
    assert "Move feature UI into `features/*` modules" in roadmap
    assert "Move shared UI primitives into `components/*`" in roadmap
