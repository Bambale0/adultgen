"""System and diagnostics endpoints."""

from fastapi import APIRouter

from adultgen import __version__

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Return a cheap liveness response.

    This endpoint intentionally does not touch external dependencies. It is safe
    for Docker, Nginx, and load-balancer health checks.
    """

    return {"status": "ok"}


@router.get("/version")
async def version() -> dict[str, str]:
    """Return the running application version."""

    return {"version": __version__}
