from pathlib import Path


AUTH_TS = Path("apps/mini_app/src/auth.ts")
TELEGRAM_TS = Path("apps/mini_app/src/telegram.ts")
ENV_EXAMPLE = Path("apps/mini_app/.env.example")


def test_mini_app_auth_calls_backend_init_data_endpoint() -> None:
    content = AUTH_TS.read_text()

    assert "/auth/telegram-mini-app" in content
    assert "init_data" in content
    assert "bot_username" in content
    assert "start_payload" in content


def test_mini_app_reads_telegram_webapp_init_data() -> None:
    content = TELEGRAM_TS.read_text()

    assert "Telegram" in content
    assert "WebApp" in content
    assert "initData" in content
    assert "start_param" in content


def test_mini_app_env_example_documents_backend_and_bot() -> None:
    content = ENV_EXAMPLE.read_text()

    assert "VITE_CORE_API_BASE_URL" in content
    assert "VITE_TELEGRAM_BOT_USERNAME" in content
