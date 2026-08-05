from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_TSX = ROOT / "apps" / "web_app" / "src" / "App.tsx"
API_TS = ROOT / "apps" / "web_app" / "src" / "api.ts"
STYLES_CSS = ROOT / "apps" / "web_app" / "src" / "styles.css"


def test_web_app_fetches_generation_history_with_effect_cleanup() -> None:
    app = APP_TSX.read_text(encoding="utf-8")

    assert "useEffect" in app
    assert "fetchMyGenerations(session.access_token)" in app
    assert "let ignore = false" in app
    assert "ignore = true" in app
    assert "setGenerationTasks(result.items)" in app


def test_web_app_renders_generation_result_cards_and_actions() -> None:
    app = APP_TSX.read_text(encoding="utf-8")

    assert "GenerationResultsPanel" in app
    assert "GenerationTaskCard" in app
    assert "ResultAssetList" in app
    assert "onImportResultAsset" in app
    assert "onPublishResultAsset" in app
    assert "Импортировать" in app
    assert "Опубликовать" in app
    assert "asset.is_external" in app


def test_web_api_has_generation_result_and_import_methods() -> None:
    api = API_TS.read_text(encoding="utf-8")

    assert "GenerationResultAsset" in api
    assert "GenerationListResponse" in api
    assert "fetchGenerationTask" in api
    assert "fetchMyGenerations" in api
    assert "importExternalMedia" in api
    assert "/media/assets/${assetId}/import-external" in api


def test_web_result_styles_are_registered() -> None:
    styles = STYLES_CSS.read_text(encoding="utf-8")

    assert ".results-panel" in styles
    assert ".generation-grid" in styles
    assert ".generation-card" in styles
    assert ".result-card" in styles
    assert ".result-preview img" in styles
    assert ".task-status.completed" in styles
