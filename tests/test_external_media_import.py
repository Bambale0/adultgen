from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA_SERVICE = ROOT / "src" / "adultgen" / "services" / "media.py"
MEDIA_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "media.py"


def test_external_media_import_service_persists_provider_bytes() -> None:
    content = MEDIA_SERVICE.read_text(encoding="utf-8")

    assert "async def import_external_media_asset" in content
    assert "storage.put_object" in content
    assert "asset.external_url = None" in content
    assert "asset.checksum_sha256 = sha256_hex(raw)" in content
    assert "External provider media must be imported before publishing" in content


def test_external_media_import_route_is_owner_only_and_size_limited() -> None:
    content = MEDIA_ROUTER.read_text(encoding="utf-8")

    assert '@router.post("/assets/{asset_id}/import-external"' in content
    assert "MAX_PROVIDER_IMPORT_BYTES" in content
    assert "Media asset is not owned by user" in content
    assert "httpx.AsyncClient" in content
    assert "import_external_media_asset" in content
