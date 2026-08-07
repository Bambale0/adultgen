from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_TSX = ROOT / "apps" / "orbital_web" / "src" / "App.tsx"
API_TS = ROOT / "apps" / "orbital_web" / "src" / "api.ts"
STYLES_CSS = ROOT / "apps" / "orbital_web" / "src" / "styles.css"


def test_orbital_web_fetches_generation_history() -> None:
    app = APP_TSX.read_text(encoding="utf-8")

    assert "api.generations(session.access_token)" in app
    assert "setTasks(result.items)" in app
    assert "async function refresh()" in app
    assert "api.generations(session.access_token, 50)" in app


def test_orbital_web_renders_generation_results_and_telemetry() -> None:
    app = APP_TSX.read_text(encoding="utf-8")

    assert "function TelemetryScreen(" in app
    assert "function TaskRows(" in app
    assert 'className="result-grid"' in app
    assert 'className="result-asset"' in app
    assert "selected.results.map" in app
    assert "asset.is_external ? 'EXTERNAL' : 'STORED'" in app
    assert "provider_task" in app


def test_orbital_api_has_generation_result_methods() -> None:
    api = API_TS.read_text(encoding="utf-8")

    assert "export type GenerationResult" in api
    assert "export type GenerationTask" in api
    assert "generationById(token: string, id: string)" in api
    assert "generations(token: string, limit = 30)" in api


def test_orbital_result_styles_are_registered() -> None:
    styles = STYLES_CSS.read_text(encoding="utf-8")

    assert ".telemetry-layout" in styles
    assert ".task-row" in styles
    assert ".result-grid" in styles
    assert ".result-asset" in styles
    assert ".status-completed" in styles
