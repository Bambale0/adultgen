"""Adult content policy evaluation rules.

The first version is intentionally deterministic and conservative. It is not a
replacement for a ML classifier or human review, but it gives the product a
single policy boundary for generation and publication flows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AdultPolicyAction(StrEnum):
    """Policy decision for a request."""

    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


class AdultPolicyFlag(StrEnum):
    """Normalized adult-policy flags."""

    MINOR_OR_UNDERAGE = "minor_or_underage"
    NCII_OR_REAL_PERSON = "ncii_or_real_person"
    PUBLIC_FIGURE = "public_figure"
    COERCION_OR_VIOLENCE = "coercion_or_violence"
    HIDDEN_CAMERA = "hidden_camera"
    INCEST = "incest"
    BESTIALITY = "bestiality"
    TRAFFICKING_OR_EXPLOITATION = "trafficking_or_exploitation"
    PUBLISHED_EXPLICIT = "published_explicit"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


@dataclass(frozen=True, slots=True)
class AdultPolicyDecision:
    """Decision returned by the adult policy engine."""

    action: AdultPolicyAction
    flags: tuple[AdultPolicyFlag, ...] = ()
    reasons: tuple[str, ...] = ()
    public_allowed: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        """Return whether this decision blocks the request."""

        return self.action == AdultPolicyAction.BLOCK

    @property
    def needs_review(self) -> bool:
        """Return whether this decision should create a human-review case."""

        return self.action == AdultPolicyAction.REVIEW or AdultPolicyFlag.NEEDS_HUMAN_REVIEW in self.flags


@dataclass(frozen=True, slots=True)
class AdultPolicyInput:
    """Normalized inputs for policy evaluation."""

    text: str
    surface: str
    is_public: bool = False
    has_real_person_reference: bool = False
    has_identity_consent: bool = False


ABSOLUTE_BLOCK_PATTERNS: tuple[tuple[AdultPolicyFlag, tuple[str, ...], str], ...] = (
    (
        AdultPolicyFlag.MINOR_OR_UNDERAGE,
        (
            "minor",
            "underage",
            "child",
            "kid",
            "schoolgirl",
            "schoolboy",
            "teen",
            "teenager",
            "young-looking",
            "barely legal",
            "loli",
            "shota",
            "несовершеннолет",
            "малолет",
            "ребен",
            "ребён",
            "школьниц",
            "школьник",
            "подрост",
        ),
        "Minor/underage sexual content is absolutely blocked.",
    ),
    (
        AdultPolicyFlag.COERCION_OR_VIOLENCE,
        (
            "rape",
            "forced",
            "coerced",
            "unconscious",
            "drugged",
            "sleeping without consent",
            "violent sex",
            "sexual violence",
            "изнасил",
            "насильн",
            "без сознания",
            "принуд",
            "насили",
        ),
        "Sexual coercion, rape, or violence is blocked.",
    ),
    (
        AdultPolicyFlag.HIDDEN_CAMERA,
        (
            "hidden camera",
            "spy cam",
            "secretly filmed",
            "偷拍",
            "скрытая камера",
            "тайная съемка",
            "тайная съёмка",
            "подглядыв",
        ),
        "Hidden-camera or voyeuristic sexual content is blocked.",
    ),
    (
        AdultPolicyFlag.INCEST,
        (
            "incest",
            "mother and son",
            "father and daughter",
            "brother and sister",
            "sister and brother",
            "инцест",
            "мать и сын",
            "отец и дочь",
            "брат и сестра",
        ),
        "Incest sexual content is blocked.",
    ),
    (
        AdultPolicyFlag.BESTIALITY,
        (
            "bestiality",
            "zoophilia",
            "animal sex",
            "зоофил",
            "с животн",
        ),
        "Bestiality is blocked.",
    ),
    (
        AdultPolicyFlag.TRAFFICKING_OR_EXPLOITATION,
        (
            "trafficking",
            "sex slave",
            "forced prostitution",
            "exploitation",
            "торговля людьми",
            "сексуальное рабство",
            "принуждение к проституции",
        ),
        "Trafficking or sexual exploitation is blocked.",
    ),
)

REVIEW_PATTERNS: tuple[tuple[AdultPolicyFlag, tuple[str, ...], str], ...] = (
    (
        AdultPolicyFlag.NCII_OR_REAL_PERSON,
        (
            "celebrity lookalike",
            "real person",
            "my ex",
            "ex girlfriend",
            "ex boyfriend",
            "classmate",
            "coworker",
            "neighbor",
            "without consent",
            "non-consensual",
            "deepfake",
            "реальный человек",
            "бывшая",
            "бывший",
            "одноклассниц",
            "коллег",
            "сосед",
            "без согласия",
            "дипфейк",
        ),
        "Real-person sexual identity requires consent and human review.",
    ),
    (
        AdultPolicyFlag.PUBLIC_FIGURE,
        (
            "celebrity",
            "politician",
            "public figure",
            "actress",
            "actor",
            "singer",
            "famous",
            "знаменит",
            "политик",
            "актрис",
            "актер",
            "актёр",
            "певиц",
            "известн",
        ),
        "Public-figure sexual identity requests require review and are not public-feed safe.",
    ),
)

EXPLICIT_PUBLIC_MARKERS = (
    "nude",
    "porn",
    "sex",
    "explicit",
    "xxx",
    "nsfw",
    "обнажен",
    "обнажён",
    "порно",
    "секс",
    "эротик",
)


def evaluate_adult_policy(policy_input: AdultPolicyInput) -> AdultPolicyDecision:
    """Evaluate a normalized adult content request."""

    normalized = _normalize(policy_input.text)
    flags: list[AdultPolicyFlag] = []
    reasons: list[str] = []

    for flag, patterns, reason in ABSOLUTE_BLOCK_PATTERNS:
        if _contains_any(normalized, patterns):
            flags.append(flag)
            reasons.append(reason)

    if policy_input.has_real_person_reference and not policy_input.has_identity_consent:
        flags.append(AdultPolicyFlag.NCII_OR_REAL_PERSON)
        reasons.append("Real-person reference is present without explicit consent evidence.")

    if flags:
        return AdultPolicyDecision(
            action=AdultPolicyAction.BLOCK,
            flags=tuple(_dedupe(flags)),
            reasons=tuple(_dedupe_text(reasons)),
            public_allowed=False,
            metadata={"surface": policy_input.surface},
        )

    for flag, patterns, reason in REVIEW_PATTERNS:
        if _contains_any(normalized, patterns):
            flags.append(flag)
            reasons.append(reason)

    public_allowed = True
    if policy_input.is_public and _contains_any(normalized, EXPLICIT_PUBLIC_MARKERS):
        flags.append(AdultPolicyFlag.PUBLISHED_EXPLICIT)
        reasons.append("Explicit public content must pass human review and blur controls.")
        public_allowed = False

    if flags:
        flags.append(AdultPolicyFlag.NEEDS_HUMAN_REVIEW)
        return AdultPolicyDecision(
            action=AdultPolicyAction.REVIEW,
            flags=tuple(_dedupe(flags)),
            reasons=tuple(_dedupe_text(reasons)),
            public_allowed=public_allowed,
            metadata={"surface": policy_input.surface},
        )

    return AdultPolicyDecision(
        action=AdultPolicyAction.ALLOW,
        public_allowed=public_allowed,
        metadata={"surface": policy_input.surface},
    )


def evaluate_request_payload(
    request_payload: dict[str, Any],
    *,
    surface: str,
    is_public: bool = False,
    has_real_person_reference: bool = False,
    has_identity_consent: bool = False,
) -> AdultPolicyDecision:
    """Evaluate free-text fields in a provider request payload."""

    return evaluate_adult_policy(
        AdultPolicyInput(
            text=_extract_payload_text(request_payload),
            surface=surface,
            is_public=is_public,
            has_real_person_reference=has_real_person_reference,
            has_identity_consent=has_identity_consent,
        )
    )


def _extract_payload_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("prompt", "negative_prompt", "title", "description", "notes"):
        value = payload.get(key)
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


def _contains_any(value: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern.casefold().replace("ё", "е") in value for pattern in patterns)


def _dedupe(flags: list[AdultPolicyFlag]) -> list[AdultPolicyFlag]:
    seen: set[AdultPolicyFlag] = set()
    result: list[AdultPolicyFlag] = []
    for flag in flags:
        if flag in seen:
            continue
        seen.add(flag)
        result.append(flag)
    return result


def _dedupe_text(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
