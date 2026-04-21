#!/usr/bin/env python3
"""Shared helpers for benchmark and production ontology registry pipelines."""

from __future__ import annotations

import datetime as dt
import re
import unicodedata
from pathlib import Path
from typing import Any

try:
    from incremental_support import read_jsonl, sha256_file, sha256_text, write_jsonl
except ModuleNotFoundError:
    from scripts.incremental_support import read_jsonl, sha256_file, sha256_text, write_jsonl

try:
    from workbench.common import extract_summary, parse_frontmatter, read_text, slugify, wikilinks
except ModuleNotFoundError:
    from scripts.workbench.common import extract_summary, parse_frontmatter, read_text, slugify, wikilinks

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
TEXT_FILE_SUFFIXES = {".md", ".markdown", ".rst", ".text", ".txt"}
RAW_ALLOWED_PREFIXES = ("raw/inbox/", "raw/processed/", "raw/notes/")
ENTITY_STOPWORDS = {
    "A",
    "An",
    "And",
    "Another",
    "But",
    "For",
    "Graph",
    "In",
    "It",
    "Its",
    "Memo",
    "Note",
    "Notes",
    "Offline",
    "Operators",
    "Or",
    "Source",
    "The",
    "This",
    "Today",
}


def today_iso() -> str:
    return dt.date.today().isoformat()


def stringify_dateish(value: Any) -> str:
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if value is None:
        return ""
    return str(value)


def warehouse_jsonl_dir(project_root: Path) -> Path:
    return project_root / "warehouse" / "jsonl"


def graph_projection_dir(project_root: Path) -> Path:
    return project_root / "warehouse" / "graph_projection"


def wiki_root_dir(project_root: Path, wiki_dir: Path | None = None) -> Path:
    return wiki_dir or (project_root / "wiki")


def source_pages_dir(project_root: Path, wiki_dir: Path | None = None) -> Path:
    return wiki_root_dir(project_root, wiki_dir) / "sources"


def assert_safe_root(project_root: Path, *, allow_main_repo: bool = False) -> None:
    if allow_main_repo:
        return
    if project_root.resolve() == REPO_ROOT.resolve():
        raise ValueError(
            "Refusing to write ontology registries against the main DocTology repo root without allow_main_repo=True."
        )


def assert_inside_repo(project_root: Path, candidate: Path) -> None:
    resolved_root = project_root.resolve()
    resolved_candidate = candidate.resolve()
    if resolved_candidate != resolved_root and resolved_root not in resolved_candidate.parents:
        raise ValueError(f"Resolved path escapes project root: {candidate}")


def relative_repo_path(project_root: Path, candidate: Path) -> str:
    assert_inside_repo(project_root, candidate)
    return candidate.resolve().relative_to(project_root.resolve()).as_posix()


def stable_document_id(stem: str) -> str:
    return f"document:{stem}"


def stable_source_family_id(stem: str) -> str:
    return f"family-source-page:{stem}"


def stable_export_version_id(stem: str, content_hash: str) -> str:
    return f"export:{stem}:{content_hash[:12]}"


def stable_entity_id(stem: str) -> str:
    return f"entity:{slugify(stem)}"


def stable_message_id(stem: str, sequence: int) -> str:
    return f"message:{stem}:{sequence}"


def stable_segment_id(stem: str, position: int) -> str:
    return f"segment:{stem}:{position}"


def stable_claim_id(stem: str, claim_text: str) -> str:
    return f"claim:{stem}:{sha256_text(claim_text)[:12]}"


def singular_section(section: str) -> str:
    return section[:-1] if section.endswith("s") else section


def normalize_entity_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_friendly = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    ascii_friendly = ascii_friendly.lower()
    return re.sub(r"[^a-z0-9가-힣]+", "", ascii_friendly)


def choose_canonical_alias(aliases: list[str] | set[str]) -> str:
    alias_list = [alias.strip() for alias in aliases if alias and alias.strip()]
    if not alias_list:
        return "Unknown Entity"

    def score(alias: str) -> tuple[int, int, int, str]:
        has_alpha = any(char.isalpha() for char in alias)
        all_caps = int(has_alpha and alias.upper() == alias)
        punctuation_penalty = alias.count(" ") + alias.count("-") + alias.count("_")
        return (all_caps, punctuation_penalty, len(alias), alias.casefold())

    return sorted(alias_list, key=score)[0]


def is_allowed_raw_relative_path(raw_path: str) -> bool:
    return raw_path.startswith(RAW_ALLOWED_PREFIXES)


def resolve_raw_path(project_root: Path, raw_path_value: str | None) -> tuple[str, str | None, Path | None]:
    if not raw_path_value:
        return "", None, None
    raw_path = raw_path_value.strip()
    if not raw_path:
        return "", None, None
    if not is_allowed_raw_relative_path(raw_path):
        raise ValueError("raw_path must stay under raw/inbox/, raw/processed/, or raw/notes/")
    candidate = (project_root / raw_path).resolve()
    assert_inside_repo(project_root, candidate)
    if candidate.exists():
        return raw_path, sha256_file(candidate), candidate
    return raw_path, None, candidate


def iter_source_pages(project_root: Path, wiki_dir: Path | None = None) -> list[Path]:
    base = source_pages_dir(project_root, wiki_dir)
    if not base.exists():
        return []
    return sorted(path for path in base.glob("*.md") if path.is_file())


