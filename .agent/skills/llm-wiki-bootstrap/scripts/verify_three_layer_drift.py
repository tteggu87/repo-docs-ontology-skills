#!/usr/bin/env python3
"""Verify basic drift signals across file, SQLite, and DuckDB layers."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

try:
    import duckdb
except ModuleNotFoundError:  # pragma: no cover
    duckdb = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify coarse drift across three-layer wiki architecture.")
    parser.add_argument("--repo-root", required=True, help="Target wiki repository root.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()

    pages_dir = repo_root / "wiki" / "pages"
    manifest_path = repo_root / "wiki" / "sources" / "manifests" / "source_manifest.jsonl"
    sqlite_path = repo_root / "wiki" / "state" / "wiki_index.sqlite"
    duckdb_path = repo_root / "wiki" / "state" / "analytics.duckdb"

    page_count = sum(1 for _ in pages_dir.rglob("*.md")) if pages_dir.exists() else 0
    manifest_exists = manifest_path.exists()
    sqlite_exists = sqlite_path.exists()
    duckdb_exists = duckdb_path.exists()

    issues: list[str] = []
    if page_count and not sqlite_exists:
      issues.append("pages_exist_but_sqlite_missing")
    if manifest_exists and not duckdb_exists:
      issues.append("manifest_exists_but_duckdb_missing")

    if sqlite_exists:
        connection = sqlite3.connect(sqlite_path)
        try:
            cursor = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='pages'")
            if cursor.fetchone()[0] == 0:
                issues.append("sqlite_pages_table_missing")
        finally:
            connection.close()

    if duckdb_exists:
        if duckdb is None:
            issues.append("duckdb_dependency_missing")
        else:
            connection = duckdb.connect(str(duckdb_path), read_only=True)
            try:
                rows = connection.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='sources'"
                ).fetchone()
                if not rows or rows[0] == 0:
                    issues.append("duckdb_sources_table_missing")
            finally:
                connection.close()

    if issues:
        print("DRIFT_ISSUES")
        for item in issues:
            print(f"- {item}")
        return 1

    print("DRIFT_OK")
    print(f"- pages: {page_count}")
    print(f"- source_manifest: {'present' if manifest_exists else 'missing'}")
    print(f"- sqlite: {'present' if sqlite_exists else 'missing'}")
    print(f"- duckdb: {'present' if duckdb_exists else 'missing'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
