"""Markdown rendering utilities for README table generation."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Sequence

TABLE_HEADERS: tuple[str, ...] = (
    "イベント名",
    "開催日",
    "開催場所",
    "締切",
    "ステータス",
    "公式URL",
    "最終更新",
)
MARKER_START = "<!-- events:table:start -->"
MARKER_END = "<!-- events:table:end -->"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_SPLIT_SEPARATORS: tuple[str, ...] = ("/", "~", "〜", "～")


def render_table(
    rows: Sequence[dict[str, str]],
    *,
    highlight_timestamp: str | None = None,
) -> str:
    """Return a Markdown table sorted by event_date with optional highlighting."""
    sorted_rows = sorted(rows, key=_sorting_key)
    lines: list[str] = [
        _render_header(),
        _render_separator(),
    ]

    for row in sorted_rows:
        lines.append(
            _render_row(
                row,
                highlight_timestamp=highlight_timestamp,
            )
        )

    if len(lines) == 2:
        # No data rows: provide an explicit placeholder row.
        lines.append(_render_empty_row())

    return "\n".join(lines)


def update_markdown_table(
    target_path: str | Path,
    table_text: str,
) -> bool:
    """Replace the marker section inside ``target_path`` with ``table_text``."""
    content = Path(target_path).read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}",
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        raise RuntimeError("Marker section not found.")

    replacement = f"{MARKER_START}\n{table_text}\n{MARKER_END}"
    updated_content = pattern.sub(replacement, content, count=1)

    if updated_content == content:
        return False

    Path(target_path).write_text(updated_content, encoding="utf-8")
    return True


def update_readme_table(
    readme_path: str | Path,
    table_text: str,
) -> bool:
    """Backward-compatible wrapper that updates README.md."""
    return update_markdown_table(readme_path, table_text)


def _render_header() -> str:
    return _render_markdown_row(TABLE_HEADERS)


def _render_separator() -> str:
    return _render_markdown_row(["---"] * len(TABLE_HEADERS))


def _render_row(
    row: dict[str, str],
    *,
    highlight_timestamp: str | None,
) -> str:
    event_name = row.get("event_name", "")
    if highlight_timestamp and row.get("last_updated") == highlight_timestamp:
        event_name = f"**{event_name}**"

    url = row.get("url", "")
    url_cell = _render_url_cell(url)

    cells: Iterable[str] = (
        event_name or "",
        row.get("event_date", "") or "",
        row.get("location", "") or "",
        row.get("deadline", "") or "",
        row.get("status", "") or "",
        url_cell,
        _format_last_updated(row.get("last_updated")),
    )
    return _render_markdown_row(cells)


def _render_empty_row() -> str:
    return _render_markdown_row(["-"] * len(TABLE_HEADERS))


def _render_markdown_row(values: Iterable[str]) -> str:
    escaped = [str(value).replace("\n", " ").strip() for value in values]
    return "| " + " | ".join(escaped) + " |"


def _sorting_key(row: dict[str, str]) -> tuple[int, date | str]:
    sortable_date = _parse_date(row.get("event_date", ""))
    if sortable_date is None:
        return (1, row.get("event_name", ""))
    return (0, sortable_date)


def _parse_date(value: str | None) -> date | None:
    primary = _extract_primary_date(value)
    if not primary:
        return None
    try:
        return date.fromisoformat(primary)
    except ValueError:
        return None


def _render_url_cell(url: str) -> str:
    if not url:
        return "-"
    return f"[リンク]({url})"


def _format_last_updated(value: str | None) -> str:
    if not value:
        return ""
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError:
        return value
    return timestamp.strftime("%Y-%m-%d %H:%M")


def _extract_primary_date(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    for separator in DATE_SPLIT_SEPARATORS:
        if separator in candidate:
            candidate = candidate.split(separator, 1)[0].strip()
            break
    if DATE_RE.match(candidate):
        return candidate
    return None
