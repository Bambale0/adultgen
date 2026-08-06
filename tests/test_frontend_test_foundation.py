from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_web_package_exposes_vitest_gate() -> None:
    package = read("apps/web_app/package.json")

    assert '"test": "vitest run"' in package
    assert '"vitest": "latest"' in package
    assert '"@testing-library/react": "latest"' in package
    assert '"jsdom": "latest"' in package


def test_ci_runs_frontend_tests_before_build() -> None:
    workflow = read(".github/workflows/ci.yml")

    assert "Test web app" in workflow
    assert "npm run test" in workflow
    assert workflow.index("Test web app") < workflow.index("Build web app")


def test_vitest_config_uses_jsdom_for_react_tests() -> None:
    config = read("apps/web_app/vitest.config.ts")

    assert "environment: 'jsdom'" in config
    assert "@vitejs/plugin-react" in config
    assert "src/**/*.test.{ts,tsx}" in config


def test_app_shell_has_react_testing_library_coverage() -> None:
    test_file = read("apps/web_app/src/components/AppShell.test.tsx")

    assert "@testing-library/react" in test_file
    assert "describe('AppShell'" in test_file
    assert "renders shell regions and children" in test_file
    assert "renders sidebar routes from route metadata" in test_file
    assert "renders topbar status and route selector" in test_file