def source_page_records(project_root: Path, wiki_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    wiki_root = wiki_root_dir(project_root, wiki_dir)
    for path in iter_source_pages(project_root, wiki_dir):
        text = read_text(path)
        frontmatter, body = parse_frontmatter(text)
        raw_path = str(frontmatter.get("raw_path") or "").strip()
        records[path.stem] = {
            "stem": path.stem,
            "path": path,
            "title": str(frontmatter.get("title") or path.stem.replace("-", " ").title()),
            "frontmatter": frontmatter,
            "body": body,
            "summary": extract_summary(text),
            "section": path.relative_to(wiki_root).parts[0],
            "links": sorted(set(wikilinks(text))),
            "raw_path": raw_path,
        }
    return records


def source_pages_by_raw_path(project_root: Path, wiki_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    return {
        record["raw_path"]: record
        for record in source_page_records(project_root, wiki_dir).values()
        if record.get("raw_path")
    }


def iter_raw_files(
    project_root: Path,
    *,
    raw_dir: Path | None = None,
    raw_paths: list[str] | None = None,
    limit_sources: int | None = None,
) -> list[Path]:
    if raw_paths:
        resolved: list[Path] = []
        for raw_path in raw_paths:
            normalized = raw_path.strip()
            if not normalized:
                continue
            candidate = (project_root / normalized).resolve()
            assert_inside_repo(project_root, candidate)
            if not candidate.exists():
                raise FileNotFoundError(f"Raw source file not found: {normalized}")
            if not is_allowed_raw_relative_path(relative_repo_path(project_root, candidate)):
                raise ValueError(f"Raw path must stay under raw/inbox/, raw/processed/, or raw/notes/: {normalized}")
            resolved.append(candidate)
        return sorted(dict.fromkeys(resolved))

    bases = [raw_dir] if raw_dir else [project_root / "raw" / name for name in ("inbox", "processed", "notes")]
    raw_files: list[Path] = []
    for base in bases:
        if base is None:
            continue
        resolved_base = Path(base).resolve()
        if not resolved_base.exists():
            continue
        assert_inside_repo(project_root, resolved_base)
        for candidate in sorted(path for path in resolved_base.rglob("*") if path.is_file()):
            if candidate.suffix.lower() not in TEXT_FILE_SUFFIXES:
                continue
            raw_files.append(candidate)
    unique = sorted(dict.fromkeys(raw_files))
    if limit_sources is not None:
        return unique[: max(0, limit_sources)]
    return unique


def title_from_raw_path(raw_path: Path) -> str:
    return raw_path.stem.replace("-", " ").replace("_", " ").title()


def paragraph_entries(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    offset = 0
    line_no = 1
    active_lines: list[str] = []
    active_start = 0
    active_line_start = 1

    def flush() -> None:
        nonlocal active_lines, active_start, active_line_start
        if not active_lines:
            return
        paragraph_text = " ".join(line.strip() for line in active_lines if line.strip()).strip()
        if paragraph_text:
            entries.append(
                {
                    "text": paragraph_text,
                    "char_start": active_start,
                    "char_end": active_start + len(paragraph_text),
                    "line_start": active_line_start,
                    "line_end": active_line_start + len(active_lines) - 1,
                    "paragraph_index": len(entries) + 1,
                }
            )
        active_lines = []

    for raw_line in text.splitlines(keepends=True):
        stripped = raw_line.strip()
        line_text = raw_line.rstrip("\n")
        if stripped:
            if not active_lines:
                active_start = offset + max(0, len(line_text) - len(line_text.lstrip()))
                active_line_start = line_no
            active_lines.append(line_text)
        else:
            flush()
        offset += len(raw_line)
        line_no += 1
    flush()
    return [entry for entry in entries if len(entry["text"]) >= MIN_SEGMENT_CHARS]


def sentence_entries(text: str, *, base_char_start: int, paragraph_index: int) -> list[dict[str, Any]]:
    matches = list(re.finditer(r"[^.!?\n]+[.!?]?", text))
    entries: list[dict[str, Any]] = []
    for match in matches:
        sentence = match.group(0).strip()
        if len(sentence) < MIN_SEGMENT_CHARS:
            continue
        entries.append(
            {
                "text": sentence,
                "char_start": base_char_start + match.start(),
                "char_end": base_char_start + match.end(),
                "paragraph_index": paragraph_index,
            }
        )
    return entries


def extract_candidate_aliases(text: str) -> list[str]:
    aliases: list[str] = []
    for match in re.findall(r"\b(?:[A-Z][A-Za-z0-9]+(?:[- ][A-Z0-9][A-Za-z0-9]+)*)\b", text):
        cleaned = match.strip().strip('"“”()[]{}')
        if len(cleaned) < 3 or cleaned in ENTITY_STOPWORDS:
            continue
        aliases.append(cleaned)
    for hangul, english in re.findall(r"([가-힣][가-힣\s]{1,30})\(([^)]+)\)", text):
        if len(hangul.strip()) >= 2:
            aliases.append(hangul.strip())
        if len(english.strip()) >= 3:
            aliases.append(english.strip())
    return aliases


def extract_raw_summary(raw_text: str) -> str:
    for paragraph in paragraph_entries(raw_text):
        if paragraph["text"]:
            return paragraph["text"]
    return "No raw summary available."


def sanitize_raw_text(text: str) -> str:
    sanitized_lines: list[str] = []
    lines = text.splitlines(keepends=True)
    in_frontmatter = False
    for index, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if index == 0 and stripped == "---":
            in_frontmatter = True
            sanitized_lines.append("\n" if raw_line.endswith("\n") else "")
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            sanitized_lines.append("\n" if raw_line.endswith("\n") else "")
            continue
        if stripped.startswith("#"):
            sanitized_lines.append("\n" if raw_line.endswith("\n") else "")
            continue
        if stripped.lower().startswith("primary url:") or re.match(r"^-?\s*https?://", stripped):
            sanitized_lines.append("\n" if raw_line.endswith("\n") else "")
            continue
        sanitized_lines.append(raw_line)
    return "".join(sanitized_lines)
