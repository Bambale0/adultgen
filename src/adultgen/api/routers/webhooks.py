"""Provider webhook routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_db_session, get_runtime_settings
from adultgen.api.schemas.webhooks import KieCallbackResponse
from adultgen.config import Settings
from adultgen.services.kie_callbacks import KieCallbackError, ingest_kie_callback

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/kie", response_model=KieCallbackResponse)
async def ingest_kie_provider_callback(
    payload: dict[str, object],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    secret: Annotated[str | None, Query()] = None,
    x_adultgen_webhook_secret: Annotated[str | None, Header(alias="X-AdultGen-Webhook-Secret")] = None,
) -> KieCallbackResponse:
    """Ingest Kie task completion/failure callbacks.

    The callback URL can include `?secret=...`; a custom header is also accepted
    for providers or reverse proxies that support it.
    """

    configured_secret = settings.kie_webhook_secret.strip()
    if configured_secret:
        received_secret = secret or x_adultgen_webhook_secret
        if received_secret != configured_secret:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Kie webhook secret.")

    try:
        result = await ingest_kie_callback(session, settings=settings, payload=payload)
    except KieCallbackError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return KieCallbackResponse(
        provider_task_id=result.provider_task_id,
        generation_task_id=result.generation_task_id,
        status=result.status,
        changed_task=result.changed_task,
        result_asset_ids=list(result.result_asset_ids),
        scene_take_id=result.scene_take_id,
    )
