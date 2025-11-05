"""Gemini API client helpers for extracting event metadata."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Mapping, Sequence

import requests

from .utils import request_with_retries

LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-pro"
API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
API_TIMEOUT = 60
API_MAX_RETRIES = 3
PROMPT_TEMPLATE = """あなたは展示会・イベント情報の抽出アシスタントです。

ターゲットとなるイベント識別情報は以下です。
- alias: {alias}
- 現在CSVに記録されている名称: {reference_name}

ページ内に複数イベントが記載されている場合は、上記 alias/既存名称に最も一致する最新開催のイベントのみを選択してください。
該当イベントが見つからない場合は各フィールドを "不明" として構いません。

必要なフィールド:
- event_name
- event_date (できる限り YYYY-MM-DD。複数日程の場合は範囲を明示。例: 2025-12-07 または 2025-12-07/2025-12-08)
- location
- deadline (応募締切がなければ "不明")
- status (例: 応募受付中, 開催予定, 開催終了 等)

出力は必ず JSON 形式で、キーは英語の event_name, event_date, location, deadline, status の5つのみを使用してください。
本文:
{body}
"""
MULTI_PROMPT_TEMPLATE = """あなたは展示会・イベント情報の抽出アシスタントです。

ターゲットとなるイベント識別情報は以下です。
- alias: {alias}
- 現在CSVに記録されている名称: {reference_name}

ページ内に複数イベントが記載されている場合は、上記 alias/既存名称と関連が高いイベントを最大{max_events}件まで抽出し、開催日が新しい順に並べてください。
見つからない場合は空の配列を返してください。

