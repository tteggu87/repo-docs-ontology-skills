#!/usr/bin/env python3
"""Shared utilities and constants for the repository workbench adapter."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

import yaml

JSONL_REGISTRIES = [
    "source_versions",
    "documents",
    "messages",
    "entities",
    "claims",
    "claim_evidence",
    "segments",
    "derived_edges",
]

SEARCH_TOKEN_RE = re.compile(r"[0-9a-zA-Z가-힣][0-9a-zA-Z가-힣_-]{1,}")

ACTION_COMMANDS = {
    "status": ["python3", "scripts/llm_wiki.py", "status"],
    "reindex": ["python3", "scripts/llm_wiki.py", "reindex"],
    "lint": ["python3", "scripts/llm_wiki.py", "lint"],
    "doctor": ["python3", "scripts/llm_wiki.py", "doctor", "--json"],
}

REVIEW_STATE_ACTIVE = "approved"
REVIEW_STATE_PENDING = "needs_review"
REVIEW_STATE_REJECTED = "rejected"

WORKBENCH_ALLOWED_WRITE_PREFIXES = (
    "wiki/analyses/",
    "wiki/_meta/",
    "wiki/sources/",
    "wiki/concepts/",
    "wiki/entities/",
    "wiki/people/",
    "wiki/projects/",
    "wiki/timelines/",
    "warehouse/jsonl/claims.jsonl",
)


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
        rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text

    remainder = text[4:]
    marker = "\n---\n"
    end_index = remainder.find(marker)
    if end_index < 0:
        return {}, text

    raw_frontmatter = remainder[:end_index]
    body = remainder[end_index + len(marker):]
    frontmatter = yaml.safe_load(raw_frontmatter) or {}
    if not isinstance(frontmatter, dict):
        frontmatter = {}
    return frontmatter, body


def extract_summary(text: str) -> str:
    _, body = parse_frontmatter(text)
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            return stripped[2:].strip()
        return stripped
    return "No summary yet."


def strip_markdown(text: str) -> str:
    return re.sub(r"[#>*_`\\[\\]()!-]", " ", text)


def wikilinks(content: str) -> list[str]:
    return re.findall(r"\[\[([^\]|#]+)", content)


def tokenize_query(value: str) -> list[str]:
    return [token.lower() for token in SEARCH_TOKEN_RE.findall(value)]


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^0-9a-zA-Z가-힣]+", "-", lowered)
    return lowered.strip("-") or "untitled"


def safe_iso_date(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) else ""


def days_since_iso(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return (dt.date.today() - dt.date.fromisoformat(value)).days
    except ValueError:
        return None


def flatten_row_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(flatten_row_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(flatten_row_text(item) for item in value)
    if isinstance(value, tuple):
        return " ".join(flatten_row_text(item) for item in value)
    if value is None:
        return ""
    return str(value)


def update_frontmatter_date(text: str, field: str, value: str) -> str:
    pattern = re.compile(rf"^{field}:\s*.*$", re.MULTILINE)
    if pattern.search(text):
        return pattern.sub(f"{field}: {value}", text, count=1)
    return text


def append_bullet_to_section(text: str, heading: str, bullet: str) -> str:
    normalized = text if text.endswith("\n") else text + "\n"
    if bullet in normalized:
        return normalized

    lines = normalized.splitlines()
    section_header = f"## {heading}"
    try:
        start_index = lines.index(section_header)
    except ValueError:
        return normalized.rstrip() + f"\n\n## {heading}\n\n{bullet}\n"

    insert_at = len(lines)
    for index in range(start_index + 1, len(lines)):
        if lines[index].startswith("## "):
            insert_at = index
            break

    insertion = [bullet]
    if insert_at > 0 and lines[insert_at - 1] != "":
        insertion.insert(0, "")
    updated_lines = lines[:insert_at] + insertion + lines[insert_at:]
    return "\n".join(updated_lines).rstrip() + "\n"


def load_json_body(body_text: str | None) -> dict[str, Any]:
    if not body_text:
        return {}
    payload = json.loads(body_text)
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    return payload


def ensure_allowed_write_paths(paths: list[str]) -> None:
    for path in paths:
        if not any(path == prefix or path.startswith(prefix) for prefix in WORKBENCH_ALLOWED_WRITE_PREFIXES):
            raise ValueError(f"Write path is outside allowed workbench scope: {path}")


def default_incremental_registry_paths() -> list[str]:
    return [
        "warehouse/jsonl/documents.jsonl",
        "warehouse/jsonl/messages.jsonl",
        "warehouse/jsonl/source_versions.jsonl",
    ]


def default_incremental_wiki_paths(
    source_page_stem: str,
    incremental_status_page: str | None,
) -> list[str]:
    paths = [
        f"wiki/sources/{source_page_stem}.md",
        "wiki/_meta/index.md",
        "wiki/_meta/log.md",
    ]
    if incremental_status_page and incremental_status_page != source_page_stem:
        paths.insert(0, f"wiki/sources/{incremental_status_page}.md")
    return paths


def count_non_placeholder_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return sum(
        1
        for path in directory.rglob("*")
        if path.is_file() and not path.name.startswith(".")
    )


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return value


def metric_key(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def summarize_action_output(action: str, stdout_lines: list[str]) -> dict[str, Any]:
    if action == "status":
        metrics: dict[str, str] = {}
        for line in stdout_lines:
            if line.startswith("- ") and ": " in line:
                label, value = line[2:].split(": ", 1)
                metrics[metric_key(label)] = value
        return {
            "kind": "status",
            "metrics": metrics,
        }

    if action == "lint":
        section: str | None = None
        hard_failures: dict[str, str] = {}
        advisory_warnings: dict[str, str] = {}
        for line in stdout_lines:
            if line == "Hard failures":
                section = "hard_failures"
                continue
            if line == "Advisory warnings":
                section = "advisory_warnings"
                continue
            if line.startswith("- ") and ": " in line and section:
                label, value = line[2:].split(": ", 1)
                if section == "hard_failures":
                    hard_failures[metric_key(label)] = value
                elif section == "advisory_warnings":
                    advisory_warnings[metric_key(label)] = value
        return {
            "kind": "lint",
            "hard_failures": hard_failures,
            "advisory_warnings": advisory_warnings,
        }

    if action == "doctor":
        try:
            return json.loads("\n".join(stdout_lines))
        except json.JSONDecodeError:
            return {
                "kind": "doctor",
                "messages": stdout_lines,
                "warnings": ["doctor_summary_parse_failed"],
            }

    return {
        "kind": action,
        "messages": stdout_lines,
    }


def parse_index_sections(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current = {"name": line[3:].strip(), "entries": []}
            sections.append(current)
            continue
        if not current or not line.startswith("- [["):
            continue

        match = re.match(r"- \[\[([^\]]+)\]\](?: - (.*))?$", line)
        if not match:
            continue

        current["entries"].append(
            {
                "stem": match.group(1),
                "summary": match.group(2) or "",
            }
        )

    return sections


def parse_log_entries(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## ["):
            match = re.match(r"## \[([^\]]+)\] ([^|]+)\| (.+)$", line)
            if match:
                current = {
                    "date": match.group(1).strip(),
                    "kind": match.group(2).strip(),
                    "title": match.group(3).strip(),
                    "bullets": [],
                }
                entries.append(current)
            else:
                current = None
            continue

        if current and line.startswith("- "):
            current["bullets"].append(line[2:].strip())

    return entries
