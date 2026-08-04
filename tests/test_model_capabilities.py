import pytest

from adultgen.domain.enums import GenerationOperation, ModelCode
from adultgen.domain.model_capabilities import CapabilityValidationError, validate_generation_payload


def test_seedance_first_last_frame_rejects_multimodal_references() -> None:
    payload: dict[str, object] = {
        "prompt": "cinematic scene",
        "first_frame_url": "https://cdn.example.com/first.png",
        "last_frame_url": "https://cdn.example.com/last.png",
        "reference_video_urls": ["https://cdn.example.com/camera.mp4"],
        "duration": 10,
        "resolution": "720p",
        "aspect_ratio": "9:16",
    }

    with pytest.raises(CapabilityValidationError, match="forbidden fields"):
        validate_generation_payload(
            ModelCode.SEEDANCE_2,
            GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_LAST_FRAMES,
            payload,
        )


def test_seedance_multimodal_rejects_strict_first_frame_fields() -> None:
    payload: dict[str, object] = {
        "prompt": "cinematic scene",
        "first_frame_url": "https://cdn.example.com/first.png",
        "reference_image_urls": ["https://cdn.example.com/ref.png"],
        "duration": 10,
        "resolution": "720p",
        "aspect_ratio": "9:16",
    }

    with pytest.raises(CapabilityValidationError, match="forbidden fields"):
        validate_generation_payload(
            ModelCode.SEEDANCE_2,
            GenerationOperation.VIDEO_MULTIMODAL_REFERENCE_TO_VIDEO,
            payload,
        )


def test_seedream_image_to_image_requires_image_urls() -> None:
    payload: dict[str, object] = {
        "prompt": "keep identity, improve light",
        "aspect_ratio": "9:16",
    }

    with pytest.raises(CapabilityValidationError, match="missing required fields"):
        validate_generation_payload(
            ModelCode.SEEDREAM_5_PRO_IMAGE_TO_IMAGE,
            GenerationOperation.IMAGE_TO_IMAGE,
            payload,
        )


def test_seedance_first_frame_valid_payload() -> None:
    payload: dict[str, object] = {
        "prompt": "slow dolly-in, neon light",
        "first_frame_url": "https://cdn.example.com/first.png",
        "duration": 15,
        "resolution": "720p",
        "aspect_ratio": "9:16",
        "return_last_frame": True,
    }

    validate_generation_payload(
        ModelCode.SEEDANCE_2,
        GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_FRAME,
        payload,
    )
