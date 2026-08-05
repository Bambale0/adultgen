"""Moderation report and admin queue routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session, require_admin_api_token
from adultgen.api.schemas.moderation import (
    ModerationCaseResponse,
    ModerationQueueResponse,
    ReportPublicationRequest,
    ResolveModerationCaseRequest,
)
from adultgen.db.models.moderation import ModerationCase
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.moderation import (
    ModerationServiceError,
    list_open_moderation_cases,
    report_publication,
    resolve_moderation_case,
)

router = APIRouter(tags=["moderation"])


@router.post("/publications/{publication_id}/reports", response_model=ModerationCaseResponse)
async def report_publication_content(
    publication_id: uuid.UUID,
    payload: ReportPublicationRequest,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ModerationCaseResponse:
    """Create a user report for a publication."""

    try:
        case = await report_publication(
            session,
            reporter_user_id=claims.subject,
            publication_id=publication_id,
            category=payload.category,
            description=payload.description,
        )
    except ModerationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _case_response(case)


@router.get(
    "/admin/moderation/cases",
    response_model=ModerationQueueResponse,
    dependencies=[Depends(require_admin_api_token)],
)
async def list_admin_moderation_cases(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ModerationQueueResponse:
    """List open moderation cases for admin review."""

    try:
        cases = await list_open_moderation_cases(session, limit=limit)
    except ModerationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return ModerationQueueResponse(items=[_case_response(case) for case in cases])


@router.post(
    "/admin/moderation/cases/{case_id}/resolve",
    response_model=ModerationCaseResponse,
    dependencies=[Depends(require_admin_api_token)],
)
async def resolve_admin_moderation_case(
    case_id: uuid.UUID,
    payload: ResolveModerationCaseRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ModerationCaseResponse:
    """Resolve, reject, or hide publication for an open moderation case."""

    try:
        case = await resolve_moderation_case(
            session,
            case_id=case_id,
            admin_user_id=None,
            action=payload.action,
            resolution=payload.resolution,
        )
    except ModerationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _case_response(case)


def _case_response(case: ModerationCase) -> ModerationCaseResponse:
    return ModerationCaseResponse(
        id=case.id,
        publication_id=case.publication_id,
        reported_user_id=case.reported_user_id,
        reporter_user_id=case.reporter_user_id,
        category=case.category,
        description=case.description,
        status=case.status,
        priority=case.priority,
        resolution=case.resolution,
        resolved_by_admin_id=case.resolved_by_admin_id,
        resolved_at=case.resolved_at,
        created_at=case.created_at,
    )
