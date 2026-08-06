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
    assert "Создай AI-контент за один prompt" in landing
    assert "Сначала показываем продукт и генератор" in landing
    assert "Вход в сайт-приложение" not in landing
    assert "Войти и получить Core token" not in landing


def test_public_generator_landing_keeps_createporn_style_product_priority() -> None:
    landing = read("apps/web_app/src/components/PublicGeneratorLanding.tsx")

    assert "Prompt" in landing
    assert "Text to image" in landing
    assert "Image to video" in landing
    assert "Reference style" in landing
    assert "Cinematic scene" in landing
    assert "Private by default" in landing
    assert "Создать" in landing


def test_public_generator_landing_starts_session_before_private_app() -> None:
    routed_app = read("apps/web_app/src/RoutedUserApp.tsx")

    assert "createWebSession" in routed_app
    assert "saveWebSession(session)" in routed_app
    assert "navigate(resolveRoute('ageGate')" in routed_app
    assert "blockedRouteTitle={activeRoute.id === 'landing' ? null : activeRoute.title}" in routed_app
