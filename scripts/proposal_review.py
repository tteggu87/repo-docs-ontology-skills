#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.intelligence_contracts import load_proposal_policy


def _safe_repo_path(root: Path, value: str) -> Path:
    path = (root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("path must stay inside repository") from exc
    return path


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text[4:end]) or {}
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    return data, text[end + 4 :].lstrip("\n")


def _render_frontmatter(data: dict[str, Any], body: str) -> str:
    try:
        import yaml  # type: ignore

        frontmatter = yaml.safe_dump(data, allow_unicode=True, sort_keys=False).strip()
    except Exception:
        lines = [f"{key}: {value}" for key, value in data.items()]
        frontmatter = "\n".join(lines)
    return f"---\n{frontmatter}\n---\n\n{body.strip()}\n"


def _proposal_files(root: Path) -> list[Path]:
    analyses = root / "wiki" / "analyses"
    if not analyses.exists():
        return []
    out: list[Path] = []
    for path in sorted(analyses.glob("*compile-proposal*.md")):
        fm, _ = _split_frontmatter(path.read_text(encoding="utf-8"))
        if fm.get("analysis_method") == "llm_compile_proposal":
            out.append(path)
    return out


def list_proposals(root: Path) -> dict[str, Any]:
    proposals = []
    for path in _proposal_files(root):
        fm, _ = _split_frontmatter(path.read_text(encoding="utf-8"))
        proposals.append(
            {
                "path": _rel(root, path),
                "title": fm.get("title") or path.stem,
                "status": fm.get("status"),
                "trust_level": fm.get("trust_level"),
                "updated": fm.get("updated"),
            }
        )
    return {"status": "ok", "proposals": proposals}


def set_proposal_status(root: Path, proposal_path: str, status: str) -> dict[str, Any]:
    path = _safe_repo_path(root, proposal_path)
    policy = load_proposal_policy(root, "compile_proposal")
    allowed = policy.get("allowed_transitions", {}) or {}
    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)
    current = str(fm.get("status") or policy.get("initial_status"))
    if status not in allowed.get(current, []):
        raise ValueError(f"invalid proposal transition: {current} -> {status}")
    fm["status"] = status
    fm["updated"] = dt.date.today().isoformat()
    path.write_text(_render_frontmatter(fm, body), encoding="utf-8")
    return {"status": "ok", "proposal_path": _rel(root, path), "new_status": status}


def apply_reviewed_content(root: Path, proposal_path: str, target_path: str, content_file: str) -> dict[str, Any]:
    proposal = _safe_repo_path(root, proposal_path)
    target = _safe_repo_path(root, target_path)
    content = _safe_repo_path(root, content_file)
    target_rel = _rel(root, target)
    if not target_rel.startswith("wiki/"):
        raise ValueError("target must be under wiki/")
    if target_rel.startswith("wiki/_meta/"):
        raise ValueError("proposal apply target must not be wiki/_meta/")
    fm, _ = _split_frontmatter(proposal.read_text(encoding="utf-8"))
    if fm.get("status") != "accepted":
        raise ValueError("proposal must be accepted before apply")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.read_text(encoding="utf-8"), encoding="utf-8")
    result = set_proposal_status(root, proposal_path, "applied")
    result.update({"target_path": target_rel, "content_file": _rel(root, content)})
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Review and apply human-approved LLM compile proposals.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    status_parser = sub.add_parser("set-status")
    status_parser.add_argument("proposal_path")
    status_parser.add_argument("--status", required=True, choices=["accepted", "rejected"])
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("proposal_path")
    apply_parser.add_argument("--target", required=True)
    apply_parser.add_argument("--content-file", required=True)
    try:
        args = parser.parse_args()
        if args.command == "list":
            payload = list_proposals(ROOT)
        elif args.command == "set-status":
            payload = set_proposal_status(ROOT, args.proposal_path, args.status)
        else:
            payload = apply_reviewed_content(ROOT, args.proposal_path, args.target, args.content_file)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, FileNotFoundError) as error:
        print(json.dumps({"status": "error", "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
