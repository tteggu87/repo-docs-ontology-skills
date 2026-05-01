#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analysis_profiles.common import load_jsonl
from scripts.workbench.llm_config import (
    helper_model_public_summary,
    load_continue_helper_config,
    run_helper_chat_completion,
)


def _read(path: Path, max_chars: int = 12000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    return text[:max_chars]


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for raw in text[4:end].splitlines():
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def _wikilinks(text: str) -> list[str]:
    return sorted(set(re.findall(r"\[\[([^\]|#]+)", text)))


def _page_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.suffix == ".md":
        return (root / path).resolve() if not path.is_absolute() else path.resolve()
    for candidate in (root / "wiki").rglob(f"{value}.md"):
        return candidate.resolve()
    raise FileNotFoundError(f"wiki page not found: {value}")


def _safe_rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def build_compile_bundle(root: Path, source_page: str, max_page_chars: int = 12000) -> dict[str, Any]:
    source_path = _page_path(root, source_page)
    source_text = _read(source_path, max_page_chars)
    fm = _frontmatter(source_text)
    document_id = fm.get("document_id")
    raw_path = fm.get("raw_path")
    units = [
        unit
        for unit in load_jsonl(root / "warehouse/jsonl/content_units.jsonl")
        if not document_id or unit.get("document_id") == document_id
    ]
    related_pages: list[dict[str, str]] = []
    for stem in _wikilinks(source_text):
        try:
            related_path = _page_path(root, stem)
        except FileNotFoundError:
            continue
        if related_path == source_path:
            continue
        related_pages.append(
            {
                "path": _safe_rel(root, related_path),
                "stem": related_path.stem,
                "content": _read(related_path, max_page_chars // 2),
            }
        )

    index_text = _read(root / "wiki/_meta/index.md", max_page_chars)
    raw_text = _read(root / raw_path, max_page_chars) if raw_path else ""
    evidence_units = [
        {
            "unit_id": unit.get("unit_id"),
            "heading": unit.get("heading"),
            "line_start": unit.get("line_start"),
            "line_end": unit.get("line_end"),
            "text": str(unit.get("text") or "")[:1200],
        }
        for unit in units[:80]
    ]
    return {
        "source_page": _safe_rel(root, source_path),
        "document_id": document_id,
        "raw_path": raw_path,
        "source_page_markdown": source_text,
        "raw_excerpt": raw_text,
        "content_units": evidence_units,
        "wiki_index": index_text,
        "wiki_moc": _read(root / "wiki/_meta/moc.md", max_page_chars),
        "wiki_link_map": _read(root / "wiki/_meta/link-map.md", max_page_chars),
        "contradiction_review": _read(root / "wiki/_meta/contradiction-review.md", max_page_chars // 2),
        "source_coverage": _read(root / "wiki/_meta/source-coverage.md", max_page_chars // 2),
        "related_existing_pages": related_pages,
    }


SYSTEM_PROMPT = """You are an LLM Wiki compiler.
You do not write a final answer from heuristics.
Read the source page, raw excerpt, content units, wiki index, and linked pages as a structured knowledge substrate.
Return a JSON object with:
- pages_to_update: existing concept/entity/project/source/analysis pages to update, with rationale
- new_page_candidates: new wiki pages worth creating, with page type and rationale
- citation_links: source-backed citations using source page, unit_id, heading, and line range
- uncertainties: unknowns, contradictions, thin coverage, and open questions
- compile_notes_markdown: concise markdown synthesis for a human/agent to apply
Every semantic claim must cite content_units or source_page/raw evidence when possible.
If the bundle is insufficient, say so explicitly instead of inventing content."""


def build_user_prompt(bundle: dict[str, Any]) -> str:
    return json.dumps(bundle, ensure_ascii=False, indent=2)


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9가-힣._-]+", "-", value).strip("-._")
    return slug[:96] or "source"


def _proposal_markdown(bundle: dict[str, Any], llm_output: str) -> str:
    today = dt.date.today().isoformat()
    source_stem = Path(str(bundle["source_page"])).stem
    return "\n".join(
        [
            "---",
            f'title: "Compile Proposal - {source_stem}"',
            "type: analysis",
            "status: draft",
            "analysis_method: llm_compile_proposal",
            "trust_level: human_review_required",
            f"created: {today}",
            f"updated: {today}",
            "tags:",
            "  - llm-compile-proposal",
            "---",
            "",
            "# Compile Proposal",
            "",
            "## Source",
            "",
            f"- [[{source_stem}]]",
            f"- Source page path: `{bundle['source_page']}`",
            f"- Document ID: `{bundle.get('document_id') or 'unknown'}`",
            f"- Raw path: `{bundle.get('raw_path') or 'unknown'}`",
            "",
            "## Pages To Update",
            "",
            "_Review the LLM output below. Do not apply changes to active concept/entity/project pages until a human accepts them._",
            "",
            "## New Page Candidates",
            "",
            "_Review the LLM output below._",
            "",
            "## Citation Links",
            "",
            "_Every accepted semantic claim should keep source-page/content-unit citations._",
            "",
            "## Uncertainties",
            "",
            "_Preserve unresolved uncertainty instead of converting it into asserted wiki facts._",
            "",
            "## Human Review Checklist",
            "",
            "- [ ] Verify every proposed page update against cited source evidence.",
            "- [ ] Decide which proposed new pages should be created.",
            "- [ ] Reject unsupported or speculative semantic claims.",
            "- [ ] Apply accepted changes manually to active wiki pages.",
            "- [ ] Rebuild wiki graph navigation after applying changes.",
            "",
            "## LLM Compile Output",
            "",
            llm_output.strip(),
            "",
        ]
    )


def _save_compile_proposal(root: Path, bundle: dict[str, Any], llm_output: str) -> str:
    today = dt.date.today().isoformat()
    source_stem = Path(str(bundle["source_page"])).stem
    stem = f"analysis-{today}-compile-proposal-{_slug(source_stem)}"
    path = root / "wiki" / "analyses" / f"{stem}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_proposal_markdown(bundle, llm_output), encoding="utf-8")
    return _safe_rel(root, path)


def compile_source(root: Path, source_page: str, *, emit_bundle: bool = False, save_proposal: bool = True) -> dict[str, Any]:
    bundle = build_compile_bundle(root, source_page)
    user_prompt = build_user_prompt(bundle)
    config = load_continue_helper_config(root)
    if emit_bundle:
        return {
            "status": "prompt_bundle",
            "mode": "llm_compile_source",
            "source_page": bundle["source_page"],
            "llm_system_prompt": SYSTEM_PROMPT,
            "llm_user_prompt": user_prompt,
            "bundle": bundle,
            "message": "Explicit prompt bundle emission only; this is not semantic success.",
        }
    if not config or not config.get("enabled", True):
        raise RuntimeError("No enabled wikiconfig.json helper model found. Strict LLM mode refuses semantic compile without an LLM.")
    output = run_helper_chat_completion(config, system_prompt=SYSTEM_PROMPT, user_prompt=user_prompt, temperature=0.1)
    result = {
        "status": "ok",
        "mode": "llm_compile_source",
        "source_page": bundle["source_page"],
        "helper_model": helper_model_public_summary(config),
        "llm_output": output,
    }
    if save_proposal:
        result["proposal_path"] = _save_compile_proposal(root, bundle, output)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM-first source compile workflow for DocTology.")
    parser.add_argument("--source-page", required=True, help="Source page stem or path, e.g. source-2026-... or wiki/sources/source-....md")
    parser.add_argument("--emit-bundle", action="store_true", help="Explicitly print the LLM prompt/evidence bundle instead of calling the helper model.")
    args = parser.parse_args()
    try:
        print(json.dumps(compile_source(ROOT, args.source_page, emit_bundle=args.emit_bundle), ensure_ascii=False, indent=2))
        return 0
    except RuntimeError as error:
        print(json.dumps({"status": "error", "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
