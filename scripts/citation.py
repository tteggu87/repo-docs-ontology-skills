from __future__ import annotations

import json
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _source_page_by_document(root: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for path in (root / "wiki" / "sources").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("document_id:"):
                out[line.split(":", 1)[1].strip().strip('"')] = path
                break
    return out


def make_citation(root: Path, unit_id: str) -> dict:
    units = {row.get("unit_id"): row for row in load_jsonl(root / "warehouse/jsonl/content_units.jsonl")}
    docs = {row.get("document_id"): row for row in load_jsonl(root / "warehouse/jsonl/documents.jsonl")}
    unit = units.get(unit_id)
    warnings: list[str] = []
    if not unit:
        return {"ok": False, "citation": "", "warnings": [f"content unit not found: {unit_id}"]}

    doc = docs.get(unit.get("document_id"), {})
    source_pages = _source_page_by_document(root)
    source_page = source_pages.get(unit.get("document_id"))
    if source_page:
        source_ref = f"[[{source_page.stem}]]"
    else:
        source_ref = f"`{doc.get('raw_path') or unit.get('document_id')}`"
        warnings.append("source page not found for document_id")

    heading = unit.get("heading") or "untitled section"
    line_start = unit.get("line_start")
    line_end = unit.get("line_end")
    citation = f"{source_ref}, `{unit_id}`, section “{heading}”, lines {line_start}-{line_end}"
    return {"ok": True, "citation": citation, "warnings": warnings, "unit": unit, "document": doc}
