from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_public_generator_landing_replaces_initial_login_wall() -> None:
    landing = read("apps/web_app/src/components/PublicGeneratorLanding.tsx")
    routed_app = read("apps/web_app/src/RoutedUserApp.tsx")

    assert "PublicGeneratorLanding" in routed_app
    assert "shouldRenderPublicLanding" in routed_app
    assert "activeRoute.id === 'landing'" in routed_app
    assert "activeRoute.requiresAuth && !hasSession" in routed_app
    assert "TikTok-style лента AI-превью" in landing
    assert "public-reels-stage" in landing
    assert "public-compose-dock" in landing
    assert "Вход в сайт-приложение" not in landing
    assert "Войти и получить Core token" not in landing


def test_public_generator_landing_uses_reels_feed_product_priority() -> None:
    landing = read("apps/web_app/src/components/PublicGeneratorLanding.tsx")
    styles = read("apps/web_app/src/components/PublicGeneratorLanding.css")

    assert "public-reels-header" in landing
    assert "public-search" in landing
    assert "public-tabs" in landing
    assert "public-reels-scroll" in landing
    assert "public-reel-card" in landing
    assert "public-action-rail" in landing
    assert "feedItems" in landing
    assert "scroll-snap-type: y mandatory" in styles
    assert "scroll-snap-align: start" in styles
    assert "height: 100vh" in styles
    assert "public-gallery" not in landing
    assert "public-category-strip" not in landing
    assert "public-category-link" not in styles
    assert "public-footer" not in landing


def test_public_generator_landing_keeps_create_flow_visible() -> None:
    landing = read("apps/web_app/src/components/PublicGeneratorLanding.tsx")

    assert "Text to image" in landing
    assert "Image to video" in landing
    assert "Reference style" in landing
    assert "Cinematic scene" in landing
    assert "Создать AI-контент" in landing
    assert "Studio" in landing


def test_public_generator_landing_starts_session_before_private_app() -> None:
    routed_app = read("apps/web_app/src/RoutedUserApp.tsx")

    assert "createWebSession" in routed_app
    assert "saveWebSession(session)" in routed_app
    assert "navigate(resolveRoute('ageGate')" in routed_app
    assert "blockedRouteTitle={activeRoute.id === 'landing' ? null : activeRoute.title}" in routed_app
