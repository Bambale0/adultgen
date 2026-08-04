"""Aiogram dispatcher factory for Telegram gateway."""

from aiogram import Dispatcher


def create_dispatcher() -> Dispatcher:
    """Create Telegram gateway dispatcher.

    Business handlers are intentionally added later. This factory gives the
    webhook boundary a stable place to attach routers without mixing them into
    FastAPI app setup.
    """

    return Dispatcher()
