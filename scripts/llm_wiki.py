#!/usr/bin/env python3
"""Minimal local tooling for an Obsidian-first LLM Wiki.

The `ingest` command performs source registration only.
It does not run ontology-backed extraction or full wiki synthesis.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
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
LOW_COVERAGE_MIN_CONTENT_LINES = 6
STALE_PAGE_DAYS = 90
UNCERTAINTY_MARKERS = [
    "todo",
    "tbd",
    "unclear",
    "uncertain",
    "needs review",
    "maybe",
    "possibly",
    "unknown",
]


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


def parse_frontmatter_date(content: str, field: str) -> dt.date | None:
    match = re.search(rf"^{field}:\s*(\d{{4}}-\d{{2}}-\d{{2}})\s*$", content, re.MULTILINE)
    if not match:
        return None
    try:
        return dt.date.fromisoformat(match.group(1))
    except ValueError:
        return None


def content_line_count(content: str) -> int:
    count = 0
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "---":
            continue
        if re.match(r"^(title|type|status|created|updated|tags|sources):", stripped):
            continue
        if stripped == "#":
            continue
        count += 1
    return count


def build_maintenance_plan() -> dict[str, object]:
    lookup = page_lookup()
    indexed_stems = indexed_page_stems()

    broken: list[tuple[Path, str]] = []
    no_frontmatter: list[Path] = []
    unindexed: list[Path] = []
    oversized: list[tuple[Path, int]] = []
    orphaned: list[Path] = []
    duplicate_titles: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    low_coverage: list[tuple[Path, int]] = []
    stale: list[tuple[Path, str]] = []
    uncertainty: list[Path] = []
    inbound: dict[str, int] = defaultdict(int)

    for path in iter_markdown_pages():
        rel = path.relative_to(WIKI_DIR)
        content = read_text(path)
        title = page_title_from_content(path, content)
        duplicate_titles[title.casefold()].append((title, path))

        if rel != Path("_meta/index.md") and path.stem not in indexed_stems:
            unindexed.append(path)

        if not has_frontmatter(content):
            no_frontmatter.append(path)

        line_count = len(content.splitlines())
        if rel.parts[0] != "_meta" and line_count > MAX_PAGE_LINES:
            oversized.append((path, line_count))

        if rel.parts[0] in {"concepts", "entities", "people", "projects", "timelines"}:
            body_lines = content_line_count(content)
            if body_lines < LOW_COVERAGE_MIN_CONTENT_LINES:
                low_coverage.append((path, body_lines))

        updated_at = parse_frontmatter_date(content, "updated")
        if updated_at is not None:
            age_days = (dt.date.today() - updated_at).days
            if age_days > STALE_PAGE_DAYS and rel.parts[0] != "_meta":
                stale.append((path, updated_at.isoformat()))

        lowered = content.casefold()
        if any(marker in lowered for marker in UNCERTAINTY_MARKERS):
            uncertainty.append(path)

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
            orphaned.append(path)

    duplicate_title_hits = [entries for entries in duplicate_titles.values() if len(entries) > 1]

    registered_raw_paths: set[str] = set()
    for path in (WIKI_DIR / "sources").glob("*.md"):
        content = read_text(path)
        registered_raw_paths.update(re.findall(r"raw/(?:inbox|processed|notes)/[^\s`)\]]+", content))

    unregistered_raw_inbox = []
    for raw_file in sorted((RAW_DIR / "inbox").rglob("*")):
        if not raw_file.is_file():
            continue
        rel_raw = raw_file.relative_to(ROOT).as_posix()
        if rel_raw not in registered_raw_paths:
            unregistered_raw_inbox.append(raw_file)

    return {
        "generated_on": today(),
        "broken_wikilinks": broken,
        "missing_frontmatter": no_frontmatter,
        "unindexed_pages": unindexed,
        "oversized_pages": oversized,
        "orphan_pages": orphaned,
        "duplicate_titles": duplicate_title_hits,
        "low_coverage_pages": low_coverage,
        "stale_pages": stale,
        "uncertainty_candidates": uncertainty,
        "unregistered_raw_inbox_files": unregistered_raw_inbox,
    }


def render_maintenance_plan(plan: dict[str, object]) -> str:
    def section(title: str, items: list[str]) -> list[str]:
        lines = [f"## {title}", ""]
        if not items:
            lines.append("- None")
        else:
            lines.extend(f"- {item}" for item in items)
        lines.append("")
        return lines

    lines = [
        "---",
        "title: Maintenance Plan",
        "type: meta",
        "status: active",
        f"created: {today()}",
        f"updated: {today()}",
        "---",
        "",
        "# Maintenance Plan",
        "",
        f"Generated by `python3 scripts/llm_wiki.py maintain` on {plan['generated_on']}.",
        "",
        "This plan reports mechanical maintenance candidates. It does not apply semantic rewrites to wiki pages or modify canonical warehouse registries.",
        "",
    ]

    lines.extend(
        section(
            "Broken wikilinks",
            [f"`{path.relative_to(ROOT)}` -> `[[{link}]]`" for path, link in plan["broken_wikilinks"]],
        )
    )
    lines.extend(section("Missing frontmatter", [f"`{path.relative_to(ROOT)}`" for path in plan["missing_frontmatter"]]))
    lines.extend(section("Unindexed pages", [f"`{path.relative_to(ROOT)}`" for path in plan["unindexed_pages"]]))
    lines.extend(
        section(
            f"Oversized pages (>{MAX_PAGE_LINES} lines)",
            [f"`{path.relative_to(ROOT)}` ({line_count} lines)" for path, line_count in plan["oversized_pages"]],
        )
    )
    lines.extend(section("Orphan pages", [f"`{path.relative_to(ROOT)}`" for path in plan["orphan_pages"]]))
    lines.extend(
        section(
            "Duplicate titles",
            [
                ", ".join(f"`{path.relative_to(ROOT)}`" for _, path in entries)
                for entries in plan["duplicate_titles"]
            ],
        )
    )
    lines.extend(
        section(
            "Low-coverage durable pages",
            [f"`{path.relative_to(ROOT)}` ({count} content lines)" for path, count in plan["low_coverage_pages"]],
        )
    )
    lines.extend(
        section(
            f"Stale pages (updated > {STALE_PAGE_DAYS} days ago)",
            [f"`{path.relative_to(ROOT)}` (updated {updated})" for path, updated in plan["stale_pages"]],
        )
    )
    lines.extend(
        section(
            "Uncertainty candidates",
            [f"`{path.relative_to(ROOT)}`" for path in plan["uncertainty_candidates"]],
        )
    )
    lines.extend(
        section(
            "Unregistered raw inbox files",
            [f"`{path.relative_to(ROOT)}`" for path in plan["unregistered_raw_inbox_files"]],
        )
    )
    return "\n".join(lines).rstrip() + "\n"


def maintenance_plan(write_plan: bool = False) -> int:
    plan = build_maintenance_plan()
    print("Maintenance plan summary")
    print(f"- Broken wikilinks: {len(plan['broken_wikilinks'])}")
    print(f"- Missing frontmatter: {len(plan['missing_frontmatter'])}")
    print(f"- Unindexed pages: {len(plan['unindexed_pages'])}")
    print(f"- Oversized pages: {len(plan['oversized_pages'])}")
    print(f"- Orphan pages: {len(plan['orphan_pages'])}")
    print(f"- Duplicate titles: {len(plan['duplicate_titles'])}")
    print(f"- Low-coverage durable pages: {len(plan['low_coverage_pages'])}")
    print(f"- Stale pages: {len(plan['stale_pages'])}")
    print(f"- Uncertainty candidates: {len(plan['uncertainty_candidates'])}")
    print(f"- Unregistered raw inbox files: {len(plan['unregistered_raw_inbox_files'])}")

    if write_plan:
        plan_path = META_DIR / "maintenance-plan.md"
        write_text(plan_path, render_maintenance_plan(plan))
        append_log(
            "maintain",
            "Bounded maintenance plan refresh",
            [
                f"Updated `[[{plan_path.stem}]]`",
                "Refreshed wiki maintenance findings without semantic rewrite",
            ],
        )
        rebuild_index()
        print(f"Wrote {plan_path.relative_to(ROOT)}")
    return 0


def status() -> int:
    markdown_pages = iter_markdown_pages()
    raw_files = [path for path in RAW_DIR.rglob("*") if path.is_file()]
    log_path = META_DIR / "log.md"
    index_path = META_DIR / "index.md"
    log_entries = 0
    index_entries = 0

    if log_path.exists():
        log_entries = len(re.findall(r"^##\s+\[", read_text(log_path), re.MULTILINE))
    if index_path.exists():
        index_entries = len(re.findall(r"^- \[\[", read_text(index_path), re.MULTILINE))

    print("LLM Wiki status")
    print(f"- Root: {ROOT}")
    print(f"- Raw files: {len(raw_files)}")
    print(f"- Wiki pages: {len(markdown_pages)}")
    print(f"- Log entries: {log_entries}")
    print(f"- Index entries: {index_entries}")
    return 0


def log_command(kind: str, title: str, bullets: list[str]) -> int:
    append_log(kind, title, bullets or ["No details recorded."])
    print(f"Appended {kind} entry to wiki/_meta/log.md")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local tooling for an Obsidian-first LLM Wiki. `ingest` is source registration only."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser(
        "ingest",
        help="Register a raw source (legacy name). Source registration only; not ontology-backed ingest.",
    )
    ingest.add_argument("path", help="Path to the raw source, absolute or relative to project root.")
    ingest.add_argument("--title", help="Human-readable title for the source page.")

    register_source = sub.add_parser(
        "register-source",
        help="Register a raw source and create a source page stub. Source registration only; not ontology-backed ingest.",
    )
    register_source.add_argument("path", help="Path to the raw source, absolute or relative to project root.")
    register_source.add_argument("--title", help="Human-readable title for the source page.")

    sub.add_parser("reindex", help="Rebuild wiki/_meta/index.md")
    sub.add_parser("lint", help="Check for broken links, orphans, and missing frontmatter.")
    maintain = sub.add_parser(
        "maintain",
        help="Generate a bounded maintenance report for wiki hygiene and source registration coverage.",
    )
    maintain.add_argument(
        "--write-plan",
        action="store_true",
        help="Write wiki/_meta/maintenance-plan.md and update log/index.",
    )
    sub.add_parser("status", help="Show counts and basic wiki health metrics.")

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

    if args.command in {"ingest", "register-source"}:
        return ingest_source(args.path, args.title)
    if args.command == "reindex":
        out = rebuild_index()
        print(f"Rebuilt {out.relative_to(ROOT)}")
        return 0
    if args.command == "lint":
        return lint_wiki()
    if args.command == "maintain":
        return maintenance_plan(args.write_plan)
    if args.command == "status":
        return status()
    if args.command == "log":
        return log_command(args.kind, args.title, args.details)

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
