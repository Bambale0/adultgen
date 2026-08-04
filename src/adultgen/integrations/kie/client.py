"""Kie API client.

The adapter is intentionally thin: it submits a createTask payload and returns the
provider task id. Business state transitions stay in services, not in the HTTP
client.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class KieClientError(RuntimeError):
    """Raised when Kie API submission fails or returns an unexpected payload."""


@dataclass(frozen=True, slots=True)
class KieCreateTaskResult:
    """Normalized result of Kie createTask."""

    provider_task_id: str
    raw_response: dict[str, Any]


class KieClient:
    """Async HTTP client for Kie task submission."""

    def __init__(self, *, base_url: str, api_key: str, timeout_seconds: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def create_task(self, payload: dict[str, object]) -> KieCreateTaskResult:
        """Submit a Kie /api/v1/jobs/createTask request."""

        url = f"{self.base_url}/api/v1/jobs/createTask"
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise KieClientError(f"Kie returned non-JSON response with status {response.status_code}.") from exc

        if response.status_code >= 400:
            raise KieClientError(f"Kie createTask failed with status {response.status_code}: {data!r}")

        provider_task_id = extract_kie_task_id(data)
        return KieCreateTaskResult(provider_task_id=provider_task_id, raw_response=data)


def extract_kie_task_id(response_data: dict[str, Any]) -> str:
    """Extract provider task id from common Kie response shapes."""

    candidates: list[Any] = [
        response_data.get("taskId"),
        response_data.get("task_id"),
        response_data.get("id"),
    ]
    nested_data = response_data.get("data")
    if isinstance(nested_data, dict):
        candidates.extend(
            [
                nested_data.get("taskId"),
                nested_data.get("task_id"),
                nested_data.get("id"),
            ]
        )

    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
        if isinstance(candidate, int):
            return str(candidate)

    raise KieClientError(f"Kie createTask response does not contain a task id: {response_data!r}")
