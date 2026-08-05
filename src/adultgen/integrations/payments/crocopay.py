"""CrocoPay Express API integration helpers."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx


class CrocoPayError(ValueError):
    """Raised when a CrocoPay payload cannot be built or verified."""


@dataclass(frozen=True, slots=True)
class CrocoPayInitiatePaymentCommand:
    """Command for CrocoPay `/api/v2/initiate-payment`."""

    client_id: str
    client_secret: str
    amount_minor: int
    currency: str
    success_url: str
    cancel_url: str
    callback_url: str


@dataclass(frozen=True, slots=True)
class CrocoPayCheckout:
    """CrocoPay checkout response normalized for AdultGen."""

    redirect_url: str
    external_payment_id: str | None


@dataclass(frozen=True, slots=True)
class ParsedCrocoPayCallback:
    """Verified CrocoPay successful-payment callback."""

    timestamp: int
    subtotal: int
    total: int
    signature_valid: bool


def build_crocopay_initiate_payload(command: CrocoPayInitiatePaymentCommand) -> dict[str, str]:
    """Build form payload expected by CrocoPay Express API."""

    if command.amount_minor <= 0:
        raise CrocoPayError("Payment amount must be positive.")
    return {
        "client_id": command.client_id,
        "client_secret": command.client_secret,
        "amount": _minor_to_major(command.amount_minor),
        "currency": command.currency.upper(),
        "successUrl": command.success_url,
        "cancelUrl": command.cancel_url,
        "callbackUrl": command.callback_url,
    }


async def initiate_crocopay_payment(
    *,
    api_base_url: str,
    command: CrocoPayInitiatePaymentCommand,
    timeout_seconds: float = 15.0,
) -> CrocoPayCheckout:
    """Create a CrocoPay payment link and return the redirect URL."""

    payload = build_crocopay_initiate_payload(command)
    async with httpx.AsyncClient(base_url=api_base_url.rstrip("/"), timeout=timeout_seconds) as client:
        response = await client.post("/api/v2/initiate-payment", data=payload)
        response.raise_for_status()
        body = response.json()

    if body.get("status") != "success" or not isinstance(body.get("redirect_url"), str):
        message = body.get("message") if isinstance(body.get("message"), str) else "CrocoPay initiate-payment failed."
        raise CrocoPayError(message)

    redirect_url = body["redirect_url"]
    external_payment_id = _extract_grant_id(redirect_url)
    return CrocoPayCheckout(redirect_url=redirect_url, external_payment_id=external_payment_id)


def verify_crocopay_callback(payload: dict[str, Any], *, client_secret: str) -> ParsedCrocoPayCallback:
    """Verify a CrocoPay callback body using HMAC-SHA256."""

    timestamp = _int_field(payload, "timestamp")
    subtotal = _int_field(payload, "subtotal")
    percentage = _int_field(payload, "percentage")
    charge_percentage = _int_field(payload, "charge_percentage")
    charge_fixed = _int_field(payload, "charge_fixed")
    total = _int_field(payload, "total")
    received_sign = payload.get("sign")
    if not isinstance(received_sign, str) or not received_sign:
        raise CrocoPayError("CrocoPay callback is missing signature.")

    signed_message = f"{timestamp}|{subtotal}|{percentage}|{charge_percentage}|{charge_fixed}|{total}"
    expected_sign = hmac.new(client_secret.encode("utf-8"), signed_message.encode("utf-8"), hashlib.sha256).hexdigest()
    signature_valid = hmac.compare_digest(expected_sign, received_sign)
    return ParsedCrocoPayCallback(
        timestamp=timestamp,
        subtotal=subtotal,
        total=total,
        signature_valid=signature_valid,
    )


def _minor_to_major(amount_minor: int) -> str:
    value = Decimal(amount_minor) / Decimal(100)
    return f"{value:.2f}"


def _int_field(payload: dict[str, Any], field: str) -> int:
    value = payload.get(field)
    if isinstance(value, bool):
        raise CrocoPayError(f"CrocoPay callback field `{field}` must be an integer.")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise CrocoPayError(f"CrocoPay callback field `{field}` is missing or invalid.")


def _extract_grant_id(redirect_url: str) -> str | None:
    marker = "grant_id="
    if marker not in redirect_url:
        return None
    return redirect_url.split(marker, maxsplit=1)[1].split("&", maxsplit=1)[0] or None
