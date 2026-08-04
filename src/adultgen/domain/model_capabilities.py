"""Provider model capability registry and payload validation.

This module is intentionally pure domain code. Telegram handlers, Mini App API,
and generation workers should ask this registry what a model operation supports
instead of hardcoding provider assumptions in UI or worker code.
"""

from __future__ import annotations

from dataclasses import dataclass

from adultgen.domain.enums import (
    BillingUnit,
    GenerationOperation,
    KieProviderModel,
    ModelCode,
    ModelProvider,
)


class CapabilityValidationError(ValueError):
    """Raised when a generation payload violates model capability rules."""


@dataclass(frozen=True, slots=True)
class ModelCapability:
    """Static provider capability for one internal model code."""

    provider: ModelProvider
    model_code: ModelCode
    provider_model: KieProviderModel
    operations: frozenset[GenerationOperation]
    billing_unit: BillingUnit
    supports_callback: bool
    supports_polling: bool
    supports_return_last_frame: bool = False
    supports_generate_audio: bool = False
    supports_web_search: bool = False
    duration_values: tuple[int, ...] = ()
    default_duration: int | None = None
    resolution_values: tuple[str, ...] = ()
    default_resolution: str | None = None
    aspect_ratio_values: tuple[str, ...] = ()
    default_aspect_ratio: str | None = None
    required_fields_by_operation: dict[GenerationOperation, frozenset[str]] | None = None
    forbidden_fields_by_operation: dict[GenerationOperation, frozenset[str]] | None = None

    def supports_operation(self, operation: GenerationOperation) -> bool:
        """Return true when the operation is supported by the model."""

        return operation in self.operations

    def validate_payload(self, operation: GenerationOperation, payload: dict[str, object]) -> None:
        """Validate payload shape against operation-specific rules."""

        if not self.supports_operation(operation):
            raise CapabilityValidationError(
                f"Operation {operation.value!r} is not supported by {self.model_code.value!r}."
            )

        required = (self.required_fields_by_operation or {}).get(operation, frozenset())
        missing = sorted(field for field in required if _is_empty(payload.get(field)))
        if missing:
            raise CapabilityValidationError(
                f"Payload for {operation.value!r} is missing required fields: {', '.join(missing)}."
            )

        forbidden = (self.forbidden_fields_by_operation or {}).get(operation, frozenset())
        present_forbidden = sorted(
            field for field in forbidden if not _is_empty(payload.get(field))
        )
        if present_forbidden:
            raise CapabilityValidationError(
                f"Payload for {operation.value!r} contains forbidden fields: "
                f"{', '.join(present_forbidden)}."
            )

        duration = payload.get("duration")
        if self.duration_values and duration is not None and duration not in self.duration_values:
            raise CapabilityValidationError(
                f"Unsupported duration {duration!r}; allowed values: {self.duration_values}."
            )

        resolution = payload.get("resolution")
        if (
            self.resolution_values
            and resolution is not None
            and resolution not in self.resolution_values
        ):
            raise CapabilityValidationError(
                f"Unsupported resolution {resolution!r}; allowed values: {self.resolution_values}."
            )

        aspect_ratio = payload.get("aspect_ratio")
        if (
            self.aspect_ratio_values
            and aspect_ratio is not None
            and aspect_ratio not in self.aspect_ratio_values
        ):
            raise CapabilityValidationError(
                f"Unsupported aspect_ratio {aspect_ratio!r}; "
                f"allowed values: {self.aspect_ratio_values}."
            )


def _is_empty(value: object) -> bool:
    """Return true for absent values and empty lists/strings."""

    if value is None:
        return True
    if isinstance(value, str) and value == "":
        return True
    return isinstance(value, list | tuple | set | dict) and len(value) == 0


SEEDREAM_ASPECT_RATIOS = ("1:1", "4:3", "3:4", "16:9", "9:16")
SEEDANCE_ASPECT_RATIOS = ("16:9", "9:16", "1:1")
SEEDANCE_DURATIONS = (5, 10, 15)
SEEDANCE_RESOLUTIONS = ("480p", "720p", "1080p")

