#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = ROOT / "wiki"
META_DIR = WIKI_DIR / "_meta"

REVIEW_MARKERS = {
    "uncertainty": ["uncertain", "unclear", "unknown", "open question", "needs review", "불확실", "미정"],
    "contradiction": ["contradiction", "contradicts", "conflict", "inconsistent", "disputed", "모순", "충돌"],
}


def today() -> str:
    return date.today().isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"_invalid_jsonl": line[:200]})
    return rows


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def wikilinks(content: str) -> list[str]:
    return sorted(set(re.findall(r"\[\[([^\]|#]+)", content)))


def frontmatter_value(content: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*\"?(.+?)\"?\s*$", content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def title_for(path: Path, content: str) -> str:
    return frontmatter_value(content, "title") or path.stem.replace("-", " ").title()


def iter_pages(root: Path) -> list[Path]:
    wiki = root / "wiki"
    return sorted(path for path in wiki.rglob("*.md") if path.is_file())


def build_graph(root: Path) -> dict[str, Any]:
    wiki = root / "wiki"
    records: dict[str, dict[str, Any]] = {}
    for path in iter_pages(root):
        rel = path.relative_to(root).as_posix()
        section = path.relative_to(wiki).parts[0]
        content = read_text(path)
        records[path.stem] = {
            "stem": path.stem,
            "path": rel,
            "section": section,
            "title": title_for(path, content),
            "updated": frontmatter_value(content, "updated") or frontmatter_value(content, "created"),
            "outgoing": wikilinks(content),
            "backlinks": [],
            "review_markers": [],
        }

    known = set(records)
    for record in records.values():
        record["broken_links"] = [link for link in record["outgoing"] if link not in known]
        record["outgoing_existing"] = [link for link in record["outgoing"] if link in known]
        for link in record["outgoing_existing"]:
            records[link]["backlinks"].append(record["stem"])

    for record in records.values():
        content = read_text(root / record["path"]).lower()
        markers = []
        for kind, words in REVIEW_MARKERS.items():
            if any(word in content for word in words):
                markers.append(kind)
        record["review_markers"] = sorted(set(markers))
        record["backlinks"] = sorted(set(record["backlinks"]))

    return {"pages": sorted(records.values(), key=lambda row: (row["section"], row["title"].lower()))}


def _frontmatter(title: str) -> list[str]:
    return [
        "---",
        f'title: "{title}"',
        "type: meta",
        "status: active",
        f"created: {today()}",
        f"updated: {today()}",
        "---",
        "",
    ]


def render_moc(graph: dict[str, Any]) -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for page in graph["pages"]:
        if page["section"] == "_meta":
            continue
        grouped[page["section"]].append(page)
    lines = _frontmatter("Map of Content") + ["# Map of Content", ""]
    for section in sorted(grouped):
        lines.extend([f"## {section.title()}", ""])
        for page in grouped[section]:
            lines.append(f"- [[{page['stem']}]] — backlinks: {len(page['backlinks'])}, outgoing: {len(page['outgoing_existing'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_link_map(graph: dict[str, Any]) -> str:
    lines = _frontmatter("Link Map") + ["# Link Map", ""]
    for page in graph["pages"]:
        lines.append(f"## [[{page['stem']}]]")
        lines.append("")
        lines.append(f"- Path: `{page['path']}`")
        lines.append(f"- Section: `{page['section']}`")
        lines.append(f"- Backlinks: {', '.join(f'[[{stem}]]' for stem in page['backlinks']) or 'None'}")
        lines.append(f"- Outgoing: {', '.join(f'[[{stem}]]' for stem in page['outgoing_existing']) or 'None'}")
        if page["broken_links"]:
            lines.append(f"- Broken links: {', '.join(page['broken_links'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_review(graph: dict[str, Any], kind: str) -> str:
    title = {
        "orphan": "Orphan Review",
        "stale": "Stale Review",
        "contradiction": "Contradiction Review",
    }[kind]
    lines = _frontmatter(title) + [f"# {title}", ""]
    pages = [page for page in graph["pages"] if page["section"] != "_meta"]
    if kind == "orphan":
        selected = [page for page in pages if not page["backlinks"]]
        lines.append("Pages with no inbound wiki links. These may need MOC placement, backlinks, or archival review.")
    elif kind == "stale":
        selected = [page for page in pages if not page.get("updated") or page.get("updated", "") < "2026-04-01"]
        lines.append("Pages with missing or older updated dates. This is a review queue, not semantic truth.")
    else:
        selected = [page for page in pages if "contradiction" in page["review_markers"] or "uncertainty" in page["review_markers"]]
        lines.append("Pages with contradiction/uncertainty markers. LLM review should inspect the cited sources before resolving.")
    lines.append("")
    for page in selected:
        lines.append(f"- [[{page['stem']}]] — section: `{page['section']}`, backlinks: {len(page['backlinks'])}, markers: {', '.join(page['review_markers']) or 'none'}")
    if not selected:
        lines.append("- No candidates.")
    return "\n".join(lines).rstrip() + "\n"


def render_source_coverage(graph: dict[str, Any], root: Path) -> str:
    documents = read_jsonl(root / "warehouse/jsonl/documents.jsonl")
    source_versions = read_jsonl(root / "warehouse/jsonl/source_versions.jsonl")
    content_units = read_jsonl(root / "warehouse/jsonl/content_units.jsonl")
    versions_by_document: dict[str, list[dict[str, Any]]] = defaultdict(list)
    units_by_document: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_pages_by_document: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in source_versions:
        document_id = str(row.get("document_id") or "")
        if document_id:
            versions_by_document[document_id].append(row)
    for row in content_units:
        document_id = str(row.get("document_id") or "")
        if document_id:
            units_by_document[document_id].append(row)
    for page in graph["pages"]:
        if page["section"] != "sources":
            continue
        content = read_text(root / page["path"])
        document_id = frontmatter_value(content, "document_id")
        if document_id:
            source_pages_by_document[document_id].append(page)

    lines = _frontmatter("Source Coverage") + [
        "# Source Coverage",
        "",
        "This is a mechanical coverage surface for LLM compile/query workflows.",
        "It reports whether canonical documents have projected source pages, source versions, and citation anchors.",
        "It does not make semantic claims.",
        "",
        "## Summary",
        "",
        f"- Documents: {len(documents)}",
        f"- Source versions: {len(source_versions)}",
        f"- Content units: {len(content_units)}",
        f"- Documents with source pages: {sum(1 for row in documents if source_pages_by_document.get(str(row.get('document_id') or '')))}",
        "",
        "## Documents",
        "",
    ]
    if not documents:
        lines.append("- No documents registered yet.")
    for row in documents:
        document_id = str(row.get("document_id") or "unknown")
        raw_path = str(row.get("raw_path") or "unknown")
        pages = source_pages_by_document.get(document_id, [])
        versions = versions_by_document.get(document_id, [])
        units = units_by_document.get(document_id, [])
        page_links = ", ".join(f"[[{page['stem']}]]" for page in pages) or "missing"
        latest_version = str(versions[-1].get("version_id") or versions[-1].get("source_version_id") or "present") if versions else "missing"
        lines.append(f"### `{document_id}`")
        lines.append("")
        lines.append(f"- Raw path: `{raw_path}`")
        lines.append(f"- Source page(s): {page_links}")
        lines.append(f"- Source version: `{latest_version}`")
        lines.append(f"- Citation anchors/content units: {len(units)}")
        if not pages:
            lines.append("- Review: missing source page projection.")
        if not versions:
            lines.append("- Review: missing source version record.")
        if not units:
            lines.append("- Review: missing content-unit citation anchors.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_navigation_pages(root: Path) -> dict[str, Any]:
    graph = build_graph(root)
    outputs = {
        "wiki/_meta/moc.md": render_moc(graph),
        "wiki/_meta/link-map.md": render_link_map(graph),
        "wiki/_meta/orphan-review.md": render_review(graph, "orphan"),
        "wiki/_meta/stale-review.md": render_review(graph, "stale"),
        "wiki/_meta/contradiction-review.md": render_review(graph, "contradiction"),
        "wiki/_meta/source-coverage.md": render_source_coverage(graph, root),
    }
    changed: list[str] = []
    for rel, content in outputs.items():
        path = root / rel
        old = read_text(path) if path.exists() else None
        if old != content:
            write_text(path, content)
            changed.append(rel)
    return {"status": "ok", "changed_paths": changed, "page_count": len(graph["pages"])}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build wiki graph navigation pages for LLM-first reasoning.")
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--write", action="store_true", help="Write wiki/_meta navigation pages.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.write:
        result = write_navigation_pages(root)
    else:
        result = build_graph(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
