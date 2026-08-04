"""Core API application factory."""

from fastapi import FastAPI

from adultgen import __version__
from adultgen.api.routers import auth, generations, system


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

    return app


app = create_app()
