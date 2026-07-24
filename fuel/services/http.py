"""Shared HTTP helpers with capped retries for transient failures."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def request_json(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 20.0,
    retries: int | None = None,
    backoff_seconds: float | None = None,
) -> dict[str, Any] | list[Any]:
    """
    Perform an HTTP request and return parsed JSON.

    Retries only on timeouts and 5xx responses. Retry count is capped via settings
    so we do not silently multiply the external-call budget.
    """
    retries = settings.EXTERNAL_HTTP_RETRIES if retries is None else retries
    backoff = (
        settings.EXTERNAL_HTTP_BACKOFF_SECONDS
        if backoff_seconds is None
        else backoff_seconds
    )
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            response = requests.request(
                method,
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            if response.status_code >= 500:
                raise requests.HTTPError(
                    f"Server error {response.status_code} for {url}",
                    response=response,
                )
            response.raise_for_status()
            return response.json()
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            sleep_for = backoff * (attempt + 1)
            logger.warning(
                "Transient HTTP failure (attempt %s/%s) %s %s: %s; retrying in %.1fs",
                attempt + 1,
                retries + 1,
                method,
                url,
                exc,
                sleep_for,
            )
            time.sleep(sleep_for)

    assert last_error is not None
    raise last_error
