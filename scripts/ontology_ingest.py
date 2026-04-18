#!/usr/bin/env python3
"""Production-oriented raw-first ontology ingest for DocTology."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from build_graph_projection_from_jsonl import build_graph_projection_from_jsonl
    from ontology_registry_common import (
        MIN_SEGMENT_CHARS,
        REGISTRY_NAMES,
        REPO_ROOT,
        assert_safe_root,
        choose_canonical_alias,
        extract_candidate_aliases,
        extract_raw_summary,
        graph_projection_dir,
        iter_raw_files,
        normalize_entity_key,
        paragraph_entries,
        read_jsonl,
        relative_repo_path,
        sanitize_raw_text,
        sentence_entries,
        sha256_file,
        sha256_text,
        slugify,
        source_page_records,
        stable_claim_id,
        stable_document_id,
        stable_entity_id,
        stable_export_version_id,
        stable_message_id,
        stable_segment_id,
        stable_source_family_id,
        stringify_dateish,
        today_iso,
        warehouse_jsonl_dir,
        wiki_root_dir,
        write_jsonl,
    )
except ModuleNotFoundError:
    from scripts.build_graph_projection_from_jsonl import build_graph_projection_from_jsonl
    from scripts.ontology_registry_common import (
        MIN_SEGMENT_CHARS,
        REGISTRY_NAMES,
        REPO_ROOT,
        assert_safe_root,
        choose_canonical_alias,
        extract_candidate_aliases,
        extract_raw_summary,
        graph_projection_dir,
        iter_raw_files,
        normalize_entity_key,
        paragraph_entries,
        read_jsonl,
        relative_repo_path,
        sanitize_raw_text,
        sentence_entries,
        sha256_file,
        sha256_text,
        slugify,
        source_page_records,
        stable_claim_id,
        stable_document_id,
        stable_entity_id,
        stable_export_version_id,
        stable_message_id,
        stable_segment_id,
        stable_source_family_id,
        stringify_dateish,
        today_iso,
        warehouse_jsonl_dir,
        wiki_root_dir,
        write_jsonl,
    )

INGEST_METHOD = "ontology_production_raw_v1"
SOURCE_KIND = "raw_text_file"
REVIEW_STATE = "needs_review"


def collect_wiki_page_lookup(project_root: Path, wiki_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    wiki_root = wiki_root_dir(project_root, wiki_dir)
    if not wiki_root.exists():
        return {}
    lookup: dict[str, dict[str, Any]] = {}
    for path in sorted(wiki_root.rglob("*.md")):
        if not path.is_file() or "_meta" in path.relative_to(wiki_root).parts:
            continue
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("-", " ").title()
        frontmatter = {}
        body = text
        if text.startswith("---\n"):
            _, _, rest = text.partition("\n---\n")
            if rest:
                body = rest
            for line in text.splitlines()[1:]:
                if line == "---":
                    break
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip().strip('"')
            title = str(frontmatter.get("title") or title)
        lookup[path.stem] = {
            "stem": path.stem,
            "title": title,
            "section": path.relative_to(wiki_root).parts[0],
            "body": body,
        }
    return lookup


def raw_record(project_root: Path, raw_file: Path, page_record: dict[str, Any] | None) -> dict[str, Any]:
    raw_text = raw_file.read_text(encoding="utf-8")
    sanitized_raw_text = sanitize_raw_text(raw_text)
    source_stem = page_record["stem"] if page_record else raw_file.stem
    title = page_record["title"] if page_record else raw_file.stem.replace("-", " ").replace("_", " ").title()
    raw_rel = relative_repo_path(project_root, raw_file)
    raw_hash = sha256_file(raw_file)
    content_hash = raw_hash
    paragraphs = paragraph_entries(sanitized_raw_text)

    messages: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    message_sequence = 0
    for paragraph in paragraphs:
        for sentence in sentence_entries(
            paragraph["text"],
            base_char_start=int(paragraph["char_start"]),
            paragraph_index=int(paragraph["paragraph_index"]),
        ):
            message_sequence += 1
            message_id = stable_message_id(source_stem, message_sequence)
            segment_id = stable_segment_id(source_stem, message_sequence)
            message_row = {
                "message_id": message_id,
                "document_id": stable_document_id(source_stem),
                "source_document_id": stable_document_id(source_stem),
                "source_page": source_stem,
                "event_type": "raw_sentence",
                "text": sentence["text"],
                "sequence": message_sequence,
                "paragraph_index": sentence["paragraph_index"],
                "char_start": sentence["char_start"],
                "char_end": sentence["char_end"],
                "timestamp": None,
                "ingest_method": INGEST_METHOD,
            }
            segment_row = {
                "segment_id": segment_id,
                "document_id": stable_document_id(source_stem),
                "source_document_id": stable_document_id(source_stem),
                "source_page": source_stem,
                "text": sentence["text"],
                "position": message_sequence,
                "message_index": message_sequence,
                "paragraph_index": sentence["paragraph_index"],
                "char_start": sentence["char_start"],
                "char_end": sentence["char_end"],
                "ingest_method": INGEST_METHOD,
            }
            messages.append(message_row)
            segments.append(segment_row)

    created_or_updated = stringify_dateish(
        (page_record or {}).get("frontmatter", {}).get("updated")
        or (page_record or {}).get("frontmatter", {}).get("created")
        or today_iso()
    )
    document_row = {
        "document_id": stable_document_id(source_stem),
        "title": title,
        "raw_path": raw_rel,
        "source_page": source_stem,
        "incremental_status_page": source_stem,
        "source_family_id": stable_source_family_id(source_stem),
        "source_kind": SOURCE_KIND,
        "content_hash": content_hash,
        "ingested_at": created_or_updated,
        "export_version_id": stable_export_version_id(source_stem, content_hash),
        "message_count": len(messages),
        "benchmark_generated": False,
        "ingest_method": INGEST_METHOD,
        "raw_summary": extract_raw_summary(sanitized_raw_text),
    }
    return {
        "raw_file": raw_file,
        "raw_path": raw_rel,
        "raw_text": sanitized_raw_text,
        "raw_text_original": raw_text,
        "source_stem": source_stem,
        "title": title,
        "page_record": page_record,
        "content_hash": content_hash,
        "document": document_row,
        "messages": messages,
        "segments": segments,
    }


def sentence_predicate(sentence: str) -> tuple[str, str, int]:
    lowered = sentence.lower()
    if "does not support" in lowered or "do not support" in lowered or "unsupported" in lowered:
        return "does_not_support", "support", -1
    if "supports" in lowered or "support" in lowered:
        return "supports", "support", 1
    if "works with" in lowered:
        return "works_with", "works_with", 1
    if "integrates with" in lowered:
        return "integrates_with", "integrates_with", 1
    if '"' in sentence or "“" in sentence or "”" in sentence:
        return "quotes", "quotes", 0
    return "states", "states", 0


def sentence_topic(sentence: str, predicate: str) -> str:
    lowered = sentence.lower()
    stopwords = {"the", "for", "and", "with", "today", "another", "memo", "says", "now", "operators"}
    patterns = {
        "does_not_support": r"does not support\s+(.+)$",
        "supports": r"supports?\s+(.+)$",
        "works_with": r"works with\s+(.+)$",
        "integrates_with": r"integrates with\s+(.+)$",
    }
    pattern = patterns.get(predicate)
    if pattern:
        match = re.search(pattern, lowered)
        if match:
            tokens = [token for token in re.findall(r"[a-z0-9가-힣]+", match.group(1)) if token not in stopwords]
            return "-".join(tokens[:4]) if tokens else normalize_entity_key(match.group(1))
    tokens = [token for token in re.findall(r"[a-z0-9가-힣]+", lowered) if token not in stopwords]
    return "-".join(tokens[-3:]) if tokens else normalize_entity_key(lowered)


def claim_confidence(sentence: str, *, polarity: int, statement_kind: str) -> float:
    lowered = sentence.lower()
    confidence = 0.78
    if statement_kind == "quoted":
        confidence = 0.66
    if polarity < 0:
        confidence -= 0.12
    if any(token in lowered for token in ["incomplete", "uncertain", "maybe", "risk", "pending", "not"]):
        confidence -= 0.14
    return max(0.35, round(confidence, 2))


def add_entity_candidate(
    accumulators: dict[str, dict[str, Any]],
    *,
    alias: str,
    document_id: str,
    source_page: str,
    entity_type: str = "entity",
) -> None:
    normalized_key = normalize_entity_key(alias)
    if len(normalized_key) < 3:
        return
    bucket = accumulators.setdefault(
        normalized_key,
        {
            "normalized_key": normalized_key,
            "aliases": set(),
            "source_document_ids": set(),
            "source_pages": set(),
            "entity_type": entity_type,
        },
    )
    bucket["aliases"].add(alias.strip())
    bucket["source_document_ids"].add(document_id)
    bucket["source_pages"].add(source_page)
    if entity_type != "entity":
        bucket["entity_type"] = entity_type


def build_entities(records: list[dict[str, Any]], wiki_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    accumulators: dict[str, dict[str, Any]] = {}
    for record in records:
        document_id = record["document"]["document_id"]
        source_page = record["source_stem"]
        add_entity_candidate(accumulators, alias=record["title"], document_id=document_id, source_page=source_page, entity_type="source")
        add_entity_candidate(accumulators, alias=source_page, document_id=document_id, source_page=source_page, entity_type="source")
        for alias in extract_candidate_aliases(record["raw_text"]):
            linked_page = wiki_lookup.get(slugify(alias))
            entity_type = linked_page["section"][:-1] if linked_page and linked_page["section"].endswith("s") else linked_page["section"] if linked_page else "entity"
            add_entity_candidate(accumulators, alias=alias, document_id=document_id, source_page=source_page, entity_type=entity_type)
        if record["page_record"]:
            for link_stem in record["page_record"]["links"]:
                linked_page = wiki_lookup.get(link_stem)
                if not linked_page:
                    continue
                add_entity_candidate(
                    accumulators,
                    alias=str(linked_page["title"]),
                    document_id=document_id,
                    source_page=source_page,
                    entity_type=linked_page["section"][:-1] if linked_page["section"].endswith("s") else linked_page["section"],
                )
                add_entity_candidate(
                    accumulators,
                    alias=link_stem,
                    document_id=document_id,
                    source_page=source_page,
                    entity_type=linked_page["section"][:-1] if linked_page["section"].endswith("s") else linked_page["section"],
                )

    rows: list[dict[str, Any]] = []
    for bucket in sorted(accumulators.values(), key=lambda item: item["normalized_key"]):
        aliases = sorted(bucket["aliases"])
        canonical_name = choose_canonical_alias(aliases)
        rows.append(
            {
                "entity_id": stable_entity_id(canonical_name),
                "label": canonical_name,
                "canonical_name": canonical_name,
                "type": bucket["entity_type"],
                "aliases": aliases,
                "source_document_id": sorted(bucket["source_document_ids"])[0],
                "source_document_ids": sorted(bucket["source_document_ids"]),
                "source_page": sorted(bucket["source_pages"])[0],
                "source_pages": sorted(bucket["source_pages"]),
                "merge_candidate": len(aliases) > 1,
                "ingest_method": INGEST_METHOD,
            }
        )
    return rows


def entity_mentions(sentence: str, entities: list[dict[str, Any]]) -> list[str]:
    lowered = sentence.lower()
    hits: list[str] = []
    for row in entities:
        aliases = sorted(row.get("aliases") or [], key=len, reverse=True)
        for alias in aliases:
            alias_lower = alias.lower()
            if alias_lower and alias_lower in lowered:
                hits.append(str(row["entity_id"]))
                break
    return hits


def build_claims_and_evidence(
    records: list[dict[str, Any]],
    entities: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    claims: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    for record in records:
        source_stem = record["source_stem"]
        document_id = record["document"]["document_id"]
        source_entity_id = stable_entity_id(record["title"])
        for segment in record["segments"]:
            sentence = str(segment["text"]).strip()
            if len(sentence) < MIN_SEGMENT_CHARS:
                continue
            mentioned_entities = entity_mentions(sentence, entities)
            subject_id = mentioned_entities[0] if mentioned_entities else source_entity_id
            object_id = mentioned_entities[1] if len(mentioned_entities) > 1 else None
            predicate, predicate_family, polarity = sentence_predicate(sentence)
            statement_kind = "quoted" if ('"' in sentence or "“" in sentence or "”" in sentence) else "asserted"
            confidence = claim_confidence(sentence, polarity=polarity, statement_kind=statement_kind)
            claim_id = stable_claim_id(source_stem, sentence)
            claim_row = {
                "claim_id": claim_id,
                "claim_text": sentence,
                "document_id": document_id,
                "source_document_id": document_id,
                "subject_id": subject_id,
                "predicate": predicate,
                "predicate_family": predicate_family,
                "object_id": object_id,
                "topic_key": sentence_topic(sentence, predicate),
                "review_state": REVIEW_STATE,
                "confidence": float(confidence),
                "source_page": source_stem,
                "statement_kind": statement_kind,
                "extraction_method": INGEST_METHOD,
                "contradiction_candidate": False,
            }
            claims.append(claim_row)
            evidence_rows.append(
                {
                    "claim_id": claim_id,
                    "source_document_id": document_id,
                    "document_id": document_id,
                    "segment_id": segment["segment_id"],
                    "evidence_kind": "raw_segment",
                    "char_start": segment["char_start"],
                    "char_end": segment["char_end"],
                    "quote_text": sentence,
                    "ingest_method": INGEST_METHOD,
                }
            )

    grouped: dict[tuple[str | None, str | None, str], list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        grouped[(claim.get("subject_id"), claim.get("object_id"), str(claim.get("topic_key") or ""))].append(claim)
    for group_claims in grouped.values():
        polarities = {sentence_predicate(str(claim["claim_text"]))[2] for claim in group_claims}
        if 1 in polarities and -1 in polarities:
            for claim in group_claims:
                claim["contradiction_candidate"] = True
    return claims, evidence_rows


def build_derived_edges(claims: list[dict[str, Any]], entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def add_edge(source: str | None, target: str | None, label: str) -> None:
        if not source or not target:
            return
        key = (source, target, label)
        if key in seen:
            return
        seen.add(key)
        rows.append({"source": source, "target": target, "label": label, "ingest_method": INGEST_METHOD})

    for claim in claims:
        add_edge(str(claim.get("document_id") or ""), str(claim.get("claim_id") or ""), "documents")
        add_edge(str(claim.get("claim_id") or ""), str(claim.get("subject_id") or ""), "about_subject")
        add_edge(str(claim.get("claim_id") or ""), str(claim.get("object_id") or ""), "about_object")
    for row in entities:
        for document_id in row.get("source_document_ids") or []:
            add_edge(str(document_id), str(row.get("entity_id") or ""), "mentions")
    contradiction_claims = [claim for claim in claims if claim.get("contradiction_candidate")]
    for index, left in enumerate(contradiction_claims):
        for right in contradiction_claims[index + 1 :]:
            if left.get("subject_id") == right.get("subject_id") and left.get("topic_key") == right.get("topic_key"):
                add_edge(str(left.get("claim_id") or ""), str(right.get("claim_id") or ""), "contradicts")
    return rows


def merge_source_version_history(
    existing_versions: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in existing_versions:
        by_family[str(row.get("source_family_id") or "")].append(row)

    for record in records:
        document = record["document"]
        family_id = str(document["source_family_id"])
        history = list(by_family.get(family_id, []))
        latest = history[-1] if history else None
        same_hash = bool(latest and latest.get("content_hash") == document["content_hash"])
        if same_hash:
            continue
        export_version_id = str(document["export_version_id"])
        version_row = {
            "export_version_id": export_version_id,
            "source_family_id": family_id,
            "document_id": document["document_id"],
            "source_kind": SOURCE_KIND,
            "raw_path": document["raw_path"],
            "content_hash": document["content_hash"],
            "ingested_at": today_iso(),
            "supersedes_export_version_id": latest.get("export_version_id") if latest else None,
            "message_count": document["message_count"],
            "new_message_count": document["message_count"],
            "unchanged_message_count": 0 if latest else 0,
            "affected_registry_paths": [f"warehouse/jsonl/{name}.jsonl" for name in REGISTRY_NAMES],
            "affected_wiki_paths": [f"wiki/sources/{document['source_page']}.md"],
            "benchmark_generated": False,
            "ingest_method": INGEST_METHOD,
        }
        history.append(version_row)
        by_family[family_id] = history

    merged: list[dict[str, Any]] = []
    for family_id in sorted(by_family):
        merged.extend(by_family[family_id])
    return merged


def write_registries(project_root: Path, registries: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    warehouse_dir = warehouse_jsonl_dir(project_root)
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    output_paths: dict[str, str] = {}
    for name in REGISTRY_NAMES:
        path = warehouse_dir / f"{name}.jsonl"
        write_jsonl(path, registries.get(name, []))
        output_paths[name] = str(path.relative_to(project_root))
    return output_paths


def write_wiki_reconcile_preview(project_root: Path, records: list[dict[str, Any]], claims: list[dict[str, Any]]) -> dict[str, Any]:
    affected_pages = sorted({record["source_stem"] for record in records if record.get("page_record")})
    claims_by_page: dict[str, list[str]] = defaultdict(list)
    for claim in claims:
        claims_by_page[str(claim.get("source_page") or "")].append(str(claim.get("claim_text") or ""))
    preview_payload = {
        "generated_at": today_iso(),
        "mode": "shadow",
        "affected_source_pages": affected_pages,
        "page_previews": {
            stem: {
                "top_claims": claims_by_page.get(stem, [])[:3],
            }
            for stem in affected_pages
        },
    }
    state_dir = project_root / "wiki" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    preview_path = state_dir / "ontology_reconcile_preview.json"
    preview_path.write_text(json.dumps(preview_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "mode": "shadow",
        "preview_path": str(preview_path.relative_to(project_root)),
        "affected_source_pages": affected_pages,
    }


def ingest_ontology(
    project_root_arg: str | Path,
    *,
    wiki_dir: str | Path | None = None,
    raw_dir: str | Path | None = None,
    raw_paths: list[str] | None = None,
    clean: bool = False,
    limit_sources: int | None = None,
    allow_main_repo: bool = False,
    build_graph_projection: bool = False,
    wiki_reconcile_mode: str = "off",
) -> dict[str, Any]:
    project_root = Path(project_root_arg).resolve()
    assert_safe_root(project_root, allow_main_repo=allow_main_repo)
    resolved_wiki_dir = Path(wiki_dir).resolve() if wiki_dir else None
    resolved_raw_dir = Path(raw_dir).resolve() if raw_dir else None
    warehouse_dir = warehouse_jsonl_dir(project_root)
    warehouse_dir.mkdir(parents=True, exist_ok=True)

    page_records = source_page_records(project_root, resolved_wiki_dir)
    raw_path_to_stems: dict[str, list[str]] = defaultdict(list)
    for record in page_records.values():
        raw_path = str(record.get("raw_path") or "").strip()
        if raw_path:
            raw_path_to_stems[raw_path].append(str(record["stem"]))
    duplicate_raw_paths = {
        raw_path: sorted(stems)
        for raw_path, stems in raw_path_to_stems.items()
        if len(stems) > 1
    }
    if duplicate_raw_paths:
        details = ", ".join(f"{raw_path} -> {', '.join(stems)}" for raw_path, stems in sorted(duplicate_raw_paths.items()))
        raise ValueError(f"Duplicate source-page raw_path mappings are not allowed in production ingest: {details}")
    pages_by_raw_path = {record["raw_path"]: record for record in page_records.values() if record.get("raw_path")}
    touched_raw_files = iter_raw_files(
        project_root,
        raw_dir=resolved_raw_dir,
        raw_paths=raw_paths,
        limit_sources=limit_sources,
    ) if raw_paths else None
    raw_files = iter_raw_files(
        project_root,
        raw_dir=resolved_raw_dir,
        raw_paths=None,
        limit_sources=limit_sources,
    )
    if not raw_files:
        raise ValueError("No raw source files found for production ontology ingest.")

    selected_records = [
        raw_record(project_root, raw_file, pages_by_raw_path.get(relative_repo_path(project_root, raw_file)))
        for raw_file in raw_files
    ]
    selected_records.sort(key=lambda item: item["source_stem"])

    documents = [record["document"] for record in selected_records]
    messages = [row for record in selected_records for row in record["messages"]]
    segments = [row for record in selected_records for row in record["segments"]]

    wiki_lookup = collect_wiki_page_lookup(project_root, resolved_wiki_dir)
    entities = build_entities(selected_records, wiki_lookup)
    claims, claim_evidence = build_claims_and_evidence(selected_records, entities)
    derived_edges = build_derived_edges(claims, entities)

    source_versions_path = warehouse_dir / "source_versions.jsonl"
    existing_versions = [] if clean else read_jsonl(source_versions_path)
    source_versions = merge_source_version_history(existing_versions, selected_records)

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
    registry_paths = write_registries(project_root, registries)

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
        "clean": clean,
        "raw_file_count": len(raw_files),
        "raw_paths": [relative_repo_path(project_root, path) for path in (touched_raw_files or raw_files)],
        "registry_paths": registry_paths,
        "ingest_method": INGEST_METHOD,
    }

    if wiki_reconcile_mode == "shadow":
        result["wiki_reconcile"] = write_wiki_reconcile_preview(project_root, selected_records, claims)
    elif wiki_reconcile_mode != "off":
        raise ValueError(f"Unsupported wiki_reconcile_mode: {wiki_reconcile_mode}")

    if build_graph_projection:
        result["graph_projection"] = build_graph_projection_from_jsonl(
            project_root,
            allow_main_repo=allow_main_repo,
        )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate production canonical JSONL from DocTology raw sources.")
    parser.add_argument("--root", default=".", help="Project root to ingest. Defaults to current directory.")
    parser.add_argument("--wiki-dir", default=None, help="Optional wiki directory override.")
    parser.add_argument("--raw-dir", default=None, help="Optional raw directory override.")
    parser.add_argument("--raw-path", action="append", default=None, help="Specific raw path(s) to touch; full registry view is still rebuilt deterministically.")
    parser.add_argument("--clean", action="store_true", help="Ignore existing source-version history and rebuild from scratch.")
    parser.add_argument("--limit-sources", type=int, default=None, help="Optional cap on number of raw sources to ingest.")
    parser.add_argument("--wiki-reconcile-mode", choices=["off", "shadow"], default="off", help="How to handle wiki reconciliation previews.")
    parser.add_argument(
        "--allow-main-repo",
        action="store_true",
        help="Explicitly allow writes against the main DocTology repo root.",
    )
    parser.add_argument(
        "--build-graph-projection",
        action="store_true",
        help="Also build warehouse/graph_projection from the generated canonical JSONL.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = ingest_ontology(
        args.root,
        wiki_dir=args.wiki_dir,
        raw_dir=args.raw_dir,
        raw_paths=args.raw_path,
        clean=args.clean,
        limit_sources=args.limit_sources,
        allow_main_repo=args.allow_main_repo,
        build_graph_projection=args.build_graph_projection,
        wiki_reconcile_mode=args.wiki_reconcile_mode,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
