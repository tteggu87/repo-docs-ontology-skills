from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from pathlib import Path


VALID_PAGE_DIRS = [
    "analyses",
    "concepts",
    "entities",
    "people",
    "projects",
    "sources",
    "timelines",
]


def today() -> str:
    return date.today().isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "untitled"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def page_title_from_content(path: Path, content: str) -> str:
    match = re.search(r'^title:\s*"?(.*?)"?\s*$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    heading = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if heading:
        return heading.group(1).strip()
    return path.stem.replace("-", " ").title()


def extract_summary(content: str) -> str:
    for line in (line.strip() for line in content.splitlines()):
        if not line or line.startswith("---") or line.startswith("#") or line.startswith("title:"):
            continue
        if line.startswith(("type:", "status:", "created:", "updated:")):
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


def iter_markdown_pages(root: Path) -> list[Path]:
    wiki_dir = root / "wiki"
    return sorted(path for path in wiki_dir.rglob("*.md") if path.is_file())


def rebuild_index(root: Path) -> Path:
    wiki_dir = root / "wiki"
    meta_dir = wiki_dir / "_meta"
    pages_by_section: dict[str, list[tuple[str, str, str]]] = defaultdict(list)

    for path in iter_markdown_pages(root):
        rel = path.relative_to(wiki_dir)
        if rel == Path("_meta/index.md"):
            continue
        content = read_text(path)
        section = rel.parts[0]
        pages_by_section[section].append((path.stem, page_title_from_content(path, content), extract_summary(content)))

    index_path = meta_dir / "index.md"
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
    for section in ["_meta"] + VALID_PAGE_DIRS:
        entries = sorted(pages_by_section.get(section, []), key=lambda item: item[1].lower())
        if not entries:
            continue
        heading = "Meta" if section == "_meta" else section.replace("-", " ").title()
        lines.extend([f"## {heading}", ""])
        for stem, _title, summary in entries:
            lines.append(f"- [[{stem}]] - {summary}")
        lines.append("")

    write_text(index_path, "\n".join(lines).rstrip() + "\n")
    return index_path


def append_log(root: Path, kind: str, title: str, bullets: list[str]) -> Path:
    path = root / "wiki" / "_meta" / "log.md"
    if path.exists():
        existing = read_text(path)
    else:
        existing = (
            "---\n"
            'title: "Log"\n'
            "type: meta\n"
            "status: active\n"
            f"created: {today()}\n"
            f"updated: {today()}\n"
            "---\n\n"
            "# Log\n"
        )
    entry = ["", f"## [{today()}] {kind} | {title}", ""]
    entry.extend(f"- {bullet}" for bullet in bullets)
    entry.append("")
    write_text(path, existing.rstrip() + "\n" + "\n".join(entry))
    return path


def source_page_path(root: Path, document: dict, raw_path: str) -> Path:
    title = str(document.get("title") or Path(raw_path).stem.replace("-", " ").replace("_", " ").title())
    doc_suffix = str(document.get("document_id") or "doc")[-8:]
    filename = f"source-{today()}-{slugify(title)}-{doc_suffix}.md"
    return root / "wiki" / "sources" / filename


def render_source_page(
    document: dict,
    source_version: dict,
    units: list[dict],
    warnings: list[str],
    raw_path: str,
) -> str:
    title = str(document.get("title") or Path(raw_path).stem.replace("-", " ").replace("_", " ").title())
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_raw_path = raw_path.replace("\\", "\\\\").replace('"', '\\"')
    page_stems = sorted({str(unit.get("heading") or "Untitled section") for unit in units if unit.get("heading")})
    if not page_stems:
        page_stems = ["No headings detected"]

    unit_lines = []
    for unit in units[:20]:
        heading = unit.get("heading") or "Untitled section"
        line_start = unit.get("line_start")
        line_end = unit.get("line_end")
        unit_lines.append(f"- `{unit.get('unit_id')}` — {heading} (lines {line_start}-{line_end})")
    if len(units) > 20:
        unit_lines.append(f"- ... {len(units) - 20} more units")
    if not unit_lines:
        unit_lines.append("- No content units generated.")

    warning_lines = [f"- {warning}" for warning in warnings] or ["- None"]
    heading_lines = [f"- {heading}" for heading in page_stems[:20]]

    return (
        "---\n"
        f'title: "{safe_title}"\n'
        "type: source\n"
        "status: active\n"
        f"created: {today()}\n"
        f"updated: {today()}\n"
        f"profile_id: {source_version.get('profile_id')}\n"
        f"source_family_id: {source_version.get('source_family_id')}\n"
        f"document_id: {source_version.get('document_id')}\n"
        f"latest_source_version_id: {source_version.get('source_version_id')}\n"
        f'raw_path: "{safe_raw_path}"\n'
        f"content_hash: {source_version.get('content_hash')}\n"
        f"unit_count: {source_version.get('unit_count')}\n"
        "tags:\n"
        "  - source\n"
        "  - llm-wiki\n"
        "---\n\n"
        f"# {title}\n\n"
        "## Source Metadata\n\n"
        f"- Profile: `{source_version.get('profile_id')}`\n"
        f"- Source family: `{source_version.get('source_family_id')}`\n"
        f"- Document ID: `{source_version.get('document_id')}`\n"
        f"- Source version ID: `{source_version.get('source_version_id')}`\n"
        f"- Raw path: `{raw_path}`\n"
        f"- Content hash: `{source_version.get('content_hash')}`\n"
        f"- Unit count: {source_version.get('unit_count')}\n\n"
        "## Warnings\n\n"
        + "\n".join(warning_lines)
        + "\n\n"
        "## Major Headings\n\n"
        + "\n".join(heading_lines)
        + "\n\n"
        "## Content Units\n\n"
        + "\n".join(unit_lines)
        + "\n\n"
        "## Next Suggested Actions\n\n"
        "- Run a profile-specific analysis draft when this source needs synthesis.\n"
        "- Use generated content unit citations in downstream analysis pages.\n"
    )


def project_source_page(root: Path, document: dict, source_version: dict, units: list[dict], warnings: list[str], raw_path: str) -> Path:
    path = source_page_path(root, document, raw_path)
    write_text(path, render_source_page(document, source_version, units, warnings, raw_path))
    return path


def refresh_wiki_after_ingest(
    root: Path,
    document: dict,
    source_version: dict,
    units: list[dict],
    warnings: list[str],
    raw_path: str,
) -> list[str]:
    source_page = project_source_page(root, document, source_version, units, warnings, raw_path)
    index_page = rebuild_index(root)
    log_page = append_log(
        root,
        "ingest",
        str(document.get("title") or Path(raw_path).stem),
        [
            f"Profile ingest source `{raw_path}`",
            f"profile_id={source_version.get('profile_id')} source_family_id={source_version.get('source_family_id')}",
            f"source_version_id={source_version.get('source_version_id')} unit_count={source_version.get('unit_count')}",
            f"Created or refreshed `[[{source_page.stem}]]`",
        ],
    )
    return [source_page.relative_to(root).as_posix(), index_page.relative_to(root).as_posix(), log_page.relative_to(root).as_posix()]