各イベントで抽出する項目:
- event_name
- event_date (可能な限り YYYY-MM-DD。複数日程は範囲表記。例: 2025-12-07/2025-12-08)
- location
- deadline (不明なら \"不明\")
- status (例: 応募受付中, 開催予定 等)

出力は必ず JSON 配列で、各要素は event_name, event_date, location, deadline, status の5フィールドのみを持つオブジェクトにしてください。
本文:
{body}
"""
EXPECTED_FIELDS = (
    "event_name",
    "event_date",
    "location",
    "deadline",
    "status",
)
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "event_name": ("event_name", "eventName", "name", "タイトル", "イベント名"),
    "event_date": ("event_date", "eventDate", "開催日", "date"),
    "location": ("location", "開催場所", "会場", "venue"),
    "deadline": ("deadline", "締切", "締め切り", "応募締切", "応募締め切り"),
    "status": ("status", "状況", "ステータス", "応募状況"),
}
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "event_name": {"type": "string"},
        "event_date": {"type": "string"},
        "location": {"type": "string"},
        "deadline": {"type": "string"},
        "status": {"type": "string"},
    },
    "required": list(EXPECTED_FIELDS),
}
MULTI_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "event_name": {"type": "string"},
            "event_date": {"type": "string"},
            "location": {"type": "string"},
            "deadline": {"type": "string"},
            "status": {"type": "string"},
        },
        "required": list(EXPECTED_FIELDS),
    },
}


class GeminiError(RuntimeError):
    """Raised when the Gemini API call fails or returns malformed data."""


def extract_event_info(
    text: str,
    *,
    model: str | None = None,
    alias: str | None = None,
    reference_name: str | None = None,
) -> dict[str, str]:
    """Call Gemini to extract event information from unstructured text."""
    if not text:
        return {field: "不明" for field in EXPECTED_FIELDS}

    resolved_model = model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL
    prompt_text = PROMPT_TEMPLATE.format(
        body=text,
        alias=alias or "不明",
        reference_name=reference_name or "不明",
    )
    response_payload = _call_gemini_api(
        text,
        model=resolved_model,
        alias=alias or "",
        reference_name=reference_name or "",
        prompt_text=prompt_text,
        response_schema=RESPONSE_SCHEMA,
    )
    message_text = _extract_text_from_response(response_payload)
    data = _parse_first_json_block(message_text, require_mapping=True)
    return _normalize_fields(data)


def _call_gemini_api(
    text: str,
    *,
    model: str | None = None,
    alias: str = "",
    reference_name: str = "",
    prompt_text: str | None = None,
    response_schema: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    resolved_model = model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("GEMINI_API_KEY is not set in environment variables.")

    url = f"{API_URL_TEMPLATE.format(model=resolved_model)}?key={api_key}"
    prompt = prompt_text or PROMPT_TEMPLATE.format(
        body=text,
        alias=alias or "不明",
        reference_name=reference_name or "不明",
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": response_schema or RESPONSE_SCHEMA,
        },
    }

    try:
        response = request_with_retries(
            url,
            method="POST",
            timeout=API_TIMEOUT,
            max_retries=API_MAX_RETRIES,
            headers={"Content-Type": "application/json; charset=utf-8"},
            json=payload,
        )
    except requests.RequestException as exc:
        raise GeminiError(f"Gemini API request failed: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise GeminiError("Gemini API returned non-JSON response.") from exc


def _extract_text_from_response(payload: Mapping[str, Any]) -> str:
    try:
        candidates = payload["candidates"]
        first_candidate = candidates[0]
        parts = first_candidate["content"]["parts"]
        return "".join(part.get("text", "") for part in parts if isinstance(part, dict))
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiError("Gemini API response missing expected fields.") from exc


def _parse_first_json_block(
    text: str,
    *,
    require_mapping: bool = True,
) -> Any:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char not in "{[":
            continue
        try:
            parsed, _ = decoder.raw_decode(text[index:])
            if require_mapping:
                if isinstance(parsed, Mapping):
                    return parsed
                if isinstance(parsed, list):
                    for item in parsed:
                        if isinstance(item, Mapping):
                            return item
                    continue
                continue
            return parsed
        except ValueError:
            continue
    raise GeminiError("No JSON block found in Gemini response.")


def _normalize_fields(data: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(data, Mapping):
        raise GeminiError("Gemini response JSON is not an object.")

    normalized_map: dict[str, Any] = {}
    for key, value in data.items():
        normalized_key = _normalize_key(key)
        if normalized_key and normalized_key not in normalized_map:
            normalized_map[normalized_key] = value
        if key not in normalized_map:
            normalized_map[key] = value

    normalized: dict[str, str] = {}
    for field in EXPECTED_FIELDS:
        value = None
        for alias in FIELD_ALIASES.get(field, (field,)):
            normalized_alias = _normalize_key(alias)
            if normalized_alias in normalized_map:
                value = normalized_map[normalized_alias]
                break
            if alias in normalized_map:
                value = normalized_map[alias]
                break
        if value is None:
            value = normalized_map.get(field, "不明")
        if value in (None, ""):
            value = "不明"
        if not isinstance(value, str):
            value = str(value)
        normalized[field] = value
    return normalized


def _normalize_key(key: str) -> str:
    if not isinstance(key, str):
        return ""
    return key.strip().lower().replace("-", "_")


def extract_multiple_events(
    text: str,
    *,
    alias: str,
    reference_name: str,
    max_events: int = 10,
    model: str | None = None,
) -> list[dict[str, str]]:
    """Extract up to ``max_events`` events related to ``alias`` from the text."""
    if not text:
        return []

    resolved_model = model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL
    prompt_text = MULTI_PROMPT_TEMPLATE.format(
        body=text,
        alias=alias or "不明",
        reference_name=reference_name or "不明",
        max_events=max_events,
    )
    response_payload = _call_gemini_api(
        text,
        model=resolved_model,
        alias=alias or "",
        reference_name=reference_name or "",
        prompt_text=prompt_text,
        response_schema={**MULTI_RESPONSE_SCHEMA, "maxItems": max_events},
    )
    message_text = _extract_text_from_response(response_payload)
    parsed = _parse_first_json_block(message_text, require_mapping=False)

    items: Sequence[Mapping[str, Any]]
    if isinstance(parsed, Mapping):
        maybe_list = parsed.get("events")
        if isinstance(maybe_list, list):
            items = [item for item in maybe_list if isinstance(item, Mapping)]
        else:
            items = [parsed]
    elif isinstance(parsed, list):
        items = [item for item in parsed if isinstance(item, Mapping)]
    else:
        raise GeminiError("Gemini multi-event response is not a JSON array or object.")

    normalized = [_normalize_fields(item) for item in items]
    return normalized[:max_events]
