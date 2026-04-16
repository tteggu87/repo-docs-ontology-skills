#!/usr/bin/env python3
"""Helpers for minimal cumulative-export-aware ingest."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_family_id_for_raw_path(raw_path: str) -> str:
    normalized = unicodedata.normalize("NFC", raw_path)
    if "KakaoTalk_Chat_" in normalized and "에이전트코리아" in normalized:
        return "family-kakao-agent-korea-chat"
    return f"family-{sha256_text(normalized)[:12]}"


def source_kind_for_raw_path(raw_path: str) -> str:
    if "KakaoTalk_Chat_" in raw_path:
        return "kakao_chat_export"
    return "generic_export"


def export_version_id_for_document(document: dict[str, Any], content_hash: str) -> str:
    family_id = document["source_family_id"]
    return f"export-{family_id}-{content_hash[:12]}"


def incremental_status_page_for_family(source_family_id: str) -> str:
    return f"source-{source_family_id.removeprefix('family-')}-incremental-status"


def occurrence_key(message: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(message.get("event_type") or "message"),
        str(message.get("timestamp") or ""),
        str(message.get("speaker_name") or ""),
        str(message.get("text") or ""),
        str(message.get("inferred_date") or ""),
    )


def assign_occurrence_indexes(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str, str, str, str], int] = defaultdict(int)
    for message in messages:
        key = occurrence_key(message)
        seen[key] += 1
        message["occurrence_index"] = seen[key]
    return messages


def message_fingerprint(message: dict[str, Any]) -> str:
    event_type, timestamp, speaker, text, inferred_date = occurrence_key(message)
    occurrence_index = str(message.get("occurrence_index") or 1)
    basis = "\x1f".join([event_type, timestamp, speaker, text, inferred_date, occurrence_index])
    return f"msgfp-{sha256_text(basis)[:24]}"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
