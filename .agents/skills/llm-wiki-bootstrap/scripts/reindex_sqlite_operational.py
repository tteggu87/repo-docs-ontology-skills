#!/usr/bin/env python3
"""Initialize and rebuild a lightweight SQLite operational index for a file-canonical wiki."""

from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = ROOT / "templates" / "llm-wiki-three-layer" / "sqlite_operational.schema.sql"
PAGE_TYPE_BY_DIR = {
    "concepts": "concept",
    "entities": "entity",
    "people": "person",
    "projects": "project",
    "timelines": "timeline",
    "analyses": "analysis",
    "sources": "source",
}
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


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
    wiki_dir = repo_root / "wiki"
    if not wiki_dir.exists():
        return []
    records: list[tuple[str, str, str, str, str, str]] = []
    for path in sorted(wiki_dir.rglob("*.md")):
        rel = path.relative_to(wiki_dir)
        if not rel.parts or rel.parts[0] == "_meta":
            continue
        if rel.parts[0] not in PAGE_TYPE_BY_DIR:
            continue
        text = read_text(path)
        page_id = frontmatter_value(text, "page_id") or f"page-{path.stem}"
        title = frontmatter_value(text, "title") or extract_title(path, text)
        page_type = (
            frontmatter_value(text, "page_type")
            or frontmatter_value(text, "type")
            or PAGE_TYPE_BY_DIR.get(path.parent.name, "page")
        )
        updated_at = frontmatter_value(text, "updated_at") or frontmatter_value(text, "updated") or ""
        checksum = file_checksum(path)
        rel_path = path.relative_to(repo_root).as_posix()
        records.append((page_id, rel_path, title, page_type, updated_at, checksum))
    return records


def link_records(repo_root: Path, rows: list[tuple[str, str, str, str, str, str]]) -> list[tuple[str, str | None, str, str, str]]:
    wiki_dir = repo_root / "wiki"
    page_ids = {Path(path).stem: page_id for page_id, path, *_ in rows}
    links: list[tuple[str, str | None, str, str, str]] = []
    for page_id, path, *_ in rows:
        text = read_text(repo_root / path)
        for link in WIKILINK_RE.findall(text):
            resolved_page_id = page_ids.get(link)
            links.append((page_id, resolved_page_id, link, "resolved" if resolved_page_id else "unresolved", today_utc()))
    return links


def source_records(rows: list[tuple[str, str, str, str, str, str]], repo_root: Path) -> list[tuple[str, str, str]]:
    records: list[tuple[str, str, str]] = []
    for page_id, path, *_ in rows:
        text = read_text(repo_root / path)
        for source_link in re.findall(r'^\s*-\s*"\[\[([^\]]+)\]\]"\s*$', text, re.MULTILINE):
            records.append((page_id, source_link, "primary"))
    return records


def tag_records(rows: list[tuple[str, str, str, str, str, str]], repo_root: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for page_id, path, *_ in rows:
        text = read_text(repo_root / path)
        for tag in re.findall(r'^\s*-\s*([A-Za-z0-9._/-]+)\s*$', text, re.MULTILINE):
            records.append((page_id, tag))
    return records


def today_utc() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    db_path = repo_root / "state" / "wiki_index.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(read_text(SCHEMA_PATH))
        connection.execute("DELETE FROM pages")
        connection.execute("DELETE FROM page_links")
        connection.execute("DELETE FROM page_sources")
        connection.execute("DELETE FROM tags")
        rows = page_records(repo_root)
        connection.executemany(
            "INSERT INTO pages (id, path, title, page_type, updated_at, checksum) VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        connection.executemany(
            "INSERT INTO page_links (from_page_id, to_page_id, to_link_text, status, created_at) VALUES (?, ?, ?, ?, ?)",
            link_records(repo_root, rows),
        )
        connection.executemany(
            "INSERT OR IGNORE INTO page_sources (page_id, source_id, relation_type) VALUES (?, ?, ?)",
            source_records(rows, repo_root),
        )
        connection.executemany(
            "INSERT OR IGNORE INTO tags (page_id, tag) VALUES (?, ?)",
            tag_records(rows, repo_root),
        )
        connection.commit()
    finally:
        connection.close()

    print(f"Rebuilt SQLite operational index: {db_path}")
    print(f"Indexed pages: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
