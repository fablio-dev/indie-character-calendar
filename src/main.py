"""Command-line entry point for the auto-event-calendar pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Sequence

import requests

from .ai_client import GeminiError, extract_event_info, extract_multiple_events
from .csv_io import (
    UPDATE_FIELDS,
    CSVSchemaError,
    apply_error_update,
    apply_success_update,
    load_events,
    save_events,
)
from .markdown import render_table, update_readme_table
from .scrape import extract_main_text, fetch_html
from .utils import now_jst_isoformat

LOGGER = logging.getLogger("auto_event_calendar.main")

DEFAULT_EVENTS_PATH = Path("events.csv")
DEFAULT_README_PATH = Path("README.md")


@dataclass
class ProcessResult:
    """Outcome of processing a single event row."""

    alias: str
    status: str
    changed: bool
    message: str = ""
    changed_fields: tuple[str, ...] = ()


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point executed by ``python -m src.main``."""
    args = _parse_args(argv)
    _configure_logging(args.log_level)

    events_path = Path(args.events)
    readme_path = Path(args.readme)

    try:
        run_pipeline(events_path, readme_path, dry_run=args.dry_run)
    except CSVSchemaError as exc:
        LOGGER.error("CSVスキーマエラー: %s", exc)
        LOGGER.debug("CSV schema error details", exc_info=True)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        LOGGER.error("致命的エラー: %s", exc)
        LOGGER.debug("Unhandled exception details", exc_info=True)
        sys.exit(1)


def run_pipeline(
    events_path: Path,
    readme_path: Path,
    *,
    dry_run: bool,
) -> None:
    """Execute the end-to-end update pipeline."""
    rows = load_events(events_path)
    if not rows:
        LOGGER.warning("events.csv に処理対象の行がありません。")

    timestamp = now_jst_isoformat()
    updated = False
    success_aliases: list[str] = []
    error_results: list[ProcessResult] = []
    skipped_aliases: list[str] = []

    for row in rows:
        alias = row.get("alias", "")
        LOGGER.info("処理開始: %s", alias or "<unknown>")
        result = _process_row(row, timestamp)

        if result.status == "skipped":
            LOGGER.info("スキップ: %s (URL未設定)", result.alias)
            skipped_aliases.append(result.alias)
            continue

        if result.status == "success":
            if result.changed:
                updated = True
                success_aliases.append(result.alias)
            LOGGER.info("更新成功: %s - %s", result.alias, result.message or "差分なし")
            continue

        if result.status == "error":
            if result.changed:
                updated = True
            error_results.append(result)
            LOGGER.warning("更新失敗: %s - %s", result.alias, result.message)
            continue

        LOGGER.warning("未定義のステータス: %s - %s", result.status, result.alias)

    LOGGER.info(
        "処理結果: 成功 %d 件 / 失敗 %d 件 / スキップ %d 件",
        len(success_aliases),
        len(error_results),
        len(skipped_aliases),
    )

    if error_results:
        details = "; ".join(f"{res.alias}: {res.message}" for res in error_results)
        LOGGER.debug("失敗詳細: %s", details)

    if dry_run:
        LOGGER.info("ドライランのためファイル更新は行いません。")
        return

    if not updated:
        LOGGER.info("差分がないためファイル更新をスキップします。")
        return

    if save_events(events_path, rows):
        LOGGER.info("events.csv を更新しました。")
    else:
        LOGGER.info("events.csv の内容に変更はありませんでした。")

    latest_rows = load_events(events_path)
    table_text = render_table(latest_rows, highlight_timestamp=timestamp)

    if update_readme_table(readme_path, table_text):
        LOGGER.info("README.md を更新しました。")
    else:
        LOGGER.info("README.md に変更はありませんでした。")


def _process_row(row: dict[str, str], timestamp: str) -> ProcessResult:
    alias = row.get("alias", "")
    url = (row.get("url") or "").strip()
    if not url:
        return ProcessResult(alias=alias, status="skipped", changed=False, message="URL未設定")

    current_values = {field: row.get(field, "") for field in UPDATE_FIELDS}

    try:
        html = fetch_html(url)
        text = extract_main_text(html)
        reference_name = current_values.get("event_name") or alias
        multi_events = extract_multiple_events(
            text,
            alias=alias,
            reference_name=reference_name,
            max_events=5,
        )
        if multi_events:
            extracted = _select_best_event(alias, reference_name, multi_events)
        else:
            extracted = extract_event_info(
                text,
                alias=alias,
                reference_name=reference_name,
            )

        if _all_unknown(extracted):
            message = "情報取得できず (不明)"
            changed = apply_error_update(row, message, timestamp=timestamp)
            return ProcessResult(alias=alias, status="error", changed=changed, message=message)

        normalized_updates = {field: extracted[field] for field in UPDATE_FIELDS}
        changed_fields = tuple(
            field for field in UPDATE_FIELDS if current_values.get(field) != normalized_updates[field]
        )
        changed = apply_success_update(row, normalized_updates, timestamp=timestamp)

        if changed_fields:
            message = f"変更: {', '.join(changed_fields)}"
        elif changed:
            message = "commentリセット"
        else:
            message = "差分なし"

        return ProcessResult(
            alias=alias,
            status="success",
            changed=changed,
            message=message,
            changed_fields=changed_fields,
        )
    except requests.RequestException as exc:
        message = f"HTTPエラー: {exc}"
        changed = apply_error_update(row, message, timestamp=timestamp)
        LOGGER.debug("HTTP error trace for %s", alias, exc_info=True)
        return ProcessResult(alias=alias, status="error", changed=changed, message=message)
    except GeminiError as exc:
        message = f"Geminiエラー: {exc}"
        changed = apply_error_update(row, message, timestamp=timestamp)
        LOGGER.debug("Gemini error trace for %s", alias, exc_info=True)
        return ProcessResult(alias=alias, status="error", changed=changed, message=message)
    except Exception as exc:  # noqa: BLE001
        message = f"処理失敗: {exc}"
        changed = apply_error_update(row, message, timestamp=timestamp)
        LOGGER.debug("Unexpected error trace for %s", alias, exc_info=True)
        return ProcessResult(alias=alias, status="error", changed=changed, message=message)


def _all_unknown(values: dict[str, str]) -> bool:
    return all(not (value or "").strip() or (value or "").strip() == "不明" for value in values.values())


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto Event Calendar updater.")
    parser.add_argument(
        "--events",
        default=str(DEFAULT_EVENTS_PATH),
        help="Path to events.csv (default: %(default)s)",
    )
    parser.add_argument(
        "--readme",
        default=str(DEFAULT_README_PATH),
        help="Path to README.md (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing events.csv or README.md.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: %(default)s).",
    )
    return parser.parse_args(argv)


def _configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    logging.captureWarnings(True)


def _select_best_event(
    alias: str,
    reference_name: str,
    events: list[dict[str, str]],
) -> dict[str, str]:
    """Select the event whose name best matches the alias/reference."""
    candidates = [alias, reference_name, alias.replace("_", " ")]
    normalized_candidates = [c.lower() for c in candidates if c]

    def score(event: dict[str, str]) -> float:
        name = (event.get("event_name") or "").lower()
        if not name or name == "不明":
            return 0.0
        ratios = [
            SequenceMatcher(None, candidate, name).ratio()
            for candidate in normalized_candidates
        ]
        extra = 0.1 if any(candidate in name for candidate in normalized_candidates if candidate) else 0.0
        return max(ratios, default=0.0) + extra

    best_event = max(events, key=score)
    return best_event


if __name__ == "__main__":
    main()
