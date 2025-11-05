"""HTTP retrieval utilities used by the scraping pipeline."""

from __future__ import annotations

import logging
import re
from typing import Iterable, Sequence

from bs4 import BeautifulSoup, Comment, NavigableString

from .utils import DEFAULT_TIMEOUT, request_with_retries

LOGGER = logging.getLogger(__name__)


def fetch_html(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Fetch raw HTML from ``url`` using the shared retry configuration."""
    if not url:
        raise ValueError("url must be a non-empty string")

    LOGGER.debug("HTTP GET start: %s", url)
    response = request_with_retries(
        url,
        timeout=timeout,
    )
    LOGGER.debug(
        "HTTP GET done: %s status=%s content_length=%s",
        url,
        response.status_code,
        len(response.text),
    )
    return response.text


_REMOVABLE_TAGS: Sequence[str] = (
    "script",
    "style",
    "noscript",
    "template",
    "svg",
    "canvas",
    "iframe",
    "object",
    "embed",
    "header",
    "footer",
    "nav",
    "form",
    "aside",
)
_NOISE_KEYWORDS: Sequence[str] = (
    "breadcrumb",
    "sidebar",
    "advert",
    "ads",
    "sponsor",
    "social",
    "share",
    "subscribe",
    "cookie",
    "banner",
)
_WHITESPACE_RE = re.compile(r"[ \t\u00a0]+")


def extract_main_text(html: str) -> str:
    """Convert HTML into cleaned plain text suitable for LLM extraction."""
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    _remove_comments(soup)
    _remove_tags(soup, _REMOVABLE_TAGS)
    _remove_noise_by_keyword(soup, _NOISE_KEYWORDS)
    _inject_alt_text(soup)

    container = soup.body or soup
    text = container.get_text(separator="\n")
    return _normalize_whitespace(text)


def _remove_comments(soup: BeautifulSoup) -> None:
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()


def _remove_tags(soup: BeautifulSoup, tags: Iterable[str]) -> None:
    for tag_name in tags:
        for node in soup.find_all(tag_name):
            node.decompose()


def _remove_noise_by_keyword(soup: BeautifulSoup, keywords: Sequence[str]) -> None:
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    for element in soup.find_all(True):
        if element is None:
            continue
        attrs = getattr(element, "attrs", {}) or {}
        if not isinstance(attrs, dict):
            continue
        classes = attrs.get("class") or ()
        if isinstance(classes, str):
            classes = (classes,)
        attributes_text = " ".join(
            filter(
                None,
                [
                    attrs.get("id", ""),
                    " ".join(classes),
                    attrs.get("role", ""),
                    attrs.get("aria-label", ""),
                ],
            )
        ).lower()
        if any(keyword in attributes_text for keyword in lowered_keywords):
            element.decompose()


def _inject_alt_text(soup: BeautifulSoup) -> None:
    for image in list(soup.find_all("img")):
        if image is None or not hasattr(image, "attrs"):
            continue
        alt_text = (image.attrs.get("alt") or "").strip()
        if alt_text:
            image.insert_after(NavigableString(alt_text))
        image.decompose()


def _normalize_whitespace(text: str) -> str:
    collapsed = _WHITESPACE_RE.sub(" ", text)
    lines = [line.strip() for line in collapsed.splitlines()]
    filtered = [line for line in lines if line]
    return "\n".join(filtered)
