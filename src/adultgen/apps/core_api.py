"""Core API application factory."""

from fastapi import FastAPI

from adultgen import __version__
from adultgen.api.routers import (
    admin,
    adult_consent,
    auth,
    billing,
    collections,
    generations,
    media,
    profiles,
    publications,
    subscriptions,
    system,
    wallets,
    webhooks,
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
    app.include_router(media.router)
    app.include_router(publications.router)
    app.include_router(billing.router)
    app.include_router(wallets.router)
    app.include_router(subscriptions.router)
    app.include_router(webhooks.router)
    app.include_router(admin.router)

    return app


app = create_app()
