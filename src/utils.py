"""Utility helpers for the auto-event-calendar project."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Mapping, MutableMapping
from zoneinfo import ZoneInfo

import requests

LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15
MAX_RETRIES = 2  # Number of retries in addition to the initial attempt.
BACKOFF_INITIAL_DELAY = 1.0
BACKOFF_MULTIPLIER = 2.0
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "auto-event-calendar/0.1 (+https://github.com/auto-event-calendar)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
JST = ZoneInfo("Asia/Tokyo")


def merge_headers(extra: Mapping[str, str] | None) -> MutableMapping[str, str]:
    """Return HTTP headers merged with defaults without mutating inputs."""
    headers: MutableMapping[str, str] = dict(DEFAULT_HEADERS)
    if extra:
        headers.update(extra)
    return headers


def request_with_retries(
    url: str,
    *,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    **request_kwargs: object,
) -> requests.Response:
    """Perform an HTTP request with exponential backoff retries."""
    attempt = 0
    delay = BACKOFF_INITIAL_DELAY
    session = requests.Session()

    try:
        while True:
            try:
                response = session.request(
                    method,
                    url,
                    headers=merge_headers(headers),
                    timeout=timeout,
                    **request_kwargs,
                )
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                if attempt >= max_retries:
                    raise exc
                attempt += 1
                LOGGER.warning(
                    "Request to %s failed (attempt %s/%s): %s",
                    url,
                    attempt,
                    max_retries,
                    exc,
                )
                time.sleep(delay)
                delay *= BACKOFF_MULTIPLIER
    finally:
        session.close()


def now_jst_isoformat() -> str:
    """Return the current timestamp in JST as an ISO 8601 string."""
    return datetime.now(tz=JST).isoformat()
