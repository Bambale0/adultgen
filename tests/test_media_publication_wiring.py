from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_API = ROOT / "src" / "adultgen" / "apps" / "core_api.py"
MEDIA_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "media.py"
PUBLICATIONS_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "publications.py"
PUBLICATION_SERVICE = ROOT / "src" / "adultgen" / "services" / "publications.py"


def test_core_api_registers_media_publication_routes() -> None:
    content = CORE_API.read_text(encoding="utf-8")

    assert "media," in content
    assert "publications," in content
    assert "app.include_router(media.router)" in content
    assert "app.include_router(publications.router)" in content


def test_media_upload_routes_exist() -> None:
    content = MEDIA_ROUTER.read_text(encoding="utf-8")

    assert '@router.post("/uploads/temporary"' in content
    assert '@router.post("/uploads/references"' in content
    assert "UploadFile" in content
    assert "MAX_UPLOAD_BYTES" in content
    assert "MediaBucketRole.REFERENCES" in content


def test_publication_feed_routes_exist() -> None:
    content = PUBLICATIONS_ROUTER.read_text(encoding="utf-8")
    service_content = PUBLICATION_SERVICE.read_text(encoding="utf-8")

    assert '@router.post("/publications"' in content
    assert '@router.get("/feed"' in content
    assert '@router.get("/profiles/me/publications"' in content
    assert "promote_media_asset_to_published" in service_content
    assert "PublicationVisibility.FEED" in service_content
    assert "PublicationStatus.ACTIVE" in service_content
