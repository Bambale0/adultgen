import pytest

from adultgen.domain.enums import GenerationOperation, ModelCode
from adultgen.domain.pricing import PricingError, calculate_generation_price


def test_seedream_text_to_image_has_fixed_price() -> None:
    price = calculate_generation_price(
        ModelCode.SEEDREAM_5_PRO_TEXT_TO_IMAGE,
        GenerationOperation.IMAGE_TEXT_TO_IMAGE,
        {"prompt": "portrait", "aspect_ratio": "9:16"},
    )

    assert price == 20


def test_seedance_first_frame_charges_by_duration() -> None:
    price = calculate_generation_price(
        ModelCode.SEEDANCE_2,
        GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_FRAME,
        {
            "prompt": "slow dolly-in",
            "first_frame_url": "https://cdn.example.com/first.png",
            "duration": 10,
        },
    )

    assert price == 100


def test_seedance_uses_default_duration_when_payload_omits_duration() -> None:
    price = calculate_generation_price(
        ModelCode.SEEDANCE_2,
        GenerationOperation.VIDEO_TEXT_TO_VIDEO,
        {"prompt": "cinematic neon alley"},
    )

    assert price == 120


def test_video_price_rejects_non_integer_duration() -> None:
    with pytest.raises(PricingError, match="duration"):
        calculate_generation_price(
            ModelCode.SEEDANCE_2,
            GenerationOperation.VIDEO_TEXT_TO_VIDEO,
            {"prompt": "cinematic", "duration": "10"},
        )


def test_pricing_rejects_unsupported_operation_for_model() -> None:
    with pytest.raises(PricingError, match="not supported"):
        calculate_generation_price(
            ModelCode.SEEDREAM_5_PRO_TEXT_TO_IMAGE,
            GenerationOperation.VIDEO_TEXT_TO_VIDEO,
            {"prompt": "cinematic"},
        )
