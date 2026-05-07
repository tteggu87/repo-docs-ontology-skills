#!/usr/bin/env python3
"""Structural route checker for DocTology source ingest.

This checker is intentionally structural. It reports whether a source has been
registered, projected to a source page, reported, indexed, and logged. It never
claims semantic truth and it never upgrades pending JSONL/wiki projection work
to completion.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "AGENTS.md").exists():
            return candidate
    return current


def relative_to_root(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def check_item(name: str, status: str, message: str = "", **extra: Any) -> dict[str, Any]:
    item: dict[str, Any] = {"name": name, "status": status}
    if message:
        item["message"] = message
    item.update(extra)
    return item


def resolve_source(root: Path, source: str) -> Path:
    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = root / source_path
    return source_path.resolve()


def source_rel_or_display(root: Path, source_path: Path) -> str:
    try:
        return relative_to_root(root, source_path)
    except Exception:
        return str(source_path)


def source_is_inside_repo(root: Path, source_path: Path) -> bool:
    try:
        source_path.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def source_is_under_raw(root: Path, source_path: Path) -> bool:
    try:
        rel = source_path.relative_to(root.resolve()).as_posix()
    except ValueError:
        return False
    return rel == "raw" or rel.startswith("raw/")


def find_source_page(root: Path, raw_path: Path) -> Path | None:
    sources_dir = root / "wiki" / "sources"
    if not sources_dir.exists():
        return None
    try:
        relative = relative_to_root(root, raw_path)
    except Exception:
        return None
    patterns = [
        f'raw_path: "{relative}"',
        f"raw_path: {relative}",
        f"- Raw path: `{relative}`",
        f"Raw path: `{relative}`",
    ]
    for path in sorted(sources_dir.glob("*.md")):
        try:
            text = read_text(path)
        except Exception:
            continue
        if any(pattern in text for pattern in patterns):
            return path
    return None


def find_handoff(root: Path, raw_path: Path) -> Path | None:
    handoff_dir = root / "wiki" / "_meta" / "handoff"
    if not handoff_dir.exists():
        return None
    try:
        relative = relative_to_root(root, raw_path)
    except Exception:
        return None
    for path in sorted(handoff_dir.glob("handoff-*.md"), reverse=True):
        try:
            text = read_text(path)
        except Exception:
            continue
        if f'raw_path: "{relative}"' in text or f"raw_path: {relative}" in text:
            return path
    return None


def find_ingest_report(root: Path, raw_path: Path, source_page: Path | None) -> Path | None:
    reports_dir = root / "wiki" / "_meta" / "ingest_reports"
    if not reports_dir.exists():
        return None
    try:
        relative = relative_to_root(root, raw_path)
    except Exception:
        relative = raw_path.name
    source_stem = source_page.stem if source_page else ""
    patterns = [
        f"- Raw path: `{relative}`",
        f"Raw path: `{relative}`",
    ]
    if source_stem:
        patterns.append(f"[[{source_stem}]]")
    for path in sorted(reports_dir.glob("ingest-*.md"), reverse=True):
        try:
            text = read_text(path)
        except Exception:
            continue
        if any(pattern in text for pattern in patterns):
            return path
    return None


def index_mentions(root: Path, path: Path | None) -> bool:
    if path is None:
        return False
    index_path = root / "wiki" / "_meta" / "index.md"
    if not index_path.exists():
        return False
    return f"[[{path.stem}]]" in read_text(index_path)


def log_mentions(root: Path, raw_path: Path, source_page: Path | None, report: Path | None) -> bool:
    log_path = root / "wiki" / "_meta" / "log.md"
    if not log_path.exists():
        return False
    text = read_text(log_path)
    try:
        raw_rel = relative_to_root(root, raw_path)
    except Exception:
        raw_rel = ""
    needles = [f"`{raw_rel}`"] if raw_rel else []
    if source_page is not None:
        needles.append(f"[[{source_page.stem}]]")
    if report is not None:
        needles.append(f"[[{report.stem}]]")
    return any(needle and needle in text for needle in needles)


def aggregate_status(checks: list[dict[str, Any]]) -> str:
    if any(item["status"] == "failed" for item in checks):
        return "failed"
    if any(item["status"] == "pending" for item in checks):
        return "pending"
    if any(item["status"] == "warning" for item in checks):
        return "warning"
    return "ok"


def check_source(root: Path, source: str) -> dict[str, Any]:
    root = root.resolve()
    source_path = resolve_source(root, source)
    source_display = source_rel_or_display(root, source_path)
    checks: list[dict[str, Any]] = []

    if not (root / "AGENTS.md").exists():
        checks.append(check_item("repo_contract_exists", "failed", "AGENTS.md is required"))
    else:
        checks.append(check_item("repo_contract_exists", "ok"))

    if not source_is_inside_repo(root, source_path):
        checks.append(check_item("source_inside_repo", "failed", "source must live inside the repo"))
    else:
        checks.append(check_item("source_inside_repo", "ok"))

    if not source_path.exists():
        checks.append(check_item("source_exists", "failed", "source path does not exist", path=source_display))
        status = aggregate_status(checks)
        return {
            "status": status,
            "semantic_status": "not_started",
            "source": source_display,
            "source_page_stage": "failed",
            "checks": checks,
        }

    checks.append(check_item("source_exists", "ok", path=source_display))

    if source_is_under_raw(root, source_path):
        checks.append(check_item("source_under_raw", "ok"))
    else:
        checks.append(check_item("source_under_raw", "warning", "recommended source location is raw/**"))

    source_page = find_source_page(root, source_path)
    handoff = find_handoff(root, source_path)
    report = find_ingest_report(root, source_path, source_page)

    if source_page is None:
        if handoff is not None:
            checks.append(
                check_item(
                    "source_page_exists",
                    "pending",
                    "handoff exists, but source page projection is pending",
                    handoff=relative_to_root(root, handoff),
                )
            )
        else:
            checks.append(check_item("source_page_exists", "pending", "source registration/projection is pending"))
        checks.append(check_item("ingest_report_exists", "pending", "source-page ingest report is pending"))
        checks.append(check_item("index_mentions_source_page", "pending", "source page is pending"))
        checks.append(check_item("log_mentions_source", "pending", "source page/log closure is pending"))
        checks.append(check_item("jsonl_projection", "pending", "JSONL proposal/review is outside MVP"))
        checks.append(check_item("broader_wiki_projection", "pending", "concept/entity wiki projection is outside MVP"))
        status = aggregate_status(checks)
        return {
            "status": status,
            "semantic_status": "pending",
            "source": source_display,
            "source_page_stage": "pending",
            "source_page": None,
            "handoff": relative_to_root(root, handoff) if handoff else None,
            "checks": checks,
        }

    source_page_rel = relative_to_root(root, source_page)
    checks.append(check_item("source_page_exists", "ok", path=source_page_rel))

    if report is None:
        checks.append(check_item("ingest_report_exists", "pending", "source-page ingest report is pending"))
    else:
        checks.append(check_item("ingest_report_exists", "ok", path=relative_to_root(root, report)))

    checks.append(
        check_item(
            "index_mentions_source_page",
            "ok" if index_mentions(root, source_page) else "pending",
            "" if index_mentions(root, source_page) else "wiki/_meta/index.md does not mention the source page yet",
        )
    )
    if report is not None:
        checks.append(
            check_item(
                "index_mentions_ingest_report",
                "ok" if index_mentions(root, report) else "pending",
                "" if index_mentions(root, report) else "wiki/_meta/index.md does not mention the ingest report yet",
            )
        )

    checks.append(
        check_item(
            "log_mentions_source",
            "ok" if log_mentions(root, source_path, source_page, report) else "pending",
            "" if log_mentions(root, source_path, source_page, report) else "wiki/_meta/log.md does not mention this source stage yet",
        )
    )
    checks.append(check_item("jsonl_projection", "pending", "JSONL proposal/review is outside MVP"))
    checks.append(check_item("broader_wiki_projection", "pending", "concept/entity wiki projection is outside MVP"))
    checks.append(check_item("review_gate", "pending", "accepted truth requires a later review gate"))

    source_page_stage = "ok" if report is not None and index_mentions(root, source_page) else "pending"
    status = aggregate_status(checks)
    return {
        "status": status,
        "semantic_status": "pending_broader_projection",
        "source": source_display,
        "source_page_stage": source_page_stage,
        "source_page": source_page_rel,
        "handoff": relative_to_root(root, handoff) if handoff else None,
        "ingest_report": relative_to_root(root, report) if report else None,
        "checks": checks,
    }


def render_human(result: dict[str, Any]) -> str:
    lines = [
        f"Status: {result.get('status')}",
        f"Semantic status: {result.get('semantic_status')}",
        f"Source: {result.get('source')}",
        f"Source-page stage: {result.get('source_page_stage')}",
        "",
        "Checks:",
    ]
    for item in result.get("checks", []):
        line = f"- {item['name']}: {item['status']}"
        if item.get("message"):
            line += f" — {item['message']}"
        lines.append(line)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DocTology structural source ingest route checker.")
    parser.add_argument("--root", default=".", help="DocTology repo root. Defaults to current directory.")
    parser.add_argument("--source", required=True, help="Source path to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = find_repo_root(Path(args.root))
    result = check_source(root, args.source)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_human(result))
    return 1 if result.get("status") == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
