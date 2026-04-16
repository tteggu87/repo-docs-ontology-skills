#!/usr/bin/env python3
"""Initialize and refresh a lightweight DuckDB analytical warehouse from canonical exports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    import duckdb
except ModuleNotFoundError:  # pragma: no cover
    duckdb = None


ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = ROOT / "templates" / "llm-wiki-three-layer" / "duckdb_analytical.schema.sql"
TABLE_COLUMNS = {
    "sources": ["source_id", "source_type", "uri", "created_at", "raw_checksum"],
    "claims": ["claim_id", "source_id", "chunk_id", "claim_text", "confidence", "extraction_run_id"],
    "entities": ["entity_id", "canonical_name", "entity_type"],
    "relations": [
        "relation_id",
        "source_entity_id",
        "relation_type",
        "target_entity_id",
        "evidence_claim_id",
        "relation_confidence",
        "extraction_run_id",
    ],
    "audit_events": ["run_id", "phase", "status", "detail", "page_id", "severity", "created_at"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh analytics.duckdb from canonical JSONL exports.")
    parser.add_argument("--repo-root", required=True, help="Target wiki repository root.")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def project_rows(table_name: str, rows: list[dict]) -> list[list[object]]:
    columns = TABLE_COLUMNS[table_name]
    projected: list[list[object]] = []
    for row in rows:
        if table_name == "sources":
            normalized = {
                "source_id": row.get("source_id"),
                "source_type": row.get("source_type"),
                "uri": row.get("canonical_uri") or row.get("uri"),
                "created_at": row.get("created_at"),
                "raw_checksum": row.get("raw_checksum") or row.get("checksum"),
            }
        elif table_name == "relations":
            normalized = {
                "relation_id": row.get("relation_id"),
                "source_entity_id": row.get("source_entity_id"),
                "relation_type": row.get("relation_type"),
                "target_entity_id": row.get("target_entity_id"),
                "evidence_claim_id": row.get("evidence_claim_id"),
                "relation_confidence": row.get("relation_confidence") if row.get("relation_confidence") is not None else row.get("confidence"),
                "extraction_run_id": row.get("extraction_run_id"),
            }
        elif table_name == "audit_events":
            normalized = {
                "run_id": row.get("run_id"),
                "phase": row.get("phase"),
                "status": row.get("status"),
                "detail": row.get("detail"),
                "page_id": row.get("page_id"),
                "severity": row.get("severity"),
                "created_at": row.get("created_at") or row.get("finished_at") or row.get("started_at"),
            }
        else:
            normalized = {column: row.get(column) for column in columns}
        projected.append([normalized.get(column) for column in columns])
    return projected


def load_rows(connection, table_name: str, rows: list[dict]) -> None:
    if not rows:
        return
    columns = TABLE_COLUMNS[table_name]
    placeholders = ", ".join(["?"] * len(columns))
    column_list = ", ".join(columns)
    values = project_rows(table_name, rows)
    connection.executemany(
        f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})",
        values,
    )


def main() -> int:
    if duckdb is None:
        raise SystemExit("duckdb is required to run refresh_duckdb_analytics.py")

    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    db_path = repo_root / "wiki" / "state" / "analytics.duckdb"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(db_path))
    try:
        connection.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
        for table in (
            "sources",
            "claims",
            "entities",
            "relations",
            "audit_events",
        ):
            connection.execute(f"DELETE FROM {table}")

        manifest_rows = read_jsonl(repo_root / "wiki" / "sources" / "manifests" / "source_manifest.jsonl")
        claim_rows = read_jsonl(repo_root / "wiki" / "exports" / "claims.jsonl")
        entity_rows = read_jsonl(repo_root / "wiki" / "exports" / "entities.jsonl")
        relation_rows = read_jsonl(repo_root / "wiki" / "exports" / "relations.jsonl")
        run_rows = read_jsonl(repo_root / "wiki" / "exports" / "ingest_runs.jsonl")

        load_rows(connection, "sources", manifest_rows)
        load_rows(connection, "claims", claim_rows)
        load_rows(connection, "entities", entity_rows)
        load_rows(connection, "relations", relation_rows)
        load_rows(connection, "audit_events", run_rows)
    finally:
        connection.close()

    print(f"Refreshed DuckDB analytical warehouse: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
