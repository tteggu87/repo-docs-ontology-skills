#!/usr/bin/env python3
"""Real-LangGraph automated source-page growth runtime for DocTology.

This is the strict automated graph ingest surface. It requires LangGraph and a
configured ingest LLM for ingest modes. It never falls back to deterministic
semantic drafting, and it keeps `scripts/llm_wiki.py ingest` registration-only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import helper_llm  # noqa: E402
import llm_full_ingest  # noqa: E402


class WikiGrowthState(TypedDict, total=False):
    root: str
    source: str
    source_path: str
    source_text: str
    source_page: str
    source_page_before: str
    source_page_after: str
    mode: str
    config_path: str | None
    title: str | None
    max_source_chars: int
    max_tokens: int
    temperature: float
    llm_response: str
    draft: dict[str, Any]
    validation: dict[str, Any]
    changed_files: list[str]
    report_path: str
    lifecycle_status: str
    semantic_status: str
    meta_errors: list[str]


ALLOWED_APPLY_PREFIXES = (
    "wiki/sources/",
    "wiki/_meta/ingest_reports/",
)
ALLOWED_APPLY_EXACT = {
    "wiki/_meta/index.md",
    "wiki/_meta/log.md",
}


def today() -> str:
    return dt.date.today().isoformat()


def timestamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def json_dump(payload: dict[str, Any], *, stderr: bool = False) -> None:
    stream = sys.stderr if stderr else sys.stdout
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=stream)


def require_langgraph():
    try:
        from langgraph.graph import END, START, StateGraph
    except Exception as exc:  # pragma: no cover - exact import failure varies by env
        raise RuntimeError(
            "LangGraph is required for wiki_growth_graph.py ingest. "
            "Install langgraph or use the agent-operated DocTology workflow instead."
        ) from exc
    return StateGraph, START, END


def require_repo_contract(root: Path) -> None:
    if not (root / "AGENTS.md").exists():
        raise RuntimeError("AGENTS.md is required at the DocTology repo root")
    if not (root / "scripts" / "llm_wiki.py").exists():
        raise RuntimeError("scripts/llm_wiki.py is required and must remain registration-only")


def resolve_root(root_arg: str) -> Path:
    root = helper_llm.find_repo_root(Path(root_arg))
    require_repo_contract(root)
    return root.resolve()


def resolve_source(root: Path, source_arg: str) -> Path:
    source_path = Path(source_arg)
    if not source_path.is_absolute():
        source_path = root / source_path
    source_path = source_path.resolve()
    try:
        rel = source_path.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise RuntimeError("source must live inside the repo root") from exc
    if not source_path.exists():
        raise RuntimeError(f"source not found: {rel}")
    if not (rel == "raw" or rel.startswith("raw/")):
        raise RuntimeError("graph ingest sources must live under raw/**")
    return source_path


def relative_to_root(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def assert_safe_write(root: Path, target: Path, mode: str) -> None:
    try:
        rel = relative_to_root(root, target)
    except Exception as exc:
        raise RuntimeError(f"Unsafe write target outside repo: {target}") from exc
    if rel.startswith("raw/") or rel in {"raw", "AGENTS.md"}:
        raise RuntimeError(f"Unsafe write target: {rel}")
    if rel.startswith("scripts/") or rel.startswith("intelligence/") or rel.startswith("warehouse/jsonl/"):
        raise RuntimeError(f"Unsafe write target: {rel}")
    if rel.startswith("wiki/concepts/") or rel.startswith("wiki/entities/") or rel.startswith("wiki/projects/"):
        raise RuntimeError(f"Unsafe write target: {rel}")
    if mode == "apply-source-page":
        if rel in ALLOWED_APPLY_EXACT:
            return
        if any(rel.startswith(prefix) for prefix in ALLOWED_APPLY_PREFIXES):
            return
        raise RuntimeError(f"Mode {mode} cannot write {rel}")


def write_text_safe(root: Path, target: Path, content: str, mode: str) -> None:
    assert_safe_write(root, target, mode)
    write_text(target, content)


def run_llm_wiki(root: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(root / "scripts" / "llm_wiki.py"), *args]
    return subprocess.run(cmd, cwd=root, text=True, capture_output=True, check=False, timeout=timeout)


def run_llm_wiki_checked(root: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    result = run_llm_wiki(root, *args, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            f"llm_wiki.py {' '.join(args)} failed with exit {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )
    return result


def register_source_if_needed(root: Path, raw_path: Path, title: str | None) -> Path:
    source_page = llm_full_ingest.find_source_page_by_raw_path(root, raw_path)
    if source_page is not None:
        return source_page
    args = ["ingest", relative_to_root(root, raw_path)]
    if title:
        args.extend(["--title", title])
    run_llm_wiki_checked(root, *args)
    source_page = llm_full_ingest.find_source_page_by_raw_path(root, raw_path)
    if source_page is None:
        raise RuntimeError("source registration completed but matching source page could not be found")
    return source_page


def load_context_node(state: WikiGrowthState) -> WikiGrowthState:
    root = Path(state["root"])
    require_repo_contract(root)
    state["lifecycle_status"] = "contract_loaded"
    return state


def load_memory_node(state: WikiGrowthState) -> WikiGrowthState:
    root = Path(state["root"])
    raw_path = Path(state["source_path"])
    source_text = llm_full_ingest.safe_read(raw_path, max_chars=int(state.get("max_source_chars", 60_000)))
    source_page = llm_full_ingest.find_source_page_by_raw_path(root, raw_path)
    state["source_text"] = source_text
    if source_page is not None:
        state["source_page"] = str(source_page)
        state["source_page_before"] = read_text(source_page)
    return state


def require_configured_llm_node(state: WikiGrowthState) -> WikiGrowthState:
    root = Path(state["root"])
    config_path = helper_llm.config_path_for_root(root, state.get("config_path"))
    config = helper_llm.load_helper_config(root, str(config_path))
    if not config.enabled or config.chat_model is None:
        raise RuntimeError("configured ingest LLM is not enabled/configured")
    state["config_path"] = str(config_path)
    return state


def draft_source_page_node(state: WikiGrowthState) -> WikiGrowthState:
    root = Path(state["root"])
    raw_path = Path(state["source_path"])
    config = helper_llm.load_helper_config(root, state.get("config_path"))
    source_page = Path(state["source_page"]) if state.get("source_page") else None
    context = llm_full_ingest.load_context(root)
    system_prompt, user_prompt = llm_full_ingest.build_prompt(
        root,
        raw_path,
        source_page,
        state["source_text"],
        context,
    )
    response = helper_llm.chat_completion(
        config,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=float(state.get("temperature", 0.2)),
        max_tokens=int(state.get("max_tokens", 3500)),
    )
    draft = llm_full_ingest.parse_json_response(response)
    state["llm_response"] = response
    state["draft"] = draft
    state["lifecycle_status"] = "draft_created"
    state["semantic_status"] = "draft_pending_apply"
    return state


def validate_draft_node(state: WikiGrowthState) -> WikiGrowthState:
    source_page_after: str | None = None
    if state.get("source_page"):
        source_page_after = llm_full_ingest.build_source_page_content(state.get("source_page_before", ""), state["draft"])
        state["source_page_after"] = source_page_after
    validation = llm_full_ingest.validate_draft(state["draft"], source_page_after)
    # Always gate summary/proposed-claim validity before any write.
    llm_full_ingest.assert_apply_safe({**validation, "remaining_TBD_count": validation.get("remaining_TBD_count", 0)})
    state["validation"] = validation
    return state


def apply_source_page_node(state: WikiGrowthState) -> WikiGrowthState:
    root = Path(state["root"])
    raw_path = Path(state["source_path"])
    changed_files: list[str] = []
    meta_errors: list[str] = []

    source_page = register_source_if_needed(root, raw_path, state.get("title"))
    source_page_before = read_text(source_page)
    source_page_after = llm_full_ingest.build_source_page_content(source_page_before, state["draft"])
    validation = llm_full_ingest.validate_draft(state["draft"], source_page_after)
    llm_full_ingest.assert_apply_safe(validation)
    diff_text = llm_full_ingest.unified_diff(
        source_page_before,
        source_page_after,
        fromfile=relative_to_root(root, source_page),
        tofile=relative_to_root(root, source_page) + " (draft)",
    )

    write_text_safe(root, source_page, source_page_after, "apply-source-page")
    changed_files.append(relative_to_root(root, source_page))

    expected_report_path = (
        root
        / "wiki"
        / "_meta"
        / "ingest_reports"
        / f"ingest-{llm_full_ingest.today()}-{llm_full_ingest.slugify(source_page.stem)}.md"
    )
    assert_safe_write(root, expected_report_path, "apply-source-page")
    report_path = llm_full_ingest.write_ingest_report(
        root,
        raw_path,
        source_page,
        state["draft"],
        "apply_source_page",
        changed_files,
        diff_text,
        validation,
    )
    assert_safe_write(root, report_path, "apply-source-page")
    changed_files.append(relative_to_root(root, report_path))

    reindex = run_llm_wiki(root, "reindex")
    if reindex.returncode != 0:
        meta_errors.append(f"reindex failed: {reindex.stderr or reindex.stdout}")

    log_details = [
        f"Applied configured LLM source-page growth for `{relative_to_root(root, raw_path)}`",
        f"Updated `[[{source_page.stem}]]`",
        f"Report `[[{report_path.stem}]]`",
        "Broader JSONL/wiki projection remains pending.",
    ]
    log_result = run_llm_wiki(
        root,
        "log",
        "ingest",
        f"LangGraph source-page growth: {raw_path.name}",
        *log_details,
    )
    if log_result.returncode != 0:
        meta_errors.append(f"log failed: {log_result.stderr or log_result.stdout}")

    state["source_page"] = str(source_page)
    state["source_page_before"] = source_page_before
    state["source_page_after"] = source_page_after
    state["validation"] = validation
    state["changed_files"] = changed_files
    state["report_path"] = relative_to_root(root, report_path)
    state["meta_errors"] = meta_errors
    state["lifecycle_status"] = "partial_meta_failed" if meta_errors else "partial_source_page_applied"
    state["semantic_status"] = "pending_broader_projection"
    return state


def route_after_validate(state: WikiGrowthState) -> str:
    if state.get("mode") == "apply-source-page":
        return "apply"
    return "done"


def build_graph():
    StateGraph, START, END = require_langgraph()
    graph = StateGraph(WikiGrowthState)
    graph.add_node("load_contract", load_context_node)
    graph.add_node("load_memory", load_memory_node)
    graph.add_node("require_configured_llm", require_configured_llm_node)
    graph.add_node("draft_source_page", draft_source_page_node)
    graph.add_node("validate_draft", validate_draft_node)
    graph.add_node("apply_source_page", apply_source_page_node)
    graph.add_edge(START, "load_contract")
    graph.add_edge("load_contract", "load_memory")
    graph.add_edge("load_memory", "require_configured_llm")
    graph.add_edge("require_configured_llm", "draft_source_page")
    graph.add_edge("draft_source_page", "validate_draft")
    graph.add_conditional_edges("validate_draft", route_after_validate, {"apply": "apply_source_page", "done": END})
    graph.add_edge("apply_source_page", END)
    return graph.compile()


def state_output(state: WikiGrowthState) -> dict[str, Any]:
    root = Path(state["root"])
    output: dict[str, Any] = {
        "status": "error" if state.get("meta_errors") else "ok",
        "mode": state.get("mode"),
        "source": relative_to_root(root, Path(state["source_path"])),
        "lifecycle_status": state.get("lifecycle_status"),
        "semantic_status": state.get("semantic_status"),
        "validation": state.get("validation", {}),
        "changed_files": state.get("changed_files", []),
        "report_path": state.get("report_path"),
        "meta_errors": state.get("meta_errors", []),
    }
    if state.get("source_page"):
        output["source_page"] = relative_to_root(root, Path(state["source_page"]))
    if state.get("mode") == "draft":
        output["draft"] = state.get("draft")
    return output


def run_ingest(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    raw_path = resolve_source(root, args.source)
    graph = build_graph()
    initial: WikiGrowthState = {
        "root": str(root),
        "source": args.source,
        "source_path": str(raw_path),
        "mode": args.mode,
        "config_path": args.config,
        "title": args.title,
        "max_source_chars": args.max_source_chars,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
    }
    final_state = graph.invoke(initial)
    output = state_output(final_state)
    json_dump(output)
    return 1 if output.get("status") == "error" else 0


def load_pipeline_check_module():
    path = SCRIPT_DIR / "pipeline_check.py"
    spec = importlib.util.spec_from_file_location("pipeline_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load scripts/pipeline_check.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["pipeline_check"] = module
    spec.loader.exec_module(module)
    return module


def run_check(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    module = load_pipeline_check_module()
    result = module.check_source(root, args.source)
    json_dump(result)
    return 1 if result.get("status") == "failed" else 0


def build_handoff_markdown(
    root: Path,
    raw_path: Path,
    source_page: Path | None,
    source_text: str,
) -> str:
    raw_rel = relative_to_root(root, raw_path)
    source_page_rel = relative_to_root(root, source_page) if source_page else ""
    context = llm_full_ingest.load_context(root)
    schema = {
        "summary": "string",
        "key_facts": ["string"],
        "important_claims": [
            {
                "claim_text": "string",
                "status": "proposed",
                "extractor_confidence": "low|medium|high",
                "evidence_excerpt": "string",
            }
        ],
        "uncertainties": ["string"],
        "open_questions": ["string"],
        "affected_pages": [
            {
                "page": "[[wiki-page]]",
                "action": "source_page_only|update_candidate|create_candidate",
                "reason": "string",
                "confidence": "low|medium|high",
            }
        ],
        "completion_notes": ["string"],
    }
    lines = [
        "---",
        f'title: "Handoff: {raw_path.name}"',
        "type: handoff",
        "status: pending",
        "lifecycle_status: handoff_created",
        "semantic_status: pending",
        f"created: {today()}",
        f"updated: {today()}",
        f'raw_path: "{raw_rel}"',
    ]
    if source_page_rel:
        lines.append(f'source_page: "{source_page_rel}"')
    lines.extend(
        [
            "tags:",
            "  - handoff",
            "  - llm-wiki",
            "  - pending",
            "---",
            "",
            f"# Handoff: {raw_path.name}",
            "",
            "This is an explicit non-ingest handoff artifact. It is not semantic success.",
            "",
            "## Instructions",
            "",
            "- Return JSON only.",
            "- Keep all claims proposed.",
            "- Do not create accepted/reviewed/final truth.",
            "- Do not use filename, keyword, graph, retrieval, or YAML shortcuts as semantic gates.",
            "- Cite only source-backed evidence.",
            "",
            "## Required Output Schema",
            "",
            "```json",
            json.dumps(schema, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Repo Contract Excerpt",
            "",
            "```markdown",
            context.get("agents", "")[:12000],
            "```",
            "",
            "## Wiki Index Excerpt",
            "",
            "```markdown",
            context.get("wiki_index", "")[:12000],
            "```",
            "",
            "## Source Text",
            "",
            "```markdown",
            source_text,
            "```",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_export_handoff(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    raw_path = resolve_source(root, args.source)
    source_text = llm_full_ingest.safe_read(raw_path, max_chars=args.max_source_chars)
    source_page = llm_full_ingest.find_source_page_by_raw_path(root, raw_path)
    handoff_dir = root / "wiki" / "_meta" / "handoff"
    handoff_path = handoff_dir / f"handoff-{timestamp()}-{llm_full_ingest.slugify(raw_path.stem)}.md"
    content = build_handoff_markdown(root, raw_path, source_page, source_text)
    # Handoff is an explicit non-ingest artifact. It is the only write here.
    write_text(handoff_path, content)
    json_dump(
        {
            "status": "ok",
            "command": "export-handoff",
            "lifecycle_status": "handoff_created",
            "semantic_status": "pending",
            "path": relative_to_root(root, handoff_path),
            "source": relative_to_root(root, raw_path),
            "source_page": relative_to_root(root, source_page) if source_page else None,
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Strict LangGraph runtime for DocTology wiki growth.")
    parser.add_argument("--root", default=".", help="DocTology repo root. Defaults to current directory.")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Run strict helper-LLM graph ingest.")
    ingest.add_argument("source", help="Source path under raw/**.")
    ingest.add_argument("--mode", choices=["draft", "apply-source-page"], required=True)
    ingest.add_argument("--config", help="Optional explicit wikiconfig.json path.")
    ingest.add_argument("--title", help="Optional title for source registration.")
    ingest.add_argument("--max-source-chars", type=int, default=60_000)
    ingest.add_argument("--max-tokens", type=int, default=3500)
    ingest.add_argument("--temperature", type=float, default=0.2)

    check = sub.add_parser("check", help="Run structural source route check.")
    check.add_argument("--source", required=True, help="Source path to inspect.")

    handoff = sub.add_parser("export-handoff", help="Export an explicit non-ingest LLM handoff artifact.")
    handoff.add_argument("source", help="Source path under raw/**.")
    handoff.add_argument("--max-source-chars", type=int, default=60_000)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "ingest":
            return run_ingest(args)
        if args.command == "check":
            return run_check(args)
        if args.command == "export-handoff":
            return run_export_handoff(args)
        parser.error(f"Unknown command: {args.command}")
        return 2
    except Exception as exc:
        json_dump({"status": "error", "error": str(exc)}, stderr=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
