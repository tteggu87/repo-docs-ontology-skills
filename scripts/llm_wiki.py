#!/usr/bin/env python3
"""Minimal local tooling for an Obsidian-first LLM Wiki.

The `ingest` command performs source registration only.
It does not run ontology-backed extraction or full wiki synthesis.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = ROOT / "wiki"
META_DIR = WIKI_DIR / "_meta"
RAW_DIR = ROOT / "raw"
TEMPLATE_PATH = ROOT / "templates" / "source_page_template.md"

VALID_PAGE_DIRS = [
    "analyses",
    "concepts",
    "entities",
    "people",
    "projects",
    "sources",
    "timelines",
]

MAX_PAGE_LINES = 200
LOG_ROTATION_THRESHOLD = 500
WAREHOUSE_JSONL_REGISTRIES = [
    "source_versions",
    "documents",
    "messages",
    "entities",
    "claims",
    "claim_evidence",
    "segments",
    "derived_edges",
]
DOC_READINESS_FILES = {
    "current_state": Path("docs/CURRENT_STATE.md"),
    "layers": Path("docs/LAYERS.md"),
    "versioning_policy": Path("docs/VERSIONING_POLICY.md"),
}


def today() -> str:
    return dt.date.today().isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "untitled"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def iter_markdown_pages() -> list[Path]:
    return sorted(
        path
        for path in WIKI_DIR.rglob("*.md")
        if path.is_file()
    )


def page_title_from_content(path: Path, content: str) -> str:
    match = re.search(r'^title:\s*"?(.*?)"?\s*$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    heading = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if heading:
        return heading.group(1).strip()
    return path.stem.replace("-", " ").title()


def page_type_from_path(path: Path) -> str:
    try:
        return path.relative_to(WIKI_DIR).parts[0]
    except ValueError:
        return "unknown"


def extract_summary(content: str) -> str:
    lines = [line.strip() for line in content.splitlines()]
    for line in lines:
        if not line or line.startswith("---") or line.startswith("#") or line.startswith("title:"):
            continue
        if line.startswith("type:") or line.startswith("status:") or line.startswith("created:") or line.startswith("updated:"):
            continue
        if line.startswith("- "):
            return line[2:].strip()
        return line
    return "No summary yet."


def has_frontmatter(content: str) -> bool:
    return content.startswith("---\n")


def wikilinks(content: str) -> list[str]:
    return re.findall(r"\[\[([^\]|#]+)", content)


def page_lookup() -> dict[str, Path]:
    lookup: dict[str, Path] = {}
    for path in iter_markdown_pages():
        lookup[path.stem] = path
    return lookup


def indexed_page_stems() -> set[str]:
    path = META_DIR / "index.md"
    if not path.exists():
        return set()
    return set(re.findall(r"^- \[\[([^\]]+)\]\]", read_text(path), re.MULTILINE))


def existing_created_date(path: Path) -> str | None:
    if not path.exists():
        return None
    match = re.search(r"^created:\s*(\d{4}-\d{2}-\d{2})\s*$", read_text(path), re.MULTILINE)
    return match.group(1) if match else None


def _count_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return sum(1 for path in directory.rglob("*") if path.is_file())


def _count_log_entries(path: Path) -> int:
    if not path.exists():
        return 0
    return len(re.findall(r"^##\s+\[", read_text(path), re.MULTILINE))


def _count_index_entries(path: Path) -> int:
    if not path.exists():
        return 0
    return len(re.findall(r"^- \[\[", read_text(path), re.MULTILINE))


def _extract_raw_path(content: str) -> str:
    match = re.search(r'^raw_path:\s*"?(.*?)"?\s*$', content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_status(content: str) -> str:
    match = re.search(r'^status:\s*"?(.*?)"?\s*$', content, re.MULTILINE)
    return match.group(1).strip().lower() if match else ""


def _jsonl_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            count += 1
    return count


def _graph_projection_health(root: Path) -> dict[str, object]:
    graph_dir = root / "warehouse" / "graph_projection"
    nodes_path = graph_dir / "nodes.jsonl"
    edges_path = graph_dir / "edges.jsonl"
    payload: dict[str, object] = {
        "path": str(graph_dir.relative_to(root)),
        "available": False,
        "node_count": 0,
        "edge_count": 0,
        "warnings": [],
    }
    warnings = payload["warnings"]
    if not nodes_path.exists() or not edges_path.exists():
        warnings.append("missing_graph_projection_files")
        return payload
    try:
        node_count = _jsonl_row_count(nodes_path)
        edge_count = _jsonl_row_count(edges_path)
        for candidate in (nodes_path, edges_path):
            for raw_line in candidate.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                json.loads(line)
        payload["available"] = True
        payload["node_count"] = node_count
        payload["edge_count"] = edge_count
        return payload
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        warnings.append("graph_projection_invalid")
        return payload


def classify_working_tree_entries(lines: list[str]) -> dict[str, object]:
    buckets = {
        "agent_local": [],
        "runtime_state": [],
        "live_workspace": [],
        "durable_repo_change": [],
        "other": [],
    }
    for raw_line in lines:
        line = raw_line.rstrip()
        if not line:
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        category = "other"
        if path.startswith(".codex/") or path.startswith(".hermes/") or path.startswith(".agents/context/") or path.startswith(".agents/tmp/"):
            category = "agent_local"
        elif path.startswith("wiki/state/") or path.startswith("warehouse/graph_projection/") or "/__pycache__/" in path or path.endswith(".pyc"):
            category = "runtime_state"
        elif path.startswith("raw/") or path.startswith("warehouse/jsonl/") or path.startswith("wiki/sources/") or path.startswith("wiki/analyses/"):
            category = "live_workspace"
        elif path.startswith("docs/") or path.startswith("scripts/") or path.startswith("tests/") or path.startswith("apps/") or path.startswith("README") or path == ".gitignore":
            category = "durable_repo_change"
        buckets[category].append({"status": status, "path": path})

    counts = {key: len(items) for key, items in buckets.items()}
    total_dirty = sum(counts.values())
    return {
        "clean": total_dirty == 0,
        "counts": counts,
        "items": buckets,
    }


def _working_tree_health(root: Path) -> dict[str, object]:
    git_dir = root / ".git"
    if not git_dir.exists():
        return {
            "available": False,
            "clean": True,
            "counts": {"agent_local": 0, "runtime_state": 0, "live_workspace": 0, "durable_repo_change": 0, "other": 0},
            "items": {},
            "warnings": ["git_metadata_missing"],
        }
    process = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [line for line in process.stdout.splitlines() if line.strip()]
    payload = classify_working_tree_entries(lines)
    payload.update({"available": process.returncode == 0, "warnings": [] if process.returncode == 0 else ["git_status_failed"]})
    return payload


def build_status_payload(root: Path = ROOT) -> dict[str, object]:
    base_root = root.resolve()
    wiki_dir = base_root / "wiki"
    meta_dir = wiki_dir / "_meta"
    raw_dir = base_root / "raw"
    return {
        "root": str(base_root),
        "raw_files": _count_files(raw_dir),
        "wiki_pages": len(sorted(path for path in wiki_dir.rglob("*.md") if path.is_file())) if wiki_dir.exists() else 0,
        "log_entries": _count_log_entries(meta_dir / "log.md"),
        "index_entries": _count_index_entries(meta_dir / "index.md"),
    }


def render_status_payload(payload: dict[str, object]) -> str:
    return "\n".join(
        [
            "LLM Wiki status",
            f"- Root: {payload['root']}",
            f"- Raw files: {payload['raw_files']}",
            f"- Wiki pages: {payload['wiki_pages']}",
            f"- Log entries: {payload['log_entries']}",
            f"- Index entries: {payload['index_entries']}",
        ]
    )


def build_doctor_payload(root: Path = ROOT) -> dict[str, object]:
    base_root = root.resolve()
    wiki_dir = base_root / "wiki"
    meta_dir = wiki_dir / "_meta"
    raw_dir = base_root / "raw"
    warehouse_jsonl_dir = base_root / "warehouse" / "jsonl"
    source_pages = sorted((wiki_dir / "sources").glob("*.md")) if (wiki_dir / "sources").exists() else []
    raw_path_owners: dict[str, list[str]] = defaultdict(list)
    missing_raw_path: list[str] = []
    for path in source_pages:
        content = read_text(path)
        raw_path = _extract_raw_path(content)
        status = _extract_status(content)
        if raw_path:
            raw_path_owners[raw_path].append(path.stem)
        elif status not in {"superseded", "archived", "reference-only"}:
            missing_raw_path.append(path.stem)
    duplicate_raw_path_owners = [
        {"raw_path": raw_path, "owners": sorted(owners)}
        for raw_path, owners in sorted(raw_path_owners.items())
        if len(owners) > 1
    ]
    docs_readiness = {
        "current_state_exists": (base_root / DOC_READINESS_FILES["current_state"]).exists(),
        "layers_exists": (base_root / DOC_READINESS_FILES["layers"]).exists(),
        "versioning_policy_exists": (base_root / DOC_READINESS_FILES["versioning_policy"]).exists(),
    }
    warehouse_counts = {
        name: _jsonl_row_count(warehouse_jsonl_dir / f"{name}.jsonl")
        for name in WAREHOUSE_JSONL_REGISTRIES
    }
    canonical_total = sum(warehouse_counts[name] for name in WAREHOUSE_JSONL_REGISTRIES if name != "derived_edges")
    graph_projection = _graph_projection_health(base_root)
    operator_readiness = {
        "production_ingest_entrypoint_exists": (base_root / "scripts" / "ontology_ingest.py").exists(),
        "benchmark_ingest_entrypoint_exists": (base_root / "scripts" / "ontology_benchmark_ingest.py").exists(),
        "shadow_reconcile_preview_exists": (wiki_dir / "state" / "ontology_reconcile_preview.json").exists(),
        "canonical_truth_nonempty": canonical_total > 0,
        "recommended_next_steps": [],
    }
    if operator_readiness["production_ingest_entrypoint_exists"] and _count_files(raw_dir) > 0 and canonical_total == 0:
        operator_readiness["recommended_next_steps"].append(
            f"python scripts/ontology_ingest.py --root {base_root} --allow-main-repo --build-graph-projection --wiki-reconcile-mode shadow"
        )
    if operator_readiness["shadow_reconcile_preview_exists"]:
        operator_readiness["recommended_next_steps"].append(
            f"python scripts/llm_wiki.py reconcile-shadow --root {base_root}"
        )
    if canonical_total > 0:
        operator_readiness["recommended_next_steps"].append("Review `source_detail()` and `review_summary()` surfaces before promoting wiki changes.")
    return {
        "kind": "doctor",
        "root": str(base_root),
        "status": build_status_payload(base_root),
        "raw_counts": {
            "inbox": _count_files(raw_dir / "inbox"),
            "processed": _count_files(raw_dir / "processed"),
            "notes": _count_files(raw_dir / "notes"),
            "assets": _count_files(raw_dir / "assets"),
            "other": max(0, _count_files(raw_dir) - sum(_count_files(raw_dir / name) for name in ("inbox", "processed", "notes", "assets"))),
            "total": _count_files(raw_dir),
        },
        "wiki_health": {
            "wiki_page_count": len(sorted(path for path in wiki_dir.rglob("*.md") if path.is_file())) if wiki_dir.exists() else 0,
            "source_page_count": len(source_pages),
            "index_entries": _count_index_entries(meta_dir / "index.md"),
            "log_entries": _count_log_entries(meta_dir / "log.md"),
        },
        "source_page_health": {
            "missing_raw_path_count": len(missing_raw_path),
            "missing_raw_path_pages": missing_raw_path,
            "duplicate_raw_path_owners": duplicate_raw_path_owners,
        },
        "warehouse_counts": warehouse_counts,
        "graph_projection": graph_projection,
        "docs_readiness": docs_readiness,
        "working_tree": _working_tree_health(base_root),
        "operator_readiness": operator_readiness,
    }


def render_doctor_payload(payload: dict[str, object]) -> str:
    status_payload = payload["status"]
    raw_counts = payload["raw_counts"]
    wiki_health = payload["wiki_health"]
    source_page_health = payload["source_page_health"]
    graph_projection = payload["graph_projection"]
    docs_readiness = payload["docs_readiness"]
    working_tree = payload["working_tree"]
    operator_readiness = payload["operator_readiness"]
    warehouse_counts = payload["warehouse_counts"]
    lines = [
        "Doctor report",
        f"- Root: {payload['root']}",
        f"- Raw total: {raw_counts['total']}",
        f"- Wiki pages: {wiki_health['wiki_page_count']}",
        f"- Source pages: {wiki_health['source_page_count']}",
        f"- Index entries: {status_payload['index_entries']}",
        f"- Log entries: {status_payload['log_entries']}",
        f"- Canonical rows: {sum(warehouse_counts[name] for name in WAREHOUSE_JSONL_REGISTRIES if name != 'derived_edges')}",
        f"- Derived edges: {warehouse_counts['derived_edges']}",
        f"- Graph projection available: {graph_projection['available']}",
        f"- Missing raw_path pages: {source_page_health['missing_raw_path_count']}",
        f"- Duplicate raw_path owners: {len(source_page_health['duplicate_raw_path_owners'])}",
        f"- Docs ready: {sum(1 for value in docs_readiness.values() if value)}/{len(docs_readiness)}",
        f"- Working tree clean: {working_tree['clean']}",
        "",
        "Working tree contamination",
        f"- Agent local: {working_tree['counts']['agent_local']}",
        f"- Runtime state: {working_tree['counts']['runtime_state']}",
        f"- Live workspace: {working_tree['counts']['live_workspace']}",
        f"- Durable repo change: {working_tree['counts']['durable_repo_change']}",
        f"- Other: {working_tree['counts']['other']}",
        "",
        "Operator readiness",
        f"- Production ingest entrypoint: {operator_readiness['production_ingest_entrypoint_exists']}",
        f"- Benchmark ingest entrypoint: {operator_readiness['benchmark_ingest_entrypoint_exists']}",
        f"- Shadow reconcile preview: {operator_readiness['shadow_reconcile_preview_exists']}",
        f"- Canonical truth non-empty: {operator_readiness['canonical_truth_nonempty']}",
    ]
    next_steps = operator_readiness["recommended_next_steps"]
    if next_steps:
        lines.extend(["", "Recommended next steps"] + [f"- {step}" for step in next_steps])
    return "\n".join(lines)


def rebuild_index() -> Path:
    pages_by_section: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for path in iter_markdown_pages():
        rel = path.relative_to(WIKI_DIR)
        content = read_text(path)
        if rel == Path("_meta/index.md"):
            continue
        title = page_title_from_content(path, content)
        summary = extract_summary(content)
        section = page_type_from_path(path)
        pages_by_section[section].append((path.stem, title, summary))

    index_path = META_DIR / "index.md"
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
        "This file is rebuilt by `python scripts/llm_wiki.py reindex`.",
        "",
    ]

    ordered_sections = ["_meta"] + VALID_PAGE_DIRS
    for section in ordered_sections:
        entries = sorted(pages_by_section.get(section, []), key=lambda item: item[1].lower())
        if not entries:
            continue
        heading = "Meta" if section == "_meta" else section.replace("-", " ").title()
        lines.extend([f"## {heading}", ""])
        for stem, title, summary in entries:
            lines.append(f"- [[{stem}]] - {summary}")
        lines.append("")

    out = META_DIR / "index.md"
    write_text(out, "\n".join(lines).rstrip() + "\n")
    return out


def append_log(kind: str, title: str, bullets: list[str]) -> Path:
    path = META_DIR / "log.md"
    existing = read_text(path) if path.exists() else "---\ntitle: Log\ntype: meta\nstatus: active\ncreated: {}\nupdated: {}\n---\n\n# Log\n".format(today(), today())
    entry_lines = [
        "",
        f"## [{today()}] {kind} | {title}",
        "",
    ]
    for bullet in bullets:
        entry_lines.append(f"- {bullet}")
    entry_lines.append("")
    write_text(path, existing.rstrip() + "\n" + "\n".join(entry_lines))
    return path


def ingest_source(raw_path_str: str, title: str | None) -> int:
    raw_path = (ROOT / raw_path_str).resolve() if not Path(raw_path_str).is_absolute() else Path(raw_path_str).resolve()
    if not raw_path.exists():
        print(f"Source not found: {raw_path}", file=sys.stderr)
        return 1

    if ROOT not in raw_path.parents and raw_path != ROOT:
        print("Source path must live inside this project.", file=sys.stderr)
        return 1

    source_title = title or raw_path.stem.replace("-", " ").replace("_", " ").title()
    filename = f"source-{today()}-{slugify(source_title)}.md"
    source_page = WIKI_DIR / "sources" / filename
    relative_raw_path = raw_path.relative_to(ROOT).as_posix()

    template = read_text(TEMPLATE_PATH)
    content = (
        template.replace("{{title}}", source_title)
        .replace("{{date}}", today())
        .replace("{{raw_path}}", relative_raw_path)
    )

    if source_page.exists():
        print(f"Source page already exists: {source_page.relative_to(ROOT)}")
    else:
        write_text(source_page, content)
        print(f"Created source page: {source_page.relative_to(ROOT)}")

    append_log(
        "ingest",
        source_title,
        [
            f"Registered source at `{relative_raw_path}`",
            f"Created or reused `[[{source_page.stem}]]`",
            "Pending LLM synthesis or ontology-backed ingest into the broader wiki",
        ],
    )
    rebuild_index()
    return 0


def lint_wiki() -> int:
    lookup = page_lookup()
    broken: list[tuple[Path, str]] = []
    orphans: list[Path] = []
    no_frontmatter: list[Path] = []
    unindexed: list[Path] = []
    oversized: list[tuple[Path, int]] = []
    duplicate_titles: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    inbound: dict[str, int] = defaultdict(int)
    indexed_stems = indexed_page_stems()

    for path in iter_markdown_pages():
        rel = path.relative_to(WIKI_DIR)
        content = read_text(path)
        title = page_title_from_content(path, content)
        line_count = len(content.splitlines())

        if rel != Path("_meta/index.md") and path.stem not in indexed_stems:
            unindexed.append(path)

        if rel.parts[0] != "_meta" and line_count > MAX_PAGE_LINES:
            oversized.append((path, line_count))

        duplicate_titles[title.casefold()].append((title, path))

        if not has_frontmatter(content):
            no_frontmatter.append(path)
        for link in wikilinks(content):
            if link in lookup:
                inbound[link] += 1
            else:
                broken.append((path, link))

    for stem, path in lookup.items():
        rel = path.relative_to(WIKI_DIR)
        if rel.parts[0] == "_meta":
            continue
        if inbound.get(stem, 0) == 0:
            orphans.append(path)

    duplicate_title_hits = [
        entries for entries in duplicate_titles.values() if len(entries) > 1
    ]

    log_path = META_DIR / "log.md"
    log_entries = 0
    log_rotation_warning = False
    if log_path.exists():
        log_entries = len(re.findall(r"^##\s+\[", read_text(log_path), re.MULTILINE))
        log_rotation_warning = log_entries > LOG_ROTATION_THRESHOLD

    print("Lint results")
    print("Hard failures")
    print(f"- Broken wikilinks: {len(broken)}")
    print(f"- Missing frontmatter: {len(no_frontmatter)}")
    print("")
    print("Advisory warnings")
    print(f"- Orphan pages: {len(orphans)}")
    print(f"- Unindexed pages: {len(unindexed)}")
    print(f"- Oversized pages (>{MAX_PAGE_LINES} lines): {len(oversized)}")
    print(f"- Duplicate titles: {len(duplicate_title_hits)}")
    print(f"- Log rotation warnings: {1 if log_rotation_warning else 0}")
    print("")

    if broken:
        print("Broken wikilinks:")
        for path, link in broken:
            print(f"- {path.relative_to(ROOT)} -> [[{link}]]")
        print("")

    if orphans:
        print("Orphan pages:")
        for path in orphans:
            print(f"- {path.relative_to(ROOT)}")
        print("")

    if unindexed:
        print("Pages missing from wiki/_meta/index.md:")
        for path in unindexed:
            print(f"- {path.relative_to(ROOT)}")
        print("")

    if oversized:
        print(f"Oversized pages (>{MAX_PAGE_LINES} lines):")
        for path, line_count in oversized:
            print(f"- {path.relative_to(ROOT)} ({line_count} lines)")
        print("")

    if duplicate_title_hits:
        print("Duplicate page titles:")
        for entries in duplicate_title_hits:
            title = entries[0][0]
            print(f"- {title}")
            for _, path in entries:
                print(f"  - {path.relative_to(ROOT)}")
        print("")

    if log_rotation_warning:
        print("Log rotation warning:")
        print(
            f"- wiki/_meta/log.md has {log_entries} entries; rotate it after {LOG_ROTATION_THRESHOLD} entries."
        )
        print("")

    if no_frontmatter:
        print("Pages missing frontmatter:")
        for path in no_frontmatter:
            print(f"- {path.relative_to(ROOT)}")
        print("")

    return 1 if broken or no_frontmatter else 0


def status(json_output: bool = False) -> int:
    payload = build_status_payload(ROOT)
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_status_payload(payload))
    return 0


def doctor(json_output: bool = False) -> int:
    payload = build_doctor_payload(ROOT)
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_doctor_payload(payload))
    return 0


def log_command(kind: str, title: str, bullets: list[str]) -> int:
    append_log(kind, title, bullets or ["No details recorded."])
    print(f"Appended {kind} entry to wiki/_meta/log.md")
    return 0


def reconcile_shadow(root_override: str | None) -> int:
    base_root = Path(root_override).resolve() if root_override else ROOT
    preview_path = base_root / "wiki" / "state" / "ontology_reconcile_preview.json"
    if not preview_path.exists():
        print(f"Shadow preview not found: {preview_path}", file=sys.stderr)
        return 1
    payload = json.loads(read_text(preview_path))
    affected = payload.get("affected_source_pages") or []
    print("Ontology reconcile shadow preview")
    print(f"- Root: {base_root}")
    print(f"- Preview: {preview_path.relative_to(base_root)}")
    print(f"- Affected source pages: {len(affected)}")
    for stem in affected:
        print(f"  - {stem}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local tooling for an Obsidian-first LLM Wiki. `ingest` is source registration only."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser(
        "ingest",
        help="Register a raw source and create a source page stub. This is not ontology-backed ingest.",
    )
    ingest.add_argument("path", help="Path to the raw source, absolute or relative to project root.")
    ingest.add_argument("--title", help="Human-readable title for the source page.")

    sub.add_parser("reindex", help="Rebuild wiki/_meta/index.md")
    sub.add_parser("lint", help="Check for broken links, orphans, and missing frontmatter.")
    status_parser = sub.add_parser("status", help="Show counts and basic wiki health metrics.")
    status_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    doctor_parser = sub.add_parser("doctor", help="Show runtime, truth-density, and working-tree diagnostics.")
    doctor_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")

    reconcile = sub.add_parser("reconcile-shadow", help="Print the current ontology shadow reconciliation preview.")
    reconcile.add_argument("--root", default=None, help="Optional project root override containing wiki/state/ontology_reconcile_preview.json.")

    log_parser = sub.add_parser("log", help="Append a structured log entry.")
    log_parser.add_argument("kind", help="Entry type such as ingest, query, lint, or refactor.")
    log_parser.add_argument("title", help="Short title for the log entry.")
    log_parser.add_argument(
        "details",
        nargs="*",
        help="Optional bullet items for the log entry.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest":
        return ingest_source(args.path, args.title)
    if args.command == "reindex":
        out = rebuild_index()
        print(f"Rebuilt {out.relative_to(ROOT)}")
        return 0
    if args.command == "lint":
        return lint_wiki()
    if args.command == "status":
        return status(args.json)
    if args.command == "doctor":
        return doctor(args.json)
    if args.command == "reconcile-shadow":
        return reconcile_shadow(args.root)
    if args.command == "log":
        return log_command(args.kind, args.title, args.details)

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
