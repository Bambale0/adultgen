from pathlib import Path

import pytest

from adultgen.storage.local import LocalObjectStorage

ROOT = Path(__file__).resolve().parents[1]
MEDIA_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "media.py"
PUBLICATION_SCHEMAS = ROOT / "src" / "adultgen" / "api" / "schemas" / "publications.py"
PUBLICATION_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "publications.py"
WEB_API = ROOT / "apps" / "web_app" / "src" / "api.ts"


@pytest.mark.asyncio
async def test_local_object_storage_can_read_back_uploaded_bytes(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path)

    await storage.put_object(bucket="media-published", key="published/example.txt", body=b"hello", content_type="text/plain")
    stored = await storage.get_object(bucket="media-published", key="published/example.txt", content_type="text/plain")

    assert stored.body == b"hello"
    assert stored.content_type == "text/plain"


def test_media_delivery_endpoint_is_registered_with_access_rules() -> None:
    content = MEDIA_ROUTER.read_text(encoding="utf-8")

    assert '@router.get("/assets/{asset_id}/content")' in content
    assert "asset.storage_bucket != settings.s3_published_bucket" in content
    assert "Media asset is private" in content
    assert "Cache-Control" in content


def test_publication_responses_expose_media_preview_urls() -> None:
    schema_content = PUBLICATION_SCHEMAS.read_text(encoding="utf-8")
    router_content = PUBLICATION_ROUTER.read_text(encoding="utf-8")

    assert "media_url: str" in schema_content
    assert "preview_url: str" in schema_content
    assert "blur_preview_url: str | None" in schema_content
    assert "/media/assets/{publication.asset_id}/content" in router_content
    assert "variant=preview" in router_content
    assert "variant=blur" in router_content


def test_web_app_knows_core_media_urls() -> None:
    content = WEB_API.read_text(encoding="utf-8")

    assert "media_url: string" in content
    assert "preview_url: string" in content
    assert "blur_preview_url: string | null" in content
    assert "coreMediaUrl" in content
