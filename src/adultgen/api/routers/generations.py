"""Generation task routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session
from adultgen.api.schemas.generations import CreateGenerationTaskRequest, GenerationTaskResponse
from adultgen.domain.model_capabilities import CapabilityValidationError
from adultgen.domain.pricing import PricingError
from adultgen.domain.wallet_ledger import WalletLedgerError
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.generations import GenerationServiceError, create_generation_task_with_reserve

router = APIRouter(prefix="/generations", tags=["generations"])


@router.post("", response_model=GenerationTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_generation_task(
    payload: CreateGenerationTaskRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
) -> GenerationTaskResponse:
    """Create a generation task and reserve credits before provider submission."""

    try:
        task = await create_generation_task_with_reserve(
            session,
            user_id=claims.subject,
            model_code=payload.model_code,
            operation=payload.operation,
            request_payload=payload.request_payload,
            project_id=payload.project_id,
            scene_id=payload.scene_id,
        )
    except (CapabilityValidationError, PricingError, GenerationServiceError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except WalletLedgerError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc

    return GenerationTaskResponse(
        id=task.id,
        status=task.status,
        provider=task.provider,
        model_code=task.model_code,
        operation=task.operation,
        reserved_credits=task.reserved_credits,
        charged_credits=task.charged_credits,
        provider_task_id=task.provider_task_id,
        error_code=task.error_code,
        error_message=task.error_message,
    )
