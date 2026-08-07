from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_orbital_package_exposes_vitest_gate() -> None:
    package = read("apps/orbital_web/package.json")

    assert '"test": "vitest run"' in package
    assert '"vitest": "^4.1.7"' in package
    assert '"@testing-library/react": "^16.3.2"' in package
    assert '"@testing-library/jest-dom": "^7.0.0"' in package
    assert '"jsdom": "^30.0.1"' in package


def test_ci_runs_frontend_tests_before_build() -> None:
    workflow = read(".github/workflows/ci.yml")

    assert "Test web app" in workflow
    assert "npm run test" in workflow
    assert workflow.index("Test web app") < workflow.index("Build web app")


def test_vitest_config_uses_jsdom_for_react_tests() -> None:
    config = read("apps/orbital_web/vitest.config.ts")

    assert "environment: 'jsdom'" in config
    assert "@vitejs/plugin-react" in config
    assert "src/**/*.test.{ts,tsx}" in config
    assert "setupFiles: ['./src/test/setup.ts']" in config


def test_orbital_shell_has_react_testing_library_coverage() -> None:
    test_file = read("apps/orbital_web/src/App.test.tsx")

    assert "@testing-library/react" in test_file
    assert "describe('Orbital Web shell'" in test_file
    assert "renders safe feed before an operator session exists" in test_file
    assert "opens identity handshake instead of bypassing a protected route" in test_file
    assert "renders route sectors from the product navigation" in test_file
