#!/usr/bin/env python3
"""Minimal cumulative-export-aware incremental ingest."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from incremental_support import (
    ROOT,
    assign_occurrence_indexes,
    export_version_id_for_document,
    incremental_status_page_for_family,
    message_fingerprint,
    read_jsonl,
    sha256_file,
    sha256_text,
    write_jsonl,
)

URL_RE = re.compile(r"https?://\S+")
VALID_PAGE_DIRS = ["analyses", "concepts", "entities", "people", "projects", "sources", "timelines"]


def project_root_from_arg(project_root: str | None) -> Path:
    return Path(project_root).resolve() if project_root else ROOT


def normalized_text(value: str | None) -> str:
    return unicodedata.normalize("NFC", value or "")


def load_source_families(project_root: Path) -> dict[str, Any]:
    path = project_root / "intelligence" / "manifests" / "source_families.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def resolve_source_family(project_root: Path, raw_path: Path) -> dict[str, str]:
    manifest = load_source_families(project_root)
    normalized_path = normalized_text(raw_path.as_posix())
    matches: list[dict[str, str]] = []
    for item in manifest.get("source_families", []):
        patterns = item.get("match", {}).get("path_contains", [])
        if patterns and all(normalized_text(pattern) in normalized_path for pattern in patterns):
            matches.append(
                {
                    "source_family_id": f"family-{item['key']}",
                    "source_kind": item.get("source_kind", "generic_export"),
                    "parser": item.get("default_parser", "unknown"),
                }
            )

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SystemExit(f"Ambiguous source family match for {raw_path}")
    raise SystemExit(f"No source family mapping matched {raw_path}")


def stable_speaker_entity_id(speaker_name: str | None) -> str | None:
    if not speaker_name:
        return None
    return f"person-{sha256_text(normalized_text(speaker_name))[:12]}"


def parse_kakao_chat_csv(raw_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with raw_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=1):
            timestamp = (row.get("Date") or "").strip() or None
            speaker_name = (row.get("User") or "").strip() or None
            text = row.get("Message") or ""
            inferred_date = timestamp.split(" ")[0] if timestamp else None
            event_type = "message" if timestamp or speaker_name else "system_notice"
            urls = URL_RE.findall(text)
            rows.append(
                {
                    "sequence": index,
                    "timestamp": timestamp,
                    "inferred_date": inferred_date,
                    "event_type": event_type,
                    "speaker_name": speaker_name,
                    "speaker_entity_id": stable_speaker_entity_id(speaker_name),
                    "text": text,
                    "urls": urls,
                    "url_count": len(urls),
                }
            )
    return assign_occurrence_indexes(rows)


def parse_markdown_note(raw_path: Path) -> list[dict[str, Any]]:
    text = raw_path.read_text(encoding="utf-8")
    urls = URL_RE.findall(text)
    return assign_occurrence_indexes(
        [
            {
                "sequence": 1,
                "timestamp": None,
                "inferred_date": None,
                "event_type": "note",
                "speaker_name": None,
                "speaker_entity_id": None,
                "text": text,
                "urls": urls,
                "url_count": len(urls),
            }
        ]
    )


def parse_rows_for_family(raw_path: Path, parser_name: str) -> list[dict[str, Any]]:
    if parser_name == "kakao_chat_csv":
        return parse_kakao_chat_csv(raw_path)
    if parser_name == "markdown_note":
        return parse_markdown_note(raw_path)
    raise SystemExit(f"Unsupported parser: {parser_name}")


def document_id_for_export(source_family_id: str, export_version_id: str) -> str:
    return f"doc-{source_family_id.removeprefix('family-')}-{export_version_id[-12:]}"


def title_from_raw_path(raw_path: Path) -> str:
    return raw_path.stem.replace("_", " ")


def today() -> str:
    return dt.date.today().isoformat()


def slugify(value: str) -> str:
    value = normalized_text(value).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "untitled"


def wiki_dir(project_root: Path) -> Path:
    return project_root / "wiki"


def meta_dir(project_root: Path) -> Path:
    return wiki_dir(project_root) / "_meta"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def iter_markdown_pages(project_root: Path) -> list[Path]:
    base = wiki_dir(project_root)
    if not base.exists():
        return []
    return sorted(path for path in base.rglob("*.md") if path.is_file())


def page_title_from_content(path: Path, content: str) -> str:
    match = re.search(r'^title:\s*"?(.*?)"?\s*$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    heading = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if heading:
        return heading.group(1).strip()
    return path.stem.replace("-", " ").title()


def extract_summary(content: str) -> str:
    lines = content.splitlines()
    if lines[:1] == ["---"]:
        try:
            end_index = lines[1:].index("---") + 2
            lines = lines[end_index:]
        except ValueError:
            pass

    for line in [line.strip() for line in lines]:
        if not line or line.startswith("---") or line.startswith("#"):
            continue
        if line.startswith("- "):
            return line[2:].strip()
        return line
    return "No summary yet."


def existing_created_date(path: Path) -> str | None:
    if not path.exists():
        return None
    match = re.search(r"^created:\s*(\d{4}-\d{2}-\d{2})\s*$", read_text(path), re.MULTILINE)
    return match.group(1) if match else None


def rebuild_index(project_root: Path) -> None:
    base = wiki_dir(project_root)
    meta = meta_dir(project_root)
    pages_by_section: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for path in iter_markdown_pages(project_root):
        rel = path.relative_to(base)
        if rel == Path("_meta/index.md"):
            continue
        content = read_text(path)
        section = rel.parts[0]
        pages_by_section[section].append((path.stem, extract_summary(content)))

    index_path = meta / "index.md"
    created = existing_created_date(index_path) or today()

    lines = [
        "---",
        'title: "Index"',
        "type: meta",
        "status: active",
        f"created: {created}",
        f"updated: {today()}",
        "---",
        "",
        "# Index",
        "",
        "This file is rebuilt by the incremental ingest workflow.",
        "",
    ]

    for section in ["_meta"] + VALID_PAGE_DIRS:
        entries = pages_by_section.get(section, [])
        if not entries:
            continue
        lines.append(f"## {'Meta' if section == '_meta' else section.title()}")
        lines.append("")
        for stem, summary in sorted(entries):
            lines.append(f"- [[{stem}]] - {summary}")
        lines.append("")

    write_text(meta / "index.md", "\n".join(lines).rstrip() + "\n")


def append_log(project_root: Path, title: str, bullets: list[str]) -> None:
    path = meta_dir(project_root) / "log.md"
    if path.exists():
        existing = read_text(path).rstrip()
    else:
        existing = "\n".join(
            [
                "---",
                'title: "Log"',
                "type: meta",
                "status: active",
                f"created: {today()}",
                f"updated: {today()}",
                "---",
                "",
                "# Log",
            ]
        )

    lines = [
        "",
        f"## [{today()}] ingest | {title}",
        "",
    ]
    lines.extend([f"- {bullet}" for bullet in bullets])
    write_text(path, existing + "\n" + "\n".join(lines) + "\n")


def update_source_page(
    project_root: Path,
    source_page_stem: str,
    document_row: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    path = wiki_dir(project_root) / "sources" / f"{source_page_stem}.md"
    created = today()
    if path.exists():
        match = re.search(r"^created:\s*(\d{4}-\d{2}-\d{2})\s*$", read_text(path), re.MULTILINE)
        if match:
            created = match.group(1)

    lines = [
        "---",
        f"title: {source_page_stem.replace('-', ' ').title()}",
        "type: source",
        "status: active",
        f"created: {created}",
        f"updated: {today()}",
        "tags:",
        "  - llm-wiki",
        "  - incremental-ingest",
        "---",
        "",
        f"# {source_page_stem.replace('-', ' ').title()}",
        "",
        "Incremental ingest status for this recurring source family.",
        "",
        "## Export Status",
        "",
        f"- Source family: `{summary['source_family_id']}`",
        f"- Latest export version: `{summary['export_version_id']}`",
        f"- Supersedes export version: `{summary['supersedes_export_version_id'] or 'none'}`",
        f"- Canonical document id: `{summary['document_id']}`",
        f"- New messages in this export: `{summary['new_message_count']}`",
        f"- Unchanged messages in this export: `{summary['unchanged_message_count']}`",
        f"- Total rows in this export: `{summary['message_count']}`",
        "",
        "## Source",
        "",
        f"- Raw path: `{document_row['raw_path']}`",
        f"- Source kind: `{document_row['source_kind']}`",
        f"- Content hash: `{document_row['content_hash']}`",
        "",
    ]
    curated_source_page = document_row.get("source_page")
    if curated_source_page:
        lines.extend(
            [
                "## Related Pages",
                "",
                f"- Curated source page: `[[{curated_source_page}]]`",
                "",
            ]
        )
    lines.extend(
        [
            "## Affected Surfaces",
            "",
            "### Canonical registries",
            "",
        ]
    )
    lines.extend([f"- `{item}`" for item in summary["affected_registry_paths"]])
    lines.extend(
        [
            "",
            "### Wiki surfaces",
            "",
        ]
    )
    lines.extend([f"- `{item}`" for item in summary["affected_wiki_paths"]])
    write_text(path, "\n".join(lines))


def latest_prior_export_version(
    source_versions: list[dict[str, Any]],
    source_family_id: str,
    current_export_version_id: str,
) -> str | None:
    family_versions = [
        row
        for row in source_versions
        if row.get("source_family_id") == source_family_id and row.get("export_version_id") != current_export_version_id
    ]
    if not family_versions:
        return None
    family_versions.sort(
        key=lambda row: (
            str(row.get("ingested_at") or ""),
            str(row.get("export_version_id") or ""),
        ),
        reverse=True,
    )
    return str(family_versions[0].get("export_version_id"))


def ingest_incremental(raw_source: str, project_root_arg: str | None = None) -> dict[str, Any]:
    project_root = project_root_from_arg(project_root_arg)
    raw_path = Path(raw_source).resolve()
    if not raw_path.exists():
        raise SystemExit(f"Source not found: {raw_path}")

    family = resolve_source_family(project_root, raw_path)
    content_hash = sha256_file(raw_path)
    warehouse = project_root / "warehouse" / "jsonl"
    warehouse.mkdir(parents=True, exist_ok=True)

    documents_path = warehouse / "documents.jsonl"
    messages_path = warehouse / "messages.jsonl"
    source_versions_path = warehouse / "source_versions.jsonl"

    documents = read_jsonl(documents_path)
    messages = read_jsonl(messages_path)
    source_versions = read_jsonl(source_versions_path)

    export_stub = {
        "source_family_id": family["source_family_id"],
        "content_hash": content_hash,
    }
    export_version_id = export_version_id_for_document(export_stub, content_hash)
    document_id = document_id_for_export(family["source_family_id"], export_version_id)

    existing_documents = {row["export_version_id"]: row for row in documents if "export_version_id" in row}
    existing_messages = {(row.get("source_family_id"), row.get("message_fingerprint")): row for row in messages}

    parsed_rows = parse_rows_for_family(raw_path, family["parser"])
    if export_version_id in existing_documents:
        document_id = existing_documents[export_version_id]["document_id"]
    new_messages = 0
    unchanged_messages = 0

    for parsed in parsed_rows:
        candidate = {
            **parsed,
            "document_id": document_id,
            "source_family_id": family["source_family_id"],
            "export_version_id": export_version_id,
        }
        fingerprint = message_fingerprint(candidate)
        key = (family["source_family_id"], fingerprint)
        if key in existing_messages:
            existing = existing_messages[key]
            existing["last_seen_export_version_id"] = export_version_id
            unchanged_messages += 1
            continue

        candidate["message_id"] = f"msg-{fingerprint.removeprefix('msgfp-')}"
        candidate["message_fingerprint"] = fingerprint
        candidate["first_seen_export_version_id"] = export_version_id
        candidate["last_seen_export_version_id"] = export_version_id
        messages.append(candidate)
        existing_messages[key] = candidate
        new_messages += 1

    timestamps = [row["timestamp"] for row in parsed_rows if row.get("timestamp")]
    computed_document_row = {
        "document_id": document_id,
        "document_type": "chat_log" if family["parser"] == "kakao_chat_csv" else "note",
        "title": title_from_raw_path(raw_path),
        "raw_path": raw_path.relative_to(project_root).as_posix() if raw_path.is_relative_to(project_root) else raw_path.as_posix(),
        "source_page": None,
        "incremental_status_page": incremental_status_page_for_family(family["source_family_id"]),
        "channel_entity_id": None,
        "start_at": min(timestamps) if timestamps else None,
        "end_at": max(timestamps) if timestamps else None,
        "message_count": len(parsed_rows),
        "participant_count": len({row["speaker_name"] for row in parsed_rows if row.get("speaker_name")}),
        "undated_system_notice_count": sum(1 for row in parsed_rows if row["event_type"] == "system_notice"),
        "csv_columns": ["Date", "User", "Message"] if family["parser"] == "kakao_chat_csv" else [],
        "ingested_at": dt.date.today().isoformat(),
        "source_family_id": family["source_family_id"],
        "source_kind": family["source_kind"],
        "content_hash": content_hash,
        "supersedes_export_version_id": None,
        "export_version_id": export_version_id,
    }
    document_row = existing_documents.get(export_version_id, computed_document_row)
    existing_documents[export_version_id] = document_row

    source_versions_map = {row["export_version_id"]: row for row in source_versions}
    supersedes_export_version_id = latest_prior_export_version(
        list(source_versions_map.values()),
        family["source_family_id"],
        export_version_id,
    )
    source_versions_map[export_version_id] = {
        **source_versions_map.get(
            export_version_id,
            {
                "export_version_id": export_version_id,
                "source_family_id": family["source_family_id"],
                "document_id": document_id,
                "source_kind": family["source_kind"],
                "raw_path": document_row["raw_path"],
                "content_hash": content_hash,
                "ingested_at": document_row["ingested_at"],
                "supersedes_export_version_id": supersedes_export_version_id,
            },
        ),
        "message_count": len(parsed_rows),
        "new_message_count": new_messages,
        "unchanged_message_count": unchanged_messages,
        "supersedes_export_version_id": supersedes_export_version_id,
    }

    source_page_stem = str(document_row.get("incremental_status_page") or incremental_status_page_for_family(family["source_family_id"]))
    document_row["incremental_status_page"] = source_page_stem
    document_row["supersedes_export_version_id"] = supersedes_export_version_id
    existing_documents[export_version_id] = document_row

    write_jsonl(documents_path, list(existing_documents.values()))
    write_jsonl(messages_path, messages)
    write_jsonl(source_versions_path, list(source_versions_map.values()))

    affected_registry_paths = [
        documents_path.relative_to(project_root).as_posix(),
        messages_path.relative_to(project_root).as_posix(),
        source_versions_path.relative_to(project_root).as_posix(),
    ]
    affected_wiki_paths = [
        f"wiki/sources/{source_page_stem}.md",
        "wiki/_meta/index.md",
        "wiki/_meta/log.md",
    ]
    curated_source_page = document_row.get("source_page")
    if curated_source_page:
        affected_wiki_paths.append(f"wiki/sources/{curated_source_page}.md")
    source_versions_map[export_version_id]["affected_registry_paths"] = affected_registry_paths
    source_versions_map[export_version_id]["affected_wiki_paths"] = affected_wiki_paths
    write_jsonl(source_versions_path, list(source_versions_map.values()))

    summary = {
        "source_family_id": family["source_family_id"],
        "export_version_id": export_version_id,
        "supersedes_export_version_id": supersedes_export_version_id,
        "document_id": document_id,
        "message_count": len(parsed_rows),
        "new_message_count": new_messages,
        "unchanged_message_count": unchanged_messages,
        "affected_registry_paths": affected_registry_paths,
        "affected_wiki_paths": affected_wiki_paths,
    }
    update_source_page(project_root, source_page_stem, document_row, summary)
    rebuild_index(project_root)
    append_log(
        project_root,
        f"{source_page_stem} incremental export",
        [
            f"Updated `{source_versions_path.relative_to(project_root).as_posix()}` for `{export_version_id}`",
            f"Supersedes export version: {supersedes_export_version_id or 'none'}",
            f"New messages: {new_messages}",
            f"Unchanged messages: {unchanged_messages}",
        ],
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Incremental ingest for cumulative exports.")
    parser.add_argument("raw_source", help="Path to the raw export file.")
    parser.add_argument("--project-root", default=None, help="Optional project root override.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = ingest_incremental(args.raw_source, args.project_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
