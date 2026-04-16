#!/usr/bin/env python3
"""Initialize and rebuild a lightweight SQLite operational index for a file-canonical wiki."""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = ROOT / "templates" / "llm-wiki-three-layer" / "sqlite_operational.schema.sql"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild wiki_index.sqlite from wiki page files.")
    parser.add_argument("--repo-root", required=True, help="Target wiki repository root.")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def extract_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return path.stem.replace("-", " ").replace("_", " ").title()


def frontmatter_value(text: str, key: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    lines = text.splitlines()
    try:
        end_index = lines[1:].index("---") + 1
    except ValueError:
        return None
    for line in lines[1:end_index]:
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def page_records(repo_root: Path) -> list[tuple[str, str, str, str, str, str]]:
    pages_dir = repo_root / "wiki" / "pages"
    if not pages_dir.exists():
        return []
    records: list[tuple[str, str, str, str, str, str]] = []
    for path in sorted(pages_dir.rglob("*.md")):
        text = read_text(path)
        page_id = frontmatter_value(text, "page_id") or f"page-{path.stem}"
        title = frontmatter_value(text, "title") or extract_title(path, text)
        page_type = frontmatter_value(text, "page_type") or path.parent.name.rstrip("s")
        updated_at = frontmatter_value(text, "updated_at") or ""
        checksum = file_checksum(path)
        rel_path = path.relative_to(repo_root).as_posix()
        records.append((page_id, rel_path, title, page_type, updated_at, checksum))
    return records


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    db_path = repo_root / "wiki" / "state" / "wiki_index.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(read_text(SCHEMA_PATH))
        connection.execute("DELETE FROM pages")
        rows = page_records(repo_root)
        connection.executemany(
            "INSERT INTO pages (id, path, title, page_type, updated_at, checksum) VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        connection.commit()
    finally:
        connection.close()

    print(f"Rebuilt SQLite operational index: {db_path}")
    print(f"Indexed pages: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