MODEL_CAPABILITIES: dict[ModelCode, ModelCapability] = {
    ModelCode.SEEDREAM_5_PRO_TEXT_TO_IMAGE: ModelCapability(
        provider=ModelProvider.KIE,
        model_code=ModelCode.SEEDREAM_5_PRO_TEXT_TO_IMAGE,
        provider_model=KieProviderModel.SEEDREAM_5_PRO_TEXT_TO_IMAGE,
        operations=frozenset({GenerationOperation.IMAGE_TEXT_TO_IMAGE}),
        billing_unit=BillingUnit.GENERATION,
        supports_callback=True,
        supports_polling=True,
        aspect_ratio_values=SEEDREAM_ASPECT_RATIOS,
        default_aspect_ratio="9:16",
        required_fields_by_operation={
            GenerationOperation.IMAGE_TEXT_TO_IMAGE: frozenset({"prompt"}),
        },
        forbidden_fields_by_operation={
            GenerationOperation.IMAGE_TEXT_TO_IMAGE: frozenset(
                {
                    "image_urls",
                    "first_frame_url",
                    "last_frame_url",
                    "reference_image_urls",
                    "reference_video_urls",
                    "reference_audio_urls",
                }
            ),
        },
    ),
    ModelCode.SEEDREAM_5_PRO_IMAGE_TO_IMAGE: ModelCapability(
        provider=ModelProvider.KIE,
        model_code=ModelCode.SEEDREAM_5_PRO_IMAGE_TO_IMAGE,
        provider_model=KieProviderModel.SEEDREAM_5_PRO_IMAGE_TO_IMAGE,
        operations=frozenset({GenerationOperation.IMAGE_TO_IMAGE}),
        billing_unit=BillingUnit.GENERATION,
        supports_callback=True,
        supports_polling=True,
        aspect_ratio_values=SEEDREAM_ASPECT_RATIOS,
        default_aspect_ratio="9:16",
        required_fields_by_operation={
            GenerationOperation.IMAGE_TO_IMAGE: frozenset({"prompt", "image_urls"}),
        },
        forbidden_fields_by_operation={
            GenerationOperation.IMAGE_TO_IMAGE: frozenset(
                {
                    "first_frame_url",
                    "last_frame_url",
                    "reference_video_urls",
                    "reference_audio_urls",
                }
            ),
        },
    ),
    ModelCode.SEEDANCE_2: ModelCapability(
        provider=ModelProvider.KIE,
        model_code=ModelCode.SEEDANCE_2,
        provider_model=KieProviderModel.SEEDANCE_2,
        operations=frozenset(
            {
                GenerationOperation.VIDEO_TEXT_TO_VIDEO,
                GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_FRAME,
                GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_LAST_FRAMES,
                GenerationOperation.VIDEO_MULTIMODAL_REFERENCE_TO_VIDEO,
            }
        ),
        billing_unit=BillingUnit.SECOND,
        supports_callback=True,
        supports_polling=True,
        supports_return_last_frame=True,
        supports_generate_audio=True,
        supports_web_search=True,
        duration_values=SEEDANCE_DURATIONS,
        default_duration=15,
        resolution_values=SEEDANCE_RESOLUTIONS,
        default_resolution="720p",
        aspect_ratio_values=SEEDANCE_ASPECT_RATIOS,
        default_aspect_ratio="9:16",
        required_fields_by_operation={
            GenerationOperation.VIDEO_TEXT_TO_VIDEO: frozenset({"prompt"}),
            GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_FRAME: frozenset(
                {"prompt", "first_frame_url"}
            ),
            GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_LAST_FRAMES: frozenset(
                {"prompt", "first_frame_url", "last_frame_url"}
            ),
            GenerationOperation.VIDEO_MULTIMODAL_REFERENCE_TO_VIDEO: frozenset({"prompt"}),
        },
        forbidden_fields_by_operation={
            GenerationOperation.VIDEO_TEXT_TO_VIDEO: frozenset(
                {
                    "first_frame_url",
                    "last_frame_url",
                    "reference_image_urls",
                    "reference_video_urls",
                    "reference_audio_urls",
                }
            ),
            GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_FRAME: frozenset(
                {
                    "last_frame_url",
                    "reference_image_urls",
                    "reference_video_urls",
                    "reference_audio_urls",
                }
            ),
            GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_LAST_FRAMES: frozenset(
                {
                    "reference_image_urls",
                    "reference_video_urls",
                    "reference_audio_urls",
                }
            ),
            GenerationOperation.VIDEO_MULTIMODAL_REFERENCE_TO_VIDEO: frozenset(
                {"first_frame_url", "last_frame_url"}
            ),
        },
    ),
}


def get_model_capability(model_code: ModelCode) -> ModelCapability:
    """Return capability config for an internal model code."""

    try:
        return MODEL_CAPABILITIES[model_code]
    except KeyError as exc:
        raise CapabilityValidationError(f"Unknown model code: {model_code.value!r}.") from exc


def validate_generation_payload(
    model_code: ModelCode,
    operation: GenerationOperation,
    payload: dict[str, object],
) -> None:
    """Validate a generation payload for the selected model and operation."""

    get_model_capability(model_code).validate_payload(operation, payload)
