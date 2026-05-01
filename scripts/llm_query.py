#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.workbench.llm_config import (
    helper_model_public_summary,
    load_continue_helper_config,
    run_helper_chat_completion,
)


def _read(path: Path, max_chars: int = 16000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")[:max_chars]


def _wikilinks(text: str) -> list[str]:
    return sorted(set(re.findall(r"\[\[([^\]|#]+)", text)))


def _page_inventory(root: Path) -> list[dict[str, str]]:
    pages: list[dict[str, str]] = []
    for path in sorted((root / "wiki").rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        text = _read(path, 2200)
        title = path.stem
        match = re.search(r"^title:\s*\"?(.+?)\"?\s*$", text, re.MULTILINE)
        if match:
            title = match.group(1)
        pages.append({"stem": path.stem, "path": rel, "title": title, "preview": text[:1200]})
    return pages


def _resolve_page(root: Path, stem: str) -> Path | None:
    for path in (root / "wiki").rglob(f"{stem}.md"):
        return path
    return None


SELECT_SYSTEM_PROMPT = """You are an LLM Wiki navigation agent.
Given a user question and a wiki page inventory, select the pages that should be read before answering.
Do not answer yet.
Return strict JSON:
{"selected_page_stems": ["..."], "selection_rationale": "...", "missing_information": ["..."]}.
Prefer concept/entity/source/analysis pages that carry explanatory structure, not just lexical overlap."""


ANSWER_SYSTEM_PROMPT = """You are an LLM-first Obsidian/Ontology reasoning agent.
Use the provided wiki pages, wikilink neighborhood, and source citations as the primary reasoning surface.
This is not simple RAG context stuffing and not a heuristic answer draft.
Answer the user question with:
1. direct answer
2. evidence and citations from source/wiki pages
3. inference boundaries
4. uncertainty / missing information
5. suggested wiki updates if useful
Do not invent facts beyond the provided wiki/ontology/source material."""


def _parse_selected_stems(text: str) -> list[str]:
    data = json.loads(text)
    stems = data.get("selected_page_stems", [])
    if not isinstance(stems, list):
        raise ValueError("LLM page selection must return selected_page_stems as a list.")
    return [str(stem) for stem in stems if str(stem).strip()]


def build_query_bundle(root: Path, question: str, selected_stems: list[str] | None = None, max_pages: int = 8) -> dict[str, Any]:
    inventory = _page_inventory(root)
    pages: list[dict[str, str]] = []
    stems = selected_stems or []
    neighborhood: set[str] = set(stems)
    for stem in stems[:max_pages]:
        path = _resolve_page(root, stem)
        if not path:
            continue
        text = _read(path)
        pages.append({"stem": path.stem, "path": path.relative_to(root).as_posix(), "content": text})
        neighborhood.update(_wikilinks(text))

    for stem in sorted(neighborhood):
        if len(pages) >= max_pages * 2:
            break
        if any(page["stem"] == stem for page in pages):
            continue
        path = _resolve_page(root, stem)
        if not path:
            continue
        pages.append({"stem": path.stem, "path": path.relative_to(root).as_posix(), "content": _read(path, 9000)})

    return {
        "question": question,
        "wiki_index": _read(root / "wiki/_meta/index.md"),
        "wiki_moc": _read(root / "wiki/_meta/moc.md"),
        "wiki_link_map": _read(root / "wiki/_meta/link-map.md"),
        "orphan_review": _read(root / "wiki/_meta/orphan-review.md", 8000),
        "contradiction_review": _read(root / "wiki/_meta/contradiction-review.md", 8000),
        "source_coverage": _read(root / "wiki/_meta/source-coverage.md", 8000),
        "selected_pages": pages,
        "page_inventory_count": len(inventory),
    }


def llm_query(root: Path, question: str, *, emit_selection_prompt: bool = False) -> dict[str, Any]:
    inventory = _page_inventory(root)
    selection_prompt = json.dumps({"question": question, "page_inventory": inventory}, ensure_ascii=False, indent=2)
    config = load_continue_helper_config(root)
    if emit_selection_prompt:
        return {
            "status": "selection_prompt",
            "mode": "llm_query",
            "llm_selection_system_prompt": SELECT_SYSTEM_PROMPT,
            "llm_selection_user_prompt": selection_prompt,
            "message": "Explicit selection prompt emission only; this is not semantic success.",
        }
    if not config or not config.get("enabled", True):
        raise RuntimeError("No enabled wikiconfig.json helper model found. Strict LLM mode refuses semantic query without an LLM.")

    selection_output = run_helper_chat_completion(config, system_prompt=SELECT_SYSTEM_PROMPT, user_prompt=selection_prompt, temperature=0.1)
    selected_stems = _parse_selected_stems(selection_output)
    bundle = build_query_bundle(root, question, selected_stems)
    answer_prompt = json.dumps(bundle, ensure_ascii=False, indent=2)
    answer = run_helper_chat_completion(config, system_prompt=ANSWER_SYSTEM_PROMPT, user_prompt=answer_prompt, temperature=0.2)
    return {
        "status": "ok",
        "mode": "llm_query",
        "helper_model": helper_model_public_summary(config),
        "selection_output": selection_output,
        "selected_page_stems": selected_stems,
        "answer_markdown": answer,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="LLM-first wiki/ontology query workflow for DocTology.")
    parser.add_argument("question")
    parser.add_argument("--emit-selection-prompt", action="store_true", help="Explicitly print the first LLM page-selection prompt instead of calling the helper model.")
    args = parser.parse_args()
    try:
        print(json.dumps(llm_query(ROOT, args.question, emit_selection_prompt=args.emit_selection_prompt), ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "error", "message": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
