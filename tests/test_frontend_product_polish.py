from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_web_styles_use_orbital_tokens() -> None:
    styles = read("apps/orbital_web/src/styles.css")
    assert "--bg: #131313" in styles
    assert "--pink: #ff45a2" in styles
    assert "--cyan: #00f2ff" in styles
    assert "--lime: #a0f11c" in styles
    assert "font-family: 'JetBrains Mono'" in styles


def test_web_styles_keep_orbital_navigation_and_feed() -> None:
    styles = read("apps/orbital_web/src/styles.css")
    assert ".sidebar" in styles
    assert "width: 280px" in styles
    assert ".topbar" in styles
    assert ".scanline-layer" in styles
    assert ".masonry-feed" in styles
    assert ".signal-card" in styles


def test_web_styles_cover_product_surfaces_and_mobile() -> None:
    styles = read("apps/orbital_web/src/styles.css")
    assert ".deploy-grid" in styles
    assert ".telemetry-layout" in styles
    assert ".profile-grid" in styles
    assert ".wallet-hero" in styles
    assert ".package-grid" in styles
    assert "@media (max-width: 820px)" in styles
