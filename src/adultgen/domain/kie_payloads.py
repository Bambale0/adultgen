"""Kie provider payload builder."""

from __future__ import annotations

from adultgen.domain.enums import GenerationOperation, ModelCode
from adultgen.domain.model_capabilities import get_model_capability, validate_generation_payload


class KiePayloadError(ValueError):
    """Raised when a Kie payload cannot be built safely."""


KieCreateTaskPayload = dict[str, object]


def build_kie_create_task_payload(
    *,
    model_code: ModelCode,
    operation: GenerationOperation,
    request_payload: dict[str, object],
    callback_url: str,
) -> KieCreateTaskPayload:
    """Build a Kie /api/v1/jobs/createTask payload from AdultGen task data."""

    if not callback_url:
        raise KiePayloadError("Kie callback_url must be configured before provider submission.")

    validate_generation_payload(model_code, operation, request_payload)
    capability = get_model_capability(model_code)

    cleaned_input = _drop_empty_values(request_payload)
    return {
        "model": capability.provider_model.value,
        "callBackUrl": callback_url,
        "input": cleaned_input,
    }


def _drop_empty_values(payload: dict[str, object]) -> dict[str, object]:
    """Remove None and empty collection values before provider submission."""

    return {key: value for key, value in payload.items() if not _is_empty(value)}


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value == ""
    if isinstance(value, list | tuple | set | dict):
        return len(value) == 0
    return False
