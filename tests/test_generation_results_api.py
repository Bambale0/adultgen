from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATION_SCHEMAS = ROOT / "src" / "adultgen" / "api" / "schemas" / "generations.py"
GENERATION_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "generations.py"
WEB_API = ROOT / "apps" / "web_app" / "src" / "api.ts"


def test_generation_result_schemas_include_media_assets() -> None:
    content = GENERATION_SCHEMAS.read_text(encoding="utf-8")

    assert "class GenerationResultAssetResponse" in content
    assert "media_url: str" in content
    assert "is_external: bool" in content
    assert "class GenerationListResponse" in content
    assert "results: list[GenerationResultAssetResponse]" in content


def test_generation_router_exposes_status_and_recent_list() -> None:
    content = GENERATION_ROUTER.read_text(encoding="utf-8")

    assert '@router.get(""' in content
    assert '@router.get("/{task_id}"' in content
    assert "GenerationTask.user_id == claims.subject" in content
    assert "SceneTake" in content
    assert "GenerationResultAssetResponse" in content


def test_web_app_can_fetch_generation_status_and_results() -> None:
    content = WEB_API.read_text(encoding="utf-8")

    assert "export type GenerationResultAsset" in content
    assert "results: GenerationResultAsset[]" in content
    assert "fetchGenerationTask" in content
    assert "fetchMyGenerations" in content
    assert "importExternalMedia" in content
