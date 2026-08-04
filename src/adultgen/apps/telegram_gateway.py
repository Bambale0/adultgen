"""Telegram Gateway application factory."""

from fastapi import FastAPI

from adultgen import __version__
from adultgen.api.routers import telegram_gateway


def create_app() -> FastAPI:
    """Create the Telegram Gateway FastAPI application."""

    app = FastAPI(
        title="AdultGen Telegram Gateway",
        version=__version__,
        description="Webhook gateway for replaceable Telegram bot channels.",
    )
    app.include_router(telegram_gateway.router)
    return app


app = create_app()
