"""Moderation case service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.moderation import ModerationCase
from adultgen.db.models.publications import Publication
from adultgen.domain.adult_policy import AdultPolicyDecision, AdultPolicyFlag
from adultgen.domain.enums import PublicationStatus


class ModerationServiceError(ValueError):
    """Raised when moderation operations cannot be completed."""


MODERATION_STATUS_OPEN = "open"
MODERATION_STATUS_RESOLVED = "resolved"
MODERATION_STATUS_REJECTED = "rejected"


REPORT_CATEGORY_TO_PRIORITY = {
    "minor_or_underage": 100,
    "ncii_or_real_person": 90,
    "coercion_or_violence": 80,
    "hidden_camera": 80,
    "trafficking_or_exploitation": 80,
    "public_figure": 60,
    "explicit_public": 40,
    "other": 10,
}


async def create_policy_moderation_case(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    decision: AdultPolicyDecision,
    surface: str,
    publication_id: uuid.UUID | None = None,
    description: str | None = None,
) -> ModerationCase:
    """Create a moderation case from a policy decision."""

    category = _primary_flag(decision)
    case = ModerationCase(
        publication_id=publication_id,
        reported_user_id=user_id,
        reporter_user_id=None,
        category=category,
        description=description or _decision_description(decision, surface),
        status=MODERATION_STATUS_OPEN,
        priority=_priority_for_category(category),
    )
    session.add(case)
    await session.flush()
    return case


async def report_publication(
    session: AsyncSession,
    *,
    reporter_user_id: uuid.UUID,
    publication_id: uuid.UUID,
    category: str,
    description: str | None = None,
) -> ModerationCase:
    """Create a moderation report for a publication."""

    normalized_category = _normalize_category(category)
    result = await session.execute(select(Publication).where(Publication.id == publication_id))
    publication = result.scalar_one_or_none()
    if publication is None or publication.deleted_at is not None:
        raise ModerationServiceError("Publication not found.")

    case = ModerationCase(
        publication_id=publication.id,
        reported_user_id=publication.user_id,
        reporter_user_id=reporter_user_id,
        category=normalized_category,
        description=description,
        status=MODERATION_STATUS_OPEN,
        priority=_priority_for_category(normalized_category),
    )
    session.add(case)
    await session.flush()
    return case


async def list_open_moderation_cases(
    session: AsyncSession,
    *,
    limit: int = 50,
) -> list[ModerationCase]:
    """List open moderation cases by priority and recency."""

    if limit <= 0 or limit > 100:
        raise ModerationServiceError("Moderation queue limit must be between 1 and 100.")

    result = await session.execute(
        select(ModerationCase)
        .where(ModerationCase.status == MODERATION_STATUS_OPEN)
        .order_by(ModerationCase.priority.desc(), ModerationCase.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars())


async def resolve_moderation_case(
    session: AsyncSession,
    *,
    case_id: uuid.UUID,
    admin_user_id: uuid.UUID | None,
    resolution: str,
    action: str = "resolve",
) -> ModerationCase:
    """Resolve a moderation case and optionally hide linked publication."""

    result = await session.execute(select(ModerationCase).where(ModerationCase.id == case_id))
    case = result.scalar_one_or_none()
    if case is None:
        raise ModerationServiceError("Moderation case not found.")
    if case.status != MODERATION_STATUS_OPEN:
        raise ModerationServiceError("Moderation case is already closed.")

    normalized_action = action.casefold().strip()
    if normalized_action not in {"resolve", "reject", "hide_publication"}:
        raise ModerationServiceError("Unknown moderation action.")

    if normalized_action == "hide_publication" and case.publication_id:
        await _hide_publication(session, case.publication_id)

    case.status = MODERATION_STATUS_REJECTED if normalized_action == "reject" else MODERATION_STATUS_RESOLVED
    case.resolution = resolution
    case.resolved_by_admin_id = admin_user_id
    case.resolved_at = datetime.now(UTC)
    await session.flush()
    return case


async def _hide_publication(session: AsyncSession, publication_id: uuid.UUID) -> None:
    result = await session.execute(select(Publication).where(Publication.id == publication_id))
    publication = result.scalar_one_or_none()
    if publication is None:
        return
    publication.status = PublicationStatus.REJECTED.value
    await session.flush()


def _primary_flag(decision: AdultPolicyDecision) -> str:
    if not decision.flags:
        return "other"
    return decision.flags[0].value


def _decision_description(decision: AdultPolicyDecision, surface: str) -> str:
    reasons = "; ".join(decision.reasons) if decision.reasons else "Policy review required."
    flags = ", ".join(flag.value for flag in decision.flags) if decision.flags else "none"
    return f"{surface}: {decision.action.value}. Flags: {flags}. Reasons: {reasons}"


def _priority_for_category(category: str) -> int:
    return REPORT_CATEGORY_TO_PRIORITY.get(_normalize_category(category), 10)


def _normalize_category(category: str) -> str:
    normalized = category.casefold().strip().replace(" ", "_").replace("-", "_")
    allowed = {flag.value for flag in AdultPolicyFlag} | set(REPORT_CATEGORY_TO_PRIORITY)
    return normalized if normalized in allowed else "other"
