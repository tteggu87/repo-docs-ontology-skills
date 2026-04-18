#!/usr/bin/env python3
"""Benchmark-only ontology ingest pipeline for DocTology source pages.

This script is intentionally sandbox-first. By default it refuses to write into the
main DocTology repository root unless `--allow-main-repo` is passed explicitly.

Use `scripts/ontology_ingest.py` for the raw-first production-oriented ingest path.
This benchmark harness remains for architecture/performance comparison only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    from incremental_support import sha256_file, sha256_text, write_jsonl
    from workbench.common import extract_summary, parse_frontmatter, read_text, wikilinks
except ModuleNotFoundError:
    from scripts.incremental_support import sha256_file, sha256_text, write_jsonl
    from scripts.workbench.common import extract_summary, parse_frontmatter, read_text, wikilinks

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_NAMES = [
    "source_versions",
    "documents",
    "messages",
    "entities",
    "claims",
    "claim_evidence",
    "segments",
    "derived_edges",
]
MIN_SEGMENT_CHARS = 16


def source_pages_dir(project_root: Path, wiki_dir: Path | None = None) -> Path:
    return (wiki_dir or (project_root / "wiki")) / "sources"


def wiki_root_dir(project_root: Path, wiki_dir: Path | None = None) -> Path:
    return wiki_dir or (project_root / "wiki")


def warehouse_jsonl_dir(project_root: Path) -> Path:
    return project_root / "warehouse" / "jsonl"


def stringify_dateish(value: Any) -> str:
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if value is None:
        return ""
    return str(value)


def today_iso() -> str:
    return dt.date.today().isoformat()


def assert_safe_root(project_root: Path, *, allow_main_repo: bool = False) -> None:
    if allow_main_repo:
        return
    if project_root.resolve() == REPO_ROOT.resolve():
        raise ValueError(
            "Refusing to run ontology benchmark ingest against the main DocTology repo root without allow_main_repo=True."
        )


def assert_inside_repo(project_root: Path, candidate: Path) -> None:
    resolved_root = project_root.resolve()
    resolved_candidate = candidate.resolve()
    if resolved_candidate != resolved_root and resolved_root not in resolved_candidate.parents:
        raise ValueError(f"Resolved path escapes project root: {candidate}")



def stable_document_id(stem: str) -> str:
    return f"document:{stem}"


def stable_source_family_id(stem: str) -> str:
    return f"family-source-page:{stem}"


def stable_export_version_id(stem: str, content_hash: str) -> str:
    return f"export:{stem}:{content_hash[:12]}"


def stable_entity_id(stem: str) -> str:
    return f"entity:{stem}"


def stable_segment_id(stem: str, position: int) -> str:
    return f"segment:{stem}:{position}"


def stable_claim_id(stem: str, claim_text: str) -> str:
    return f"claim:{stem}:{sha256_text(claim_text)[:12]}"


def singular_section(section: str) -> str:
    return section[:-1] if section.endswith("s") else section


def iter_wiki_pages(project_root: Path, wiki_dir: Path | None = None) -> list[Path]:
    wiki_root = wiki_root_dir(project_root, wiki_dir)
    if not wiki_root.exists():
        return []
    return sorted(
        path
        for path in wiki_root.rglob("*.md")
        if path.is_file() and "_meta" not in path.relative_to(wiki_root).parts
    )


def iter_source_pages(project_root: Path, wiki_dir: Path | None = None, limit_sources: int | None = None) -> list[Path]:
    base = source_pages_dir(project_root, wiki_dir)
    if not base.exists():
        return []
    pages = sorted(path for path in base.glob("*.md") if path.is_file())
    if limit_sources is not None:
        return pages[: max(0, limit_sources)]
    return pages


def resolve_raw_path(project_root: Path, raw_path_value: str | None) -> tuple[str, str | None]:
    if not raw_path_value:
        return "", None
    raw_path = raw_path_value.strip()
    if not raw_path:
        return "", None
    candidate = (project_root / raw_path).resolve()
    assert_inside_repo(project_root, candidate)
    if candidate.exists():
        return raw_path, sha256_file(candidate)
    return raw_path, None


def split_markdown_entries(body: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    current_section = "root"
    paragraph_buffer: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_buffer
        if paragraph_buffer:
            text = " ".join(part.strip() for part in paragraph_buffer if part.strip()).strip()
            if text:
                entries.append((current_section, text))
            paragraph_buffer = []

    for raw_line in body.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("#"):
            flush_paragraph()
            current_section = stripped.lstrip("#").strip().lower() or "root"
            continue
        if not stripped:
            flush_paragraph()
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            entries.append((current_section, stripped[2:].strip()))
            continue
        paragraph_buffer.append(stripped)

    flush_paragraph()
    return entries


def extract_segments_from_body(body: str) -> list[str]:
    segments: list[str] = []
    for _, text in split_markdown_entries(body):
        normalized = text.strip()
        if len(normalized) < MIN_SEGMENT_CHARS:
            continue
        segments.append(normalized)
    return segments


def section_entries(body: str, section_name: str) -> list[str]:
    target = section_name.lower()
    return [text for section, text in split_markdown_entries(body) if section == target and len(text.strip()) >= MIN_SEGMENT_CHARS]


def collect_page_records(project_root: Path, wiki_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    wiki_root = wiki_root_dir(project_root, wiki_dir)
    for path in iter_wiki_pages(project_root, wiki_dir):
        text = read_text(path)
        frontmatter, body = parse_frontmatter(text)
        stem = path.stem
        if stem in records:
            raise ValueError(f"Duplicate wiki stem detected during ontology benchmark ingest: {stem}")
        records[stem] = {
            "stem": stem,
            "path": path,
            "title": str(frontmatter.get("title") or path.stem.replace("-", " ").title()),
            "frontmatter": frontmatter,
            "body": body,
            "summary": extract_summary(text),
            "section": path.relative_to(wiki_root).parts[0],
            "links": sorted(set(wikilinks(text))),
        }
    return records


def build_document_rows(
    project_root: Path,
    page_records: dict[str, dict[str, Any]],
    wiki_dir: Path | None = None,
    limit_sources: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    documents: list[dict[str, Any]] = []
    source_versions: list[dict[str, Any]] = []
    for path in iter_source_pages(project_root, wiki_dir=wiki_dir, limit_sources=limit_sources):
        record = page_records[path.stem]
        stem = record["stem"]
        frontmatter = record["frontmatter"]
        raw_path, raw_content_hash = resolve_raw_path(project_root, frontmatter.get("raw_path"))
        page_content_hash = sha256_text(read_text(path))
        content_hash = sha256_text("\x1f".join(filter(None, [raw_content_hash or "", page_content_hash])))
        source_family_id = stable_source_family_id(stem)
        export_version_id = stable_export_version_id(stem, content_hash)
        document_id = stable_document_id(stem)
        ingested_at = stringify_dateish(frontmatter.get("updated") or frontmatter.get("created"))
        message_count = len(extract_segments_from_body(record["body"]))
        document_row = {
            "document_id": document_id,
            "title": record["title"],
            "raw_path": raw_path,
            "source_page": stem,
            "incremental_status_page": stem,
            "source_family_id": source_family_id,
            "source_kind": "source_page_markdown",
            "content_hash": content_hash,
            "ingested_at": ingested_at,
            "export_version_id": export_version_id,
            "message_count": message_count,
            "benchmark_generated": True,
            "ingest_method": "ontology_benchmark_source_pages_v2",
        }
        source_version_row = {
            "export_version_id": export_version_id,
            "source_family_id": source_family_id,
            "document_id": document_id,
            "source_kind": "source_page_markdown",
            "raw_path": raw_path,
            "content_hash": content_hash,
            "ingested_at": ingested_at,
            "supersedes_export_version_id": None,
            "message_count": message_count,
            "new_message_count": message_count,
            "unchanged_message_count": 0,
            "affected_registry_paths": [
                "warehouse/jsonl/source_versions.jsonl",
                "warehouse/jsonl/documents.jsonl",
                "warehouse/jsonl/messages.jsonl",
                "warehouse/jsonl/entities.jsonl",
                "warehouse/jsonl/claims.jsonl",
                "warehouse/jsonl/claim_evidence.jsonl",
                "warehouse/jsonl/segments.jsonl",
                "warehouse/jsonl/derived_edges.jsonl",
            ],
            "affected_wiki_paths": [f"wiki/sources/{stem}.md"],
            "benchmark_generated": True,
            "ingest_method": "ontology_benchmark_source_pages_v2",
        }
        documents.append(document_row)
        source_versions.append(source_version_row)
    return documents, source_versions


def build_segments(page_records: dict[str, dict[str, Any]], documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    document_by_stem = {row["source_page"]: row for row in documents}
    segments: list[dict[str, Any]] = []
    for stem, document_row in document_by_stem.items():
        record = page_records[stem]
        segment_texts = extract_segments_from_body(record["body"])
        for position, text in enumerate(segment_texts, start=1):
            segments.append(
                {
                    "segment_id": stable_segment_id(stem, position),
                    "document_id": document_row["document_id"],
                    "source_document_id": document_row["document_id"],
                    "source_page": stem,
                    "text": text,
                    "position": position,
                    "benchmark_generated": True,
                    "ingest_method": "ontology_benchmark_source_pages_v2",
                }
            )
    return segments


def build_entities(
    page_records: dict[str, dict[str, Any]],
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entities_by_id: dict[str, dict[str, Any]] = {}
    document_by_stem = {row["source_page"]: row for row in documents}

    def add_or_update_entity(entity_id: str, row: dict[str, Any]) -> None:
        existing = entities_by_id.get(entity_id)
        if existing is None:
            entities_by_id[entity_id] = row
            return
        document_ids = set(existing.get("source_document_ids") or [])
        if row.get("source_document_id"):
            document_ids.add(str(row["source_document_id"]))
        existing["source_document_ids"] = sorted(document_ids)
        page_stems = set(existing.get("source_pages") or [])
        if row.get("source_page"):
            page_stems.add(str(row["source_page"]))
        existing["source_pages"] = sorted(page_stems)

    for stem, document_row in document_by_stem.items():
        record = page_records[stem]
        add_or_update_entity(
            stable_entity_id(stem),
            {
                "entity_id": stable_entity_id(stem),
                "label": record["title"],
                "type": singular_section(record["section"]),
                "aliases": [stem],
                "source_document_id": document_row["document_id"],
                "source_document_ids": [document_row["document_id"]],
                "source_page": stem,
                "source_pages": [stem],
                "benchmark_generated": True,
                "ingest_method": "ontology_benchmark_source_pages_v2",
            },
        )
        for link_stem in record["links"]:
            linked_record = page_records.get(link_stem)
            if not linked_record:
                continue
            entity_id = stable_entity_id(link_stem)
            add_or_update_entity(
                entity_id,
                {
                    "entity_id": entity_id,
                    "label": linked_record["title"],
                    "type": singular_section(linked_record["section"]),
                    "aliases": [link_stem],
                    "source_document_id": document_row["document_id"],
                    "source_document_ids": [document_row["document_id"]],
                    "source_page": stem,
                    "source_pages": [stem],
                    "benchmark_generated": True,
                    "ingest_method": "ontology_benchmark_source_pages_v2",
                },
            )
    return list(entities_by_id.values())


def claim_candidates_for_record(record: dict[str, Any]) -> list[str]:
    for section_name in ["important claims", "key facts", "summary"]:
        candidates = section_entries(record["body"], section_name)
        if candidates:
            return candidates
    fallback = record["summary"].strip()
    if fallback and len(fallback) >= MIN_SEGMENT_CHARS:
        return [fallback]
    return []


def build_claims_and_evidence(
    page_records: dict[str, dict[str, Any]],
    documents: list[dict[str, Any]],
    segments: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    document_by_stem = {row["source_page"]: row for row in documents}
    segments_by_stem: dict[str, list[dict[str, Any]]] = {}
    for row in segments:
        segments_by_stem.setdefault(str(row["source_page"]), []).append(row)

    claims: list[dict[str, Any]] = []
    claim_evidence: list[dict[str, Any]] = []

    for stem, document_row in document_by_stem.items():
        record = page_records[stem]
        linked_entities = [stable_entity_id(link) for link in record["links"] if link in page_records]
        subject_id = stable_entity_id(stem)
        candidates = claim_candidates_for_record(record)
        available_segments = segments_by_stem.get(stem, [])
        for index, claim_text in enumerate(candidates, start=1):
            claim_id = stable_claim_id(stem, claim_text)
            object_id = linked_entities[(index - 1) % len(linked_entities)] if linked_entities else None
            confidence = 0.72 if index % 2 else 0.84
            matching_segment = next((row for row in available_segments if claim_text in row["text"] or row["text"] in claim_text), None)
            if matching_segment is None and available_segments:
                matching_segment = available_segments[min(index - 1, len(available_segments) - 1)]
            claim_row = {
                "claim_id": claim_id,
                "claim_text": claim_text,
                "document_id": document_row["document_id"],
                "source_document_id": document_row["document_id"],
                "subject_id": subject_id,
                "predicate": "states",
                "object_id": object_id,
                "review_state": "needs_review",
                "confidence": float(confidence),
                "source_page": stem,
                "benchmark_generated": True,
                "ingest_method": "ontology_benchmark_source_pages_v2",
            }
            claims.append(claim_row)
            claim_evidence.append(
                {
                    "claim_id": claim_id,
                    "source_document_id": document_row["document_id"],
                    "document_id": document_row["document_id"],
                    "segment_id": matching_segment["segment_id"] if matching_segment else None,
                    "evidence_kind": "source_segment",
                    "benchmark_generated": True,
                    "ingest_method": "ontology_benchmark_source_pages_v2",
                }
            )
    return claims, claim_evidence


def build_derived_edges(
    page_records: dict[str, dict[str, Any]],
    documents: list[dict[str, Any]],
    claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    document_by_stem = {row["source_page"]: row for row in documents}
    edge_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def add_edge(source: str | None, target: str | None, label: str) -> None:
        if not source or not target:
            return
        key = (source, target, label)
        if key in seen:
            return
        seen.add(key)
        edge_rows.append(
            {
                "source": source,
                "target": target,
                "label": label,
                "benchmark_generated": True,
                "ingest_method": "ontology_benchmark_source_pages_v2",
            }
        )

    for claim in claims:
        add_edge(claim.get("document_id"), claim.get("claim_id"), "documents")
        add_edge(claim.get("claim_id"), claim.get("subject_id"), "about_subject")
        add_edge(claim.get("claim_id"), claim.get("object_id"), "about_object")

    for stem, document_row in document_by_stem.items():
        record = page_records[stem]
        for link in record["links"]:
            if link not in page_records:
                continue
            add_edge(stable_entity_id(stem), stable_entity_id(link), "related_to")
            add_edge(document_row["document_id"], stable_entity_id(link), "mentions")
    return edge_rows


def build_messages(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for row in segments:
        messages.append(
            {
                "message_id": row["segment_id"].replace("segment:", "message:", 1),
                "document_id": row["document_id"],
                "source_document_id": row["source_document_id"],
                "source_page": row["source_page"],
                "event_type": "note_segment",
                "text": row["text"],
                "sequence": row["position"],
                "timestamp": None,
                "benchmark_generated": True,
                "ingest_method": "ontology_benchmark_source_pages_v2",
            }
        )
    return messages


def write_registries(project_root: Path, registries: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    warehouse_dir = warehouse_jsonl_dir(project_root)
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    output_paths: dict[str, str] = {}
    for name in REGISTRY_NAMES:
        rows = registries.get(name, [])
        path = warehouse_dir / f"{name}.jsonl"
        write_jsonl(path, rows)
        output_paths[name] = str(path.relative_to(project_root))
    return output_paths


def ingest_ontology_benchmark(
    project_root_arg: str | Path,
    *,
    wiki_dir: str | Path | None = None,
    raw_dir: str | Path | None = None,  # reserved for future tranche
    clean: bool = False,
    limit_sources: int | None = None,
    allow_main_repo: bool = False,
    build_graph_projection: bool = False,
) -> dict[str, Any]:
    project_root = Path(project_root_arg).resolve()
    assert_safe_root(project_root, allow_main_repo=allow_main_repo)
    resolved_wiki_dir = Path(wiki_dir).resolve() if wiki_dir else None
    _ = Path(raw_dir).resolve() if raw_dir else None
    warehouse_dir = warehouse_jsonl_dir(project_root)
    warehouse_dir.mkdir(parents=True, exist_ok=True)

    if clean:
        for name in REGISTRY_NAMES:
            path = warehouse_dir / f"{name}.jsonl"
            if path.exists():
                path.unlink()

    page_records = collect_page_records(project_root, resolved_wiki_dir)
    documents, source_versions = build_document_rows(
        project_root,
        page_records,
        wiki_dir=resolved_wiki_dir,
        limit_sources=limit_sources,
    )
    segments = build_segments(page_records, documents)
    entities = build_entities(page_records, documents)
    claims, claim_evidence = build_claims_and_evidence(page_records, documents, segments)
    derived_edges = build_derived_edges(page_records, documents, claims)
    messages = build_messages(segments)

    registries = {
        "source_versions": source_versions,
        "documents": documents,
        "messages": messages,
        "entities": entities,
        "claims": claims,
        "claim_evidence": claim_evidence,
        "segments": segments,
        "derived_edges": derived_edges,
    }
    output_paths = write_registries(project_root, registries)

    result: dict[str, Any] = {
        "root": str(project_root),
        "document_count": len(documents),
        "source_version_count": len(source_versions),
        "message_count": len(messages),
        "segment_count": len(segments),
        "entity_count": len(entities),
        "claim_count": len(claims),
        "claim_evidence_count": len(claim_evidence),
        "derived_edge_count": len(derived_edges),
        "limit_sources": limit_sources,
        "clean": clean,
        "registry_paths": output_paths,
        "source_page_count": len(documents),
    }

    if build_graph_projection:
        try:
            from build_graph_projection_from_jsonl import build_graph_projection_from_jsonl
        except ModuleNotFoundError:
            from scripts.build_graph_projection_from_jsonl import build_graph_projection_from_jsonl
        result["graph_projection"] = build_graph_projection_from_jsonl(
            project_root,
            allow_main_repo=allow_main_repo,
        )

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate benchmark canonical JSONL from DocTology source pages. "
            "For the raw-first production path, use scripts/ontology_ingest.py instead."
        )
    )
    parser.add_argument("--root", default=".", help="Project root to ingest. Defaults to current directory.")
    parser.add_argument("--wiki-dir", default=None, help="Optional wiki directory override.")
    parser.add_argument("--raw-dir", default=None, help="Reserved for future tranche raw-dir override.")
    parser.add_argument("--clean", action="store_true", help="Delete current benchmark output files before regenerating.")
    parser.add_argument("--limit-sources", type=int, default=None, help="Optional cap on number of source pages to ingest.")
    parser.add_argument(
        "--allow-main-repo",
        action="store_true",
        help="Explicitly allow writes against the main DocTology repo root. Omit this for sandbox-first runs.",
    )
    parser.add_argument(
        "--build-graph-projection",
        action="store_true",
        help="Also build warehouse/graph_projection from the generated canonical JSONL.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = ingest_ontology_benchmark(
        args.root,
        wiki_dir=args.wiki_dir,
        raw_dir=args.raw_dir,
        clean=args.clean,
        limit_sources=args.limit_sources,
        allow_main_repo=args.allow_main_repo,
        build_graph_projection=args.build_graph_projection,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
