"""Generation pricing rules.

Pricing is deliberately pure domain code first. Later it can be backed by a
versioned database table, but generation creation should already depend on one
consistent calculator instead of scattering price math across handlers.
"""

from __future__ import annotations

from dataclasses import dataclass

from adultgen.domain.enums import BillingUnit, GenerationOperation, ModelCode
from adultgen.domain.model_capabilities import get_model_capability


class PricingError(ValueError):
    """Raised when generation price cannot be calculated safely."""


@dataclass(frozen=True, slots=True)
class PricingRule:
    """One static MVP pricing rule for a model operation."""

    model_code: ModelCode
    operation: GenerationOperation
    billing_unit: BillingUnit
    price_per_unit: int


# MVP defaults. Move to ModelPricing table before production launch.
DEFAULT_PRICING_RULES: dict[tuple[ModelCode, GenerationOperation], PricingRule] = {
    (ModelCode.SEEDREAM_5_PRO_TEXT_TO_IMAGE, GenerationOperation.IMAGE_TEXT_TO_IMAGE): PricingRule(
        model_code=ModelCode.SEEDREAM_5_PRO_TEXT_TO_IMAGE,
        operation=GenerationOperation.IMAGE_TEXT_TO_IMAGE,
        billing_unit=BillingUnit.GENERATION,
        price_per_unit=20,
    ),
    (ModelCode.SEEDREAM_5_PRO_IMAGE_TO_IMAGE, GenerationOperation.IMAGE_TO_IMAGE): PricingRule(
        model_code=ModelCode.SEEDREAM_5_PRO_IMAGE_TO_IMAGE,
        operation=GenerationOperation.IMAGE_TO_IMAGE,
        billing_unit=BillingUnit.GENERATION,
        price_per_unit=25,
    ),
    (ModelCode.SEEDANCE_2, GenerationOperation.VIDEO_TEXT_TO_VIDEO): PricingRule(
        model_code=ModelCode.SEEDANCE_2,
        operation=GenerationOperation.VIDEO_TEXT_TO_VIDEO,
        billing_unit=BillingUnit.SECOND,
        price_per_unit=8,
    ),
    (ModelCode.SEEDANCE_2, GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_FRAME): PricingRule(
        model_code=ModelCode.SEEDANCE_2,
        operation=GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_FRAME,
        billing_unit=BillingUnit.SECOND,
        price_per_unit=10,
    ),
    (ModelCode.SEEDANCE_2, GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_LAST_FRAMES): PricingRule(
        model_code=ModelCode.SEEDANCE_2,
        operation=GenerationOperation.VIDEO_IMAGE_TO_VIDEO_FIRST_LAST_FRAMES,
        billing_unit=BillingUnit.SECOND,
        price_per_unit=12,
    ),
    (ModelCode.SEEDANCE_2, GenerationOperation.VIDEO_MULTIMODAL_REFERENCE_TO_VIDEO): PricingRule(
        model_code=ModelCode.SEEDANCE_2,
        operation=GenerationOperation.VIDEO_MULTIMODAL_REFERENCE_TO_VIDEO,
        billing_unit=BillingUnit.SECOND,
        price_per_unit=14,
    ),
}


def calculate_generation_price(
    model_code: ModelCode,
    operation: GenerationOperation,
    payload: dict[str, object],
) -> int:
    """Return credits required for a generation request."""

    capability = get_model_capability(model_code)
    if not capability.supports_operation(operation):
        raise PricingError(f"Operation {operation.value!r} is not supported by {model_code.value!r}.")

    rule = DEFAULT_PRICING_RULES.get((model_code, operation))
    if rule is None:
        raise PricingError(f"No pricing rule configured for {model_code.value!r}/{operation.value!r}.")

    if rule.billing_unit == BillingUnit.GENERATION:
        return rule.price_per_unit

    if rule.billing_unit == BillingUnit.SECOND:
        duration = payload.get("duration", capability.default_duration)
        if not isinstance(duration, int):
            raise PricingError("Video duration must be an integer number of seconds.")
        if duration <= 0:
            raise PricingError("Video duration must be positive.")
        return duration * rule.price_per_unit

    raise PricingError(f"Unsupported billing unit: {rule.billing_unit.value!r}.")
