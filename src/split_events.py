"""Utility script to fan out multi-event pages into individual CSV rows."""

from __future__ import annotations

import argparse
import logging
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Iterable, MutableMapping, Sequence

import requests

from .ai_client import GeminiError, extract_multiple_events
from .csv_io import (
    UPDATE_FIELDS,
    apply_error_update,
    apply_success_update,
    load_events,
    save_events,
)
from .scrape import extract_main_text, fetch_html
from .utils import now_jst_isoformat

LOGGER = logging.getLogger(__name__)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    _configure_logging(args.log_level)

    events_path = Path(args.events)
    rows = load_events(events_path)
    existing_aliases = Counter(row["alias"] for row in rows)

    updated_rows: list[MutableMapping[str, str]] = []
    total_new_rows = 0
    total_split_sources = 0

    for row in rows:
        alias = row["alias"]
        url = (row.get("url") or "").strip()
        reference_name = row.get("event_name") or alias

        if not url:
            LOGGER.info("URLなしのためスキップ: %s", alias)
            updated_rows.append(row)
            continue

        try:
            html = fetch_html(url)
            text = extract_main_text(html)
            events = extract_multiple_events(
                text,
                alias=alias,
                reference_name=reference_name,
                max_events=args.max_events,
                model=args.model,
            )
        except requests.RequestException as exc:
            LOGGER.warning("HTTP取得失敗: %s - %s", alias, exc)
            apply_error_update(row, f"HTTP取得失敗: {exc}", timestamp=now_jst_isoformat())
            updated_rows.append(row)
            continue
        except GeminiError as exc:
            LOGGER.warning("Gemini抽出失敗: %s - %s", alias, exc)
            apply_error_update(row, f"Gemini抽出失敗: {exc}", timestamp=now_jst_isoformat())
            updated_rows.append(row)
            continue
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("予期せぬ失敗: %s - %s", alias, exc)
            apply_error_update(row, f"処理失敗: {exc}", timestamp=now_jst_isoformat())
            updated_rows.append(row)
            continue

        if not events:
            LOGGER.info("複数イベントなし: %s", alias)
            updated_rows.append(row)
            continue

        splits_created = 0
        LOGGER.info("%s で %s 件のイベントを検出", alias, len(events))

        primary_event = events[0]
        apply_success_update(row, primary_event, timestamp=now_jst_isoformat())
        updated_rows.append(row)

        for index, extra_event in enumerate(events[1:], start=1):
            new_alias = _generate_alias(alias, existing_aliases, index)
            new_row = deepcopy(row)
            new_row["alias"] = new_alias
            apply_success_update(new_row, extra_event, timestamp=now_jst_isoformat())
            updated_rows.append(new_row)
            splits_created += 1
            existing_aliases[new_alias] += 1
            LOGGER.debug("追加イベント: %s -> %s", alias, new_alias)

        if splits_created:
            total_split_sources += 1
            total_new_rows += splits_created

    LOGGER.info(
        "複数イベント分裂: ソース %s 件 / 新規行 %s 件",
        total_split_sources,
        total_new_rows,
    )

    if args.dry_run:
        LOGGER.info("ドライランのため events.csv は書き込みません。")
        return

    if save_events(events_path, updated_rows):
        LOGGER.info("events.csv を更新しました。")
    else:
        LOGGER.info("events.csv に変更はありませんでした。")


def _generate_alias(base: str, counter: Counter[str], start_index: int) -> str:
    if counter[base] == 0:
        return base

    suffix = max(start_index, 1)
    while True:
        candidate = f"{base}_{suffix:02d}"
        if counter[candidate] == 0:
            return candidate
        suffix += 1


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split multi-event pages into individual CSV rows.",
    )
    parser.add_argument(
        "--events",
        default="events.csv",
        help="Path to events.csv (default: %(default)s)",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=10,
        help="Maximum number of events to extract per page (default: %(default)s).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override Gemini model name.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process pages but do not write the CSV.",
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
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


if __name__ == "__main__":
    main()
