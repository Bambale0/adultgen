import pytest

from adultgen.domain.enums import GenerationOperation, ModelCode
from adultgen.domain.kie_payloads import KiePayloadError, build_kie_create_task_payload
from adultgen.domain.model_capabilities import CapabilityValidationError


def test_kie_payload_wraps_model_callback_and_input() -> None:
    payload = build_kie_create_task_payload(
        model_code=ModelCode.SEEDANCE_2,
        operation=GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_FRAME,
        request_payload={
            "prompt": "slow dolly-in",
            "first_frame_url": "https://cdn.example.com/first.png",
            "duration": 10,
            "resolution": "720p",
            "aspect_ratio": "9:16",
            "reference_video_urls": [],
            "reference_audio_urls": None,
        },
        callback_url="https://api.example.com/webhooks/kie",
    )

    assert payload == {
        "model": "bytedance/seedance-2",
        "callBackUrl": "https://api.example.com/webhooks/kie",
        "input": {
            "prompt": "slow dolly-in",
            "first_frame_url": "https://cdn.example.com/first.png",
            "duration": 10,
            "resolution": "720p",
            "aspect_ratio": "9:16",
        },
    }


def test_kie_payload_requires_callback_url() -> None:
    with pytest.raises(KiePayloadError, match="callback_url"):
        build_kie_create_task_payload(
            model_code=ModelCode.SEEDANCE_2,
            operation=GenerationOperation.VIDEO_TEXT_TO_VIDEO,
            request_payload={"prompt": "cinematic"},
            callback_url="",
        )


def test_kie_payload_keeps_model_capability_validation() -> None:
    with pytest.raises(CapabilityValidationError, match="forbidden fields"):
        build_kie_create_task_payload(
            model_code=ModelCode.SEEDANCE_2,
            operation=GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_LAST_FRAMES,
            request_payload={
                "prompt": "cinematic",
                "first_frame_url": "https://cdn.example.com/first.png",
                "last_frame_url": "https://cdn.example.com/last.png",
                "reference_image_urls": ["https://cdn.example.com/ref.png"],
            },
            callback_url="https://api.example.com/webhooks/kie",
        )
