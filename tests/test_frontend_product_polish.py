from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_web_styles_use_compact_staging_layout() -> None:
    styles = read("apps/web_app/src/styles.css")

    assert "grid-template-columns: 260px minmax(0, 1fr)" in styles
    assert "width: min(100%, 1480px)" in styles
    assert "padding: 18px" in styles
    assert "height: calc(100vh - 36px)" in styles
    assert "font-size: 34px" in styles
    assert "clamp(32px, 4vw, 48px)" in styles
    assert "min-height: 230px" in styles
    assert "min-height: 160px" in styles


def test_web_styles_do_not_use_old_oversized_hero_shell() -> None:
    styles = read("apps/web_app/src/styles.css")

    assert "grid-template-columns: 320px minmax(0, 1fr)" not in styles
    assert "height: calc(100vh - 48px)" not in styles
    assert "font-size: 52px" not in styles
    assert "clamp(36px, 6vw, 72px)" not in styles
    assert "clamp(28px, 4vw, 46px)" not in styles
    assert "min-height: 320px" not in styles


def test_web_styles_keep_product_navigation_and_result_cards_visible() -> None:
    styles = read("apps/web_app/src/styles.css")

    assert ".route-button.active" in styles
    assert ".topbar" in styles
    assert ".landing-grid" in styles
    assert ".studio-grid" in styles
    assert ".result-card" in styles
    assert ".generation-grid" in styles
