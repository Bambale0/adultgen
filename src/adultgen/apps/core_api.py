"""Core API application factory.

The initial API only exposes health and version endpoints. Domain routers should be
registered here as implementation phases are completed.
"""

from fastapi import FastAPI

from adultgen import __version__


def create_app() -> FastAPI:
    """Create the Core API FastAPI application."""

    app = FastAPI(
        title="AdultGen Core API",
        version=__version__,
        description="Backend-first platform for Telegram AI media generation.",
    )

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/version", tags=["system"])
    async def version() -> dict[str, str]:
        return {"version": __version__}

    return app


app = create_app()
