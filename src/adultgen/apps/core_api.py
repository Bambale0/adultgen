"""Core API application factory."""

from fastapi import FastAPI

from adultgen import __version__
from adultgen.api.routers import (
    admin,
    adult_consent,
    auth,
    collections,
    generations,
    profiles,
    system,
    workspace,
)


def create_app() -> FastAPI:
    """Create the Core API FastAPI application."""

    app = FastAPI(
        title="AdultGen Core API",
        version=__version__,
        description="Backend-first platform for Telegram AI media generation.",
    )

    app.include_router(system.router)
    app.include_router(auth.router)
    app.include_router(generations.router)
    app.include_router(adult_consent.router)
    app.include_router(workspace.router)
    app.include_router(profiles.router)
    app.include_router(collections.router)
    app.include_router(admin.router)

    return app


app = create_app()
