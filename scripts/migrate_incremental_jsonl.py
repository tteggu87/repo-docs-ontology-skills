#!/usr/bin/env python3
"""Backfill incremental-ingest fields for existing canonical JSONL files."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from incremental_support import (
    ROOT,
    assign_occurrence_indexes,
    export_version_id_for_document,
    incremental_status_page_for_family,
    message_fingerprint,
    read_jsonl,
    sha256_file,
    source_family_id_for_raw_path,
    source_kind_for_raw_path,
    write_jsonl,
)


def main() -> int:
    warehouse = ROOT / "warehouse" / "jsonl"
    documents_path = warehouse / "documents.jsonl"
    messages_path = warehouse / "messages.jsonl"
    source_versions_path = warehouse / "source_versions.jsonl"

    documents = read_jsonl(documents_path)
    messages = read_jsonl(messages_path)
    if not documents or not messages:
        print("No existing documents/messages registries to migrate.")
        return 0

    today = dt.date.today().isoformat()

    document_by_id = {}
    for document in documents:
        raw_path = document.get("raw_path", "")
        abs_raw_path = ROOT / raw_path if raw_path else None
        content_hash = sha256_file(abs_raw_path) if abs_raw_path and abs_raw_path.exists() else ""
        source_family_id = source_family_id_for_raw_path(raw_path)
        source_kind = source_kind_for_raw_path(raw_path)
        document["source_family_id"] = source_family_id
        document["source_kind"] = source_kind
        document["content_hash"] = content_hash
        document["supersedes_export_version_id"] = document.get("supersedes_export_version_id")
        document["export_version_id"] = export_version_id_for_document(document, content_hash or document["document_id"])
        document["incremental_status_page"] = document.get("incremental_status_page") or incremental_status_page_for_family(source_family_id)
        document_by_id[document["document_id"]] = document

    source_versions = []
    for document in documents:
        export_version_id = document["export_version_id"]
        source_versions.append(
            {
                "export_version_id": export_version_id,
                "source_family_id": document["source_family_id"],
                "document_id": document["document_id"],
                "source_kind": document["source_kind"],
                "raw_path": document.get("raw_path"),
                "content_hash": document["content_hash"],
                "ingested_at": document.get("ingested_at", today),
                "supersedes_export_version_id": document.get("supersedes_export_version_id"),
                "message_count": document.get("message_count"),
            }
        )

    messages_by_document: dict[str, list[dict[str, object]]] = {}
    for message in messages:
        messages_by_document.setdefault(str(message["document_id"]), []).append(message)

    for document_id, doc_messages in messages_by_document.items():
        doc_messages.sort(key=lambda item: int(item.get("sequence") or 0))
        assign_occurrence_indexes(doc_messages)
        document = document_by_id[document_id]
        export_version_id = document["export_version_id"]
        for message in doc_messages:
            message["source_family_id"] = document["source_family_id"]
            message["export_version_id"] = export_version_id
            message["message_fingerprint"] = message_fingerprint(message)
            message["first_seen_export_version_id"] = export_version_id
            message["last_seen_export_version_id"] = export_version_id

    write_jsonl(documents_path, documents)
    write_jsonl(messages_path, messages)
    write_jsonl(source_versions_path, source_versions)
    print("Backfilled incremental fields for documents/messages/source_versions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
