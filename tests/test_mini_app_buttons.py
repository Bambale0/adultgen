import pytest

from adultgen.telegram_gateway.mini_app_buttons import (
    MiniAppButtonError,
    MiniAppSection,
    build_mini_app_main_menu,
    build_mini_app_url,
)


def test_build_home_mini_app_url() -> None:
    assert build_mini_app_url("https://app.example.com") == "https://app.example.com/"


def test_build_section_mini_app_url_with_existing_root_path() -> None:
    assert (
        build_mini_app_url(
            "https://app.example.com/mini-app/",
            section=MiniAppSection.CREATE,
        )
        == "https://app.example.com/mini-app/create"
    )


def test_build_mini_app_url_preserves_query_and_adds_referral() -> None:
    url = build_mini_app_url(
        "https://app.example.com/?utm=bot",
        section=MiniAppSection.FEED,
        referral_code="partner-42",
    )

    assert url == "https://app.example.com/feed?utm=bot&ref=partner-42"


def test_build_profile_mini_app_url() -> None:
    url = build_mini_app_url(
        "https://app.example.com",
        section=MiniAppSection.PROFILE,
        profile_public_id="a8Pk3mQ",
    )

    assert url == "https://app.example.com/u/a8Pk3mQ"


def test_build_profile_mini_app_url_requires_profile_id() -> None:
    with pytest.raises(MiniAppButtonError, match="profile_public_id"):
        build_mini_app_url("https://app.example.com", section=MiniAppSection.PROFILE)


def test_build_mini_app_url_rejects_non_https_remote_url() -> None:
    with pytest.raises(MiniAppButtonError, match="https"):
        build_mini_app_url("http://app.example.com")


def test_build_mini_app_url_allows_localhost_http() -> None:
    assert build_mini_app_url("http://localhost:5173") == "http://localhost:5173/"


def test_build_main_menu_contains_expected_web_app_buttons() -> None:
    keyboard = build_mini_app_main_menu(
        "https://app.example.com",
        profile_public_id="a8Pk3mQ",
        referral_code="partner-42",
    )

    rows = keyboard.inline_keyboard
    assert rows[0][0].text == "🚀 Открыть приложение"
    assert rows[0][0].web_app is not None
    assert rows[0][0].web_app.url == "https://app.example.com/?ref=partner-42"

    assert rows[1][0].text == "🎬 Создать"
    assert rows[1][0].web_app is not None
    assert rows[1][0].web_app.url == "https://app.example.com/create?ref=partner-42"

    assert rows[1][1].text == "🔥 Лента"
    assert rows[1][1].web_app is not None
    assert rows[1][1].web_app.url == "https://app.example.com/feed?ref=partner-42"

    assert rows[2][0].text == "📁 Проекты"
    assert rows[2][0].web_app is not None
    assert rows[2][0].web_app.url == "https://app.example.com/projects?ref=partner-42"

    assert rows[3][0].text == "👤 Профиль автора"
    assert rows[3][0].web_app is not None
    assert rows[3][0].web_app.url == "https://app.example.com/u/a8Pk3mQ?ref=partner-42"
