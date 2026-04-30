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


def file_document_id(path: Path) -> str:
    return "doc-" + hashlib.sha1(path.as_posix().encode("utf-8")).hexdigest()[:16]
