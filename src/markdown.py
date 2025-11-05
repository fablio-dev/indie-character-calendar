"""Markdown rendering utilities for README table generation."""

from __future__ import annotations

import re
from datetime import date
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


def update_readme_table(
    readme_path: str | Path,
    table_text: str,
) -> bool:
    """Replace the README marker section with ``table_text``."""
    content = Path(readme_path).read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}",
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        raise RuntimeError("README markers not found.")

    replacement = f"{MARKER_START}\n{table_text}\n{MARKER_END}"
    updated_content = pattern.sub(replacement, content, count=1)

    if updated_content == content:
        return False

    Path(readme_path).write_text(updated_content, encoding="utf-8")
    return True


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
        row.get("last_updated", "") or "",
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
    if not value or not DATE_RE.match(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _render_url_cell(url: str) -> str:
    if not url:
        return "-"
    return f"[リンク]({url})"
