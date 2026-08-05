from pathlib import Path

from adultgen.services.kie_callbacks import parse_kie_callback

ROOT = Path(__file__).resolve().parents[1]
CORE_API = ROOT / "src" / "adultgen" / "apps" / "core_api.py"
GENERATIONS_MODEL = ROOT / "src" / "adultgen" / "db" / "models" / "generations.py"
MEDIA_MODEL = ROOT / "src" / "adultgen" / "db" / "models" / "media.py"
MEDIA_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "media.py"
WEBHOOK_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "webhooks.py"
ENV_EXAMPLE = ROOT / ".env.example"


def test_kie_callback_parser_accepts_seedance_style_completed_payload() -> None:
    parsed = parse_kie_callback(
        {
            "id": "task_bytedance_123",
            "status": "completed",
            "data": {
                "results": ["https://cdn.example.com/result.mp4"],
                "last_frame_url": "https://cdn.example.com/last.png",
            },
        }
    )

    assert parsed.provider_task_id == "task_bytedance_123"
    assert parsed.status == "completed"
    assert parsed.result_urls == ("https://cdn.example.com/result.mp4",)
    assert parsed.last_frame_url == "https://cdn.example.com/last.png"


def test_kie_callback_parser_accepts_kie_task_id_shape() -> None:
    parsed = parse_kie_callback(
        {
            "taskId": "task_kie_456",
            "data": {"video_url": "https://cdn.example.com/video.mp4"},
        }
    )

    assert parsed.provider_task_id == "task_kie_456"
    assert parsed.status == "completed"
    assert parsed.result_urls == ("https://cdn.example.com/video.mp4",)


def test_kie_webhook_router_is_registered() -> None:
    core_api = CORE_API.read_text(encoding="utf-8")
    router_content = WEBHOOK_ROUTER.read_text(encoding="utf-8")
    env_content = ENV_EXAMPLE.read_text(encoding="utf-8")

    assert "webhooks" in core_api
    assert 'app.include_router(webhooks.router)' in core_api
    assert '@router.post("/kie"' in router_content
    assert "KIE_WEBHOOK_SECRET" in env_content


def test_generation_callback_raw_model_is_registered() -> None:
    model_content = GENERATIONS_MODEL.read_text(encoding="utf-8")

    assert "class GenerationProviderCallbackRaw" in model_content
    assert "generation_provider_callbacks_raw" in model_content
    assert "raw_payload" in model_content
    assert "result_payload" in model_content


def test_media_assets_support_external_provider_urls() -> None:
    model_content = MEDIA_MODEL.read_text(encoding="utf-8")
    router_content = MEDIA_ROUTER.read_text(encoding="utf-8")

    assert "external_url" in model_content
    assert "RedirectResponse" in router_content
    assert "asset.external_url" in router_content
