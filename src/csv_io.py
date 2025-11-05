"""Utilities for loading, saving, and updating the events CSV file."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence

from .utils import now_jst_isoformat

CSV_COLUMNS: tuple[str, ...] = (
    "alias",
    "url",
    "genre",
    "event_name",
    "event_date",
    "location",
    "deadline",
    "status",
    "last_updated",
    "comment",
)
UPDATE_FIELDS: tuple[str, ...] = (
    "event_name",
    "event_date",
    "location",
    "deadline",
    "status",
)


class CSVSchemaError(RuntimeError):
    """Raised when the CSV schema does not comply with the contract."""


def load_events(path: str | Path) -> list[dict[str, str]]:
    """Load events from ``path`` validating the expected header order."""
    file_path = Path(path)
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise CSVSchemaError("Events CSV is missing a header row.")
        if tuple(reader.fieldnames) != CSV_COLUMNS:
            raise CSVSchemaError(
                f"Unexpected CSV header: {reader.fieldnames} != {CSV_COLUMNS}"
            )

        rows: list[dict[str, str]] = []
        seen_aliases: set[str] = set()
        for raw_row in reader:
            row = {column: _normalize_cell(raw_row.get(column)) for column in CSV_COLUMNS}
            alias = row["alias"]
            if not alias:
                raise CSVSchemaError("Encountered a row with an empty alias.")
            if alias in seen_aliases:
                raise CSVSchemaError(f"Duplicate alias detected: {alias}")
            seen_aliases.add(alias)
            rows.append(row)
        return rows


def save_events(path: str | Path, rows: Sequence[Mapping[str, str]]) -> bool:
    """Persist ``rows`` to ``path`` only when the on-disk content would change."""
    normalized_rows = list(_normalize_rows(rows))
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(normalized_rows)
    new_content = buffer.getvalue()

    file_path = Path(path)
    if file_path.exists():
        current_content = file_path.read_text(encoding="utf-8")
        if current_content == new_content:
            return False

    file_path.write_text(new_content, encoding="utf-8")
    return True


def index_by_alias(rows: Iterable[MutableMapping[str, str]]) -> dict[str, MutableMapping[str, str]]:
    """Return an alias-indexed mapping for quicker lookups."""
    indexed: dict[str, MutableMapping[str, str]] = {}
    for row in rows:
        alias = row.get("alias")
        if not alias:
            raise CSVSchemaError("Row missing alias cannot be indexed.")
        if alias in indexed:
            raise CSVSchemaError(f"Duplicate alias detected while indexing: {alias}")
        indexed[alias] = row
    return indexed


def apply_success_update(
    row: MutableMapping[str, str],
    updates: Mapping[str, str],
    *,
    timestamp: str | None = None,
) -> bool:
    """Apply successful extraction updates and reset the comment when needed."""
    changed = False
    normalized_updates = {
        field: _normalize_cell(updates.get(field, "不明"))
        for field in UPDATE_FIELDS
    }

    for field, value in normalized_updates.items():
        if row.get(field) != value:
            row[field] = value
            changed = True

    if row.get("comment"):
        row["comment"] = ""
        changed = True

    if changed:
        row["last_updated"] = timestamp or now_jst_isoformat()

    return changed


def apply_error_update(
    row: MutableMapping[str, str],
    message: str,
    *,
    timestamp: str | None = None,
) -> bool:
    """Record an error message without touching the extracted fields."""
    normalized_message = message.strip() or "情報取得に失敗しました"
    effective_timestamp = timestamp or now_jst_isoformat()

    changed = False
    if row.get("comment") != normalized_message:
        row["comment"] = normalized_message
        changed = True

    if row.get("last_updated") != effective_timestamp:
        row["last_updated"] = effective_timestamp
        changed = True

    return changed


def _normalize_rows(rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen_aliases: set[str] = set()
    for row in rows:
        normalized_row = {column: _normalize_cell(row.get(column)) for column in CSV_COLUMNS}
        alias = normalized_row["alias"]
        if not alias:
            raise CSVSchemaError("Attempted to write a row with an empty alias.")
        if alias in seen_aliases:
            raise CSVSchemaError(f"Duplicate alias detected while writing: {alias}")
        seen_aliases.add(alias)
        normalized.append(normalized_row)
    return normalized


def _normalize_cell(value: object) -> str:
    """Normalize CSV cell values to non-null strings."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)
