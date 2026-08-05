from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA_MODEL = ROOT / "src" / "adultgen" / "db" / "models" / "media.py"
MEDIA_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "media.py"
PUBLICATION_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "publications.py"
MEDIA_SERVICE = ROOT / "src" / "adultgen" / "services" / "media_derivatives.py"
MODEL_REGISTRY = ROOT / "src" / "adultgen" / "db" / "models" / "__init__.py"


def test_media_derivative_model_is_registered() -> None:
    model_content = MEDIA_MODEL.read_text(encoding="utf-8")
    registry_content = MODEL_REGISTRY.read_text(encoding="utf-8")

    assert "class MediaDerivative" in model_content
    assert "__tablename__ = \"media_derivatives\"" in model_content
    assert "UniqueConstraint(\"source_asset_id\", \"variant\")" in model_content
    assert "MediaDerivative" in registry_content


def test_media_derivative_service_has_preview_and_blur_variants() -> None:
    content = MEDIA_SERVICE.read_text(encoding="utf-8")

    assert "class MediaDerivativeVariant" in content
    assert "PREVIEW = \"preview\"" in content
    assert "BLUR = \"blur\"" in content
    assert "ensure_media_derivative" in content
    assert "copy-placeholder-v1" in content
    assert "derivatives/{variant.value}" in content


def test_media_derivative_api_endpoint_exists() -> None:
    content = MEDIA_ROUTER.read_text(encoding="utf-8")

    assert '@router.post("/assets/{asset_id}/derivatives/{variant}"' in content
    assert "MediaDerivativeResponse" in content
    assert "ensure_media_derivative" in content
    assert "Media asset is not owned by user" in content


def test_publication_response_prefers_derivative_urls_with_fallback() -> None:
    content = PUBLICATION_ROUTER.read_text(encoding="utf-8")

    assert "_publication_derivative_urls" in content
    assert "MediaDerivativeVariant.PREVIEW" in content
    assert "MediaDerivativeVariant.BLUR" in content
    assert "?variant=preview" in content
    assert "?variant=blur" in content
