"""Admin API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from adultgen.api.dependencies import require_admin_api_token

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_api_token)],
)


@router.get("/health")
async def admin_health(_admin: Annotated[None, Depends(require_admin_api_token)]) -> dict[str, str]:
    """Protected admin health endpoint used to verify admin auth wiring."""

    return {"status": "ok", "scope": "admin"}
