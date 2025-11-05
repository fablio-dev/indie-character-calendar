"""HTTP retrieval utilities used by the scraping pipeline."""

from __future__ import annotations

import logging
import re
import re
from typing import Iterable, Mapping, Sequence

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


def extract_structured_event_details(html: str) -> dict[str, str]:
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    result: dict[str, str] = {}

    for columns in soup.find_all("div", class_=lambda c: c and "wp-block-columns" in c.split()):
        column_divs = columns.find_all(
            "div",
            class_=lambda c: c and "wp-block-column" in c.split(),
            recursive=False,
        )
        if len(column_divs) < 2:
            continue

        label_text = column_divs[0].get_text(separator=" ", strip=True)
        value_text = column_divs[1].get_text(separator=" ", strip=True)
        label_text = label_text.replace("：", "").strip()
        value_text = value_text.strip()

        field = _COLUMN_LABEL_MAP.get(label_text)
        if not field:
            continue

        normalized_value = _normalize_structured_value(field, value_text)
        if normalized_value:
            result[field] = normalized_value

    return result


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
        if image is None:
            continue
        attrs = getattr(image, "attrs", None)
        if not isinstance(attrs, dict):
            continue
        alt_text = (attrs.get("alt") or "").strip()
        if alt_text:
            image.insert_after(NavigableString(alt_text))
        image.decompose()


def _normalize_whitespace(text: str) -> str:
    collapsed = _WHITESPACE_RE.sub(" ", text)
    lines = [line.strip() for line in collapsed.splitlines()]
    filtered = [line for line in lines if line]
    return "\n".join(filtered)


_COLUMN_LABEL_MAP: dict[str, str | None] = {
    "会期名": "event_name",
    "イベント名": "event_name",
    "日程": "event_date",
    "開催日": "event_date",
    "会場": "location",
    "開催場所": "location",
    "締切": "deadline",
    "応募締切": "deadline",
    "申込締切": "deadline",
    "募集締切": "deadline",
    "出展者募集期間": "deadline",
    "募集期間": "deadline",
    "エントリー締切": "deadline",
}


def _normalize_structured_value(field: str, value: str) -> str:
    if not value:
        return ""
    if field in {"event_date", "deadline"}:
        normalized = _normalize_japanese_date_range(value)
        return normalized or value
    return value


def _normalize_japanese_date_range(text: str) -> str:
    value = text.strip()
    if not value:
        return ""

    full_patterns = re.findall(r"(\d{4})年(\d{1,2})月(\d{1,2})日", value)
    formatted: list[str] = []
    used_days: set[tuple[int, int, int]] = set()

    for year_str, month_str, day_str in full_patterns:
        year, month, day = int(year_str), int(month_str), int(day_str)
        formatted.append(f"{year:04d}-{month:02d}-{day:02d}")
        used_days.add((year, month, day))

    base_match = re.search(r"(\d{4})年(\d{1,2})月", value)
    if base_match:
        base_year, base_month = int(base_match.group(1)), int(base_match.group(2))
        day_matches = re.findall(r"(\d{1,2})日", value)
        for idx, day_str in enumerate(day_matches):
            day = int(day_str)
            candidate = (base_year, base_month, day)
            if candidate not in used_days:
                formatted.append(f"{base_year:04d}-{base_month:02d}-{day:02d}")
                used_days.add(candidate)

    if not formatted:
        return ""

    # Remove duplicates while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for item in formatted:
        if item not in seen:
            ordered.append(item)
            seen.add(item)

    if len(ordered) == 1:
        return ordered[0]
    return "/".join(ordered)
