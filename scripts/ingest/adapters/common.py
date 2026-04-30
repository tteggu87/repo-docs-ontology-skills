from __future__ import annotations
from dataclasses import dataclass
import hashlib
from pathlib import Path

@dataclass
class ParsedSource:
    document: dict
    units: list[dict]


def stable_unit_id(document_id: str, unit_kind: str, sequence: int, text: str) -> str:
    key = f"{document_id}|{unit_kind}|{sequence}|{text.strip()[:120]}"
    return "unit-" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def file_document_id(raw_path: str) -> str:
    return "doc-" + hashlib.sha1(raw_path.encode("utf-8")).hexdigest()[:16]


def file_content_hash(path: Path) -> str:
    return "sha256-" + hashlib.sha256(path.read_bytes()).hexdigest()


def source_version_id(document_id: str, content_hash: str) -> str:
    return "srcver-" + hashlib.sha1(f"{document_id}|{content_hash}".encode("utf-8")).hexdigest()[:16]
