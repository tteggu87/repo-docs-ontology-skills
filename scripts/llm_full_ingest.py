#!/usr/bin/env python3
"""DocTology LLM-backed source-page ingest runner.

This is a separate configured-LLM workflow layered above `scripts/llm_wiki.py`.
`llm_wiki.py ingest` remains source-registration-only.

The initial runner fills registered source pages and writes an ingest report. It
deliberately avoids broad wiki rewrites, JSONL writes, and accepted claim
promotion. Affected pages and claims remain draft/proposed only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from helper_llm import chat_completion, find_repo_root, load_helper_config
except ModuleNotFoundError:  # pragma: no cover - supports direct execution layouts
    helper_path = Path(__file__).resolve().parent / "helper_llm.py"
    spec = importlib.util.spec_from_file_location("helper_llm", helper_path)
    if spec is None or spec.loader is None:
        raise
    helper_llm = importlib.util.module_from_spec(spec)
    sys.modules["helper_llm"] = helper_llm
    spec.loader.exec_module(helper_llm)
    chat_completion = helper_llm.chat_completion
    find_repo_root = helper_llm.find_repo_root
    load_helper_config = helper_llm.load_helper_config


APPLY_MODES = {
    "dry_run",
    "apply_source_page",
    # Reserved for later explicit expansion:
    "apply_wiki",
    "apply_jsonl_proposals",
    "apply_all",
}
SOURCE_STATUS_AFTER_APPLY = "pending-wiki-projection"


def today() -> str:
    return dt.date.today().isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^0-9a-z가-힣ㄱ-ㅎㅏ-ㅣ]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "untitled"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def relative_to_root(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def safe_read(path: Path, max_chars: int = 60_000) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[TRUNCATED_FOR_CONFIGURED_LLM]\n"
    return text


def run_llm_wiki(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(root / "scripts" / "llm_wiki.py"), *args]
    return subprocess.run(cmd, cwd=root, text=True, capture_output=True, check=False)


def ensure_registered(root: Path, raw_path: Path, title: str | None) -> None:
    args = ["ingest", relative_to_root(root, raw_path)]
    if title:
        args.extend(["--title", title])
    result = run_llm_wiki(root, *args)
    if result.returncode != 0:
        raise RuntimeError(
            "source registration failed:\n"
            f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )


def find_source_page_by_raw_path(root: Path, raw_path: Path) -> Path | None:
    sources_dir = root / "wiki" / "sources"
    if not sources_dir.exists():
        return None
    relative = relative_to_root(root, raw_path)
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


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = strip_code_fence(text)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            raise
        payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("configured LLM response JSON must be an object")
    return payload


def normalize_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def load_context(root: Path) -> dict[str, str]:
    context: dict[str, str] = {}
    for key, relative in [
        ("agents", "AGENTS.md"),
        ("wiki_index", "wiki/_meta/index.md"),
        ("wiki_log", "wiki/_meta/log.md"),
        ("pipeline_manifest", "intelligence/manifests/pipelines.yaml"),
    ]:
        path = root / relative
        context[key] = read_text(path) if path.exists() else ""
    return context


def build_prompt(
    root: Path,
    raw_path: Path,
    source_page: Path | None,
    source_text: str,
    context: dict[str, str],
) -> tuple[str, str]:
    source_page_text = read_text(source_page) if source_page and source_page.exists() else "(not registered yet)"
    system_prompt = """You are a backend-only configured LLM for DocTology.

Return JSON only. Do not return markdown fences.

You draft source-backed wiki synthesis. You do not decide accepted truth.
All claims you extract are proposed. Do not invent citations, pages, or source
coverage.

Do not use filename, keyword, directory, token-shape, graph, retrieval, or YAML
shortcuts as hard semantic routing. Use the source content, existing wiki map,
and repo contract.

Weak, passing, or uncertain signals may stay on the source page.
"""
    user_prompt = f"""Create a full-ingest source-page draft for this source.

Repo root: {root}
Raw path: {relative_to_root(root, raw_path)}

Required JSON schema:
{{
  "summary": "string",
  "key_facts": ["string", "..."],
  "important_claims": [
    {{
      "claim_text": "string",
      "status": "proposed",
      "extractor_confidence": "low | medium | high",
      "evidence_excerpt": "string"
    }}
  ],
  "uncertainties": ["string", "..."],
  "open_questions": ["string", "..."],
  "affected_pages": [
    {{
      "page": "wiki/concepts/example.md or [[page-stem]]",
      "action": "update_candidate | create_candidate | source_page_only",
      "reason": "string",
      "confidence": "low | medium | high"
    }}
  ],
  "completion_notes": ["string", "..."]
}}

Rules:
- `important_claims[*].status` must always be "proposed".
- This runner never emits accepted claims.
- Do not create dedicated pages for passing mentions.
- Prefer source-page-only preservation for weak signals.
- If source is too thin, say so in uncertainties/open_questions.
- Affected pages are candidates unless you have read enough existing page context.

AGENTS excerpt:
{context.get("agents", "")[:12000]}

Wiki index:
{context.get("wiki_index", "")[:12000]}

Existing source page:
{source_page_text[:16000]}

Raw source:
{source_text}
"""
    return system_prompt, user_prompt


def render_claim(claim: Any) -> str:
    if isinstance(claim, dict):
        text = str(claim.get("claim_text") or "").strip()
        status = str(claim.get("status") or "proposed").strip()
        confidence = claim.get("extractor_confidence", claim.get("confidence"))
        evidence = str(claim.get("evidence_excerpt") or "").strip()
        parts = [f"- ({status}) {text}" if text else f"- ({status}) Claim text missing"]
        if confidence not in (None, ""):
            parts.append(f"  - Extractor confidence: `{confidence}`")
        if evidence:
            parts.append(f"  - Evidence excerpt: “{evidence[:500]}”")
        return "\n".join(parts)
    return f"- (proposed) {str(claim).strip()}"


def render_affected_page(item: Any) -> str:
    if isinstance(item, dict):
        page = str(item.get("page") or "unknown-page").strip()
        action = str(item.get("action") or "candidate").strip()
        reason = str(item.get("reason") or "").strip()
        confidence = str(item.get("confidence") or "").strip()
        suffix = f" — {reason}" if reason else ""
        conf = f" `{confidence}`" if confidence else ""
        return f"- {page} — {action}{conf}{suffix}"
    return f"- {str(item).strip()}"


def replace_section(markdown: str, heading: str, body: str) -> str:
    pattern = re.compile(
        rf"(^##\s+{re.escape(heading)}\s*\n)([\s\S]*?)(?=^##\s+|\Z)",
        re.MULTILINE,
    )

    def replacement(match: re.Match[str]) -> str:
        return match.group(1) + "\n" + body.rstrip() + "\n\n"

    if pattern.search(markdown):
        return pattern.sub(replacement, markdown, count=1)
    return markdown.rstrip() + f"\n\n## {heading}\n\n{body.rstrip()}\n"


def refresh_source_frontmatter(markdown: str) -> str:
    match = re.match(r"\A---\n(.*?)\n---\n?", markdown, flags=re.DOTALL)
    if not match:
        return markdown

    frontmatter = match.group(1)
    replacements = {
        "status": SOURCE_STATUS_AFTER_APPLY,
        "updated": today(),
    }
    for key, value in replacements.items():
        if re.search(rf"^{re.escape(key)}:\s*.*$", frontmatter, flags=re.MULTILINE):
            frontmatter = re.sub(
                rf"^{re.escape(key)}:\s*.*$",
                f"{key}: {value}",
                frontmatter,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            frontmatter = frontmatter.rstrip() + f"\n{key}: {value}"

    return "---\n" + frontmatter.rstrip() + "\n---\n" + markdown[match.end():]


def build_source_page_content(existing: str, draft: dict[str, Any]) -> str:
    summary = str(draft.get("summary") or "No summary generated.").strip()
    key_facts = normalize_list(draft.get("key_facts"))
    important_claims = normalize_list(draft.get("important_claims"))
    uncertainties = normalize_list(draft.get("uncertainties"))
    open_questions = normalize_list(draft.get("open_questions"))
    affected_pages = normalize_list(draft.get("affected_pages"))

    replacements = {
        "Summary": summary,
        "Key Facts": "\n".join(f"- {str(item).strip()}" for item in key_facts) or "- None identified.",
        "Important Claims": "\n".join(render_claim(item) for item in important_claims) or "- None identified.",
        "Contradictions Or Uncertainty": "\n".join(f"- {str(item).strip()}" for item in uncertainties) or "- None identified.",
        "Open Questions": "\n".join(f"- {str(item).strip()}" for item in open_questions) or "- None identified.",
        "Affected Pages": "\n".join(render_affected_page(item) for item in affected_pages) or "- None identified.",
    }

    updated = existing
    for heading, body in replacements.items():
        updated = replace_section(updated, heading, body.strip() + "\n")
    updated = refresh_source_frontmatter(updated)
    return updated if updated.endswith("\n") else updated + "\n"


def unified_diff(old: str, new: str, fromfile: str, tofile: str) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=fromfile,
            tofile=tofile,
        )
    )


def validate_draft(draft: dict[str, Any], source_page_new: str | None = None) -> dict[str, Any]:
    claims = normalize_list(draft.get("important_claims"))
    result: dict[str, Any] = {
        "draft_has_summary": bool(str(draft.get("summary") or "").strip()),
        "claims_are_proposed": all(
            not isinstance(item, dict) or str(item.get("status") or "proposed") == "proposed"
            for item in claims
        ),
        "claim_count": len(claims),
        "key_fact_count": len(normalize_list(draft.get("key_facts"))),
        "affected_page_count": len(normalize_list(draft.get("affected_pages"))),
    }
    if source_page_new is not None:
        result["remaining_TBD_count"] = len(re.findall(r"\bTBD\b", source_page_new))
    return result


def assert_apply_safe(validation: dict[str, Any]) -> None:
    if not validation.get("draft_has_summary"):
        raise RuntimeError("Refusing to apply: draft has no summary")
    if not validation.get("claims_are_proposed"):
        raise RuntimeError("Refusing to apply: configured LLM attempted non-proposed claims")
    if int(validation.get("remaining_TBD_count", 0) or 0) > 0:
        raise RuntimeError("Refusing to apply: generated source page still contains TBD markers")


def write_ingest_report(
    root: Path,
    raw_path: Path,
    source_page: Path | None,
    draft: dict[str, Any],
    apply_mode: str,
    changed_files: list[str],
    diff_text: str,
    validation: dict[str, Any],
) -> Path:
    reports_dir = root / "wiki" / "_meta" / "ingest_reports"
    source_slug = slugify(source_page.stem if source_page else raw_path.stem)
    report_path = reports_dir / f"ingest-{today()}-{source_slug}.md"

    source_link = f"[[{source_page.stem}]]" if source_page else "(not registered)"
    claims = normalize_list(draft.get("important_claims"))
    uncertainties = normalize_list(draft.get("uncertainties"))
    open_questions = normalize_list(draft.get("open_questions"))
    affected_pages = normalize_list(draft.get("affected_pages"))

    lines = [
        "---",
        f'title: "Ingest Report: {raw_path.name}"',
        "type: ingest_report",
        "status: partial" if apply_mode != "dry_run" else "draft",
        f"created: {today()}",
        f"updated: {today()}",
        f'source: "{source_link}"',
        "---",
        "",
        f"# Ingest Report: {raw_path.name}",
        "",
        "## Source Registered",
        "",
        f"- Raw path: `{relative_to_root(root, raw_path)}`",
        f"- Source page: {source_link}",
        f"- Apply mode: `{apply_mode}`",
        "",
        "## JSONL Registries",
        "",
        "- documents: pending / not implemented in this runner version",
        "- claims: proposed draft only",
        "- claim_evidence: proposed draft only",
        "- segments: pending / not implemented in this runner version",
        "- derived_edges: not applicable",
        "",
        "## Wiki Pages",
        "",
    ]
    if changed_files:
        lines.extend([f"- `{item}`: changed" for item in changed_files])
    else:
        lines.append("- No files changed.")
    lines.extend(["", "## Proposed Claims", ""])
    lines.extend([render_claim(item) for item in claims] or ["- None identified."])
    lines.extend(["", "## Affected Pages", ""])
    lines.extend([render_affected_page(item) for item in affected_pages] or ["- None identified."])
    lines.extend(["", "## Validation", ""])
    lines.extend([f"- {key}: `{value}`" for key, value in validation.items()])
    lines.extend(["", "## Uncertainties", ""])
    lines.extend([f"- {str(item).strip()}" for item in uncertainties] or ["- None identified."])
    lines.extend(["", "## Open Questions", ""])
    lines.extend([f"- {str(item).strip()}" for item in open_questions] or ["- None identified."])
    if diff_text:
        lines.extend(["", "## Source Page Diff", "", "```diff", diff_text.rstrip(), "```", ""])
    write_text(report_path, "\n".join(lines).rstrip() + "\n")
    return report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LLM-backed source-page ingest runner for DocTology.")
    parser.add_argument("source", help="Raw source path, absolute or relative to repo root.")
    parser.add_argument("--root", default=".", help="DocTology repo root. Defaults to current directory.")
    parser.add_argument("--config", help="Optional explicit wikiconfig.json path.")
    parser.add_argument("--title", help="Optional source title for registration.")
    parser.add_argument(
        "--mode",
        choices=sorted(APPLY_MODES),
        default="dry_run",
        help="Apply mode. Defaults to dry_run.",
    )
    parser.add_argument("--max-source-chars", type=int, default=60_000)
    parser.add_argument("--max-tokens", type=int, default=3500)
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args(argv)

    root = find_repo_root(Path(args.root))
    raw_path = Path(args.source)
    if not raw_path.is_absolute():
        raw_path = (root / raw_path).resolve()
    else:
        raw_path = raw_path.resolve()
    if not raw_path.exists():
        print(json.dumps({"error": f"source not found: {raw_path}"}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    if root.resolve() not in raw_path.parents and raw_path.resolve() != root.resolve():
        print(json.dumps({"error": "source must live inside the repo root"}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    if args.mode in {"apply_wiki", "apply_jsonl_proposals", "apply_all"}:
        print(
            json.dumps(
                {
                    "error": f"{args.mode} is reserved for a later implementation. Use dry_run or apply_source_page.",
                    "reason": "This runner version avoids broad wiki/JSONL writes by default.",
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    try:
        config = load_helper_config(root, args.config)
        if not config.enabled or config.chat_model is None:
            raise RuntimeError("configured chat model is not enabled/configured")

        source_text = safe_read(raw_path, max_chars=args.max_source_chars)
        source_page = find_source_page_by_raw_path(root, raw_path)

        if args.mode == "apply_source_page" and source_page is None:
            ensure_registered(root, raw_path, args.title)
            source_page = find_source_page_by_raw_path(root, raw_path)
            if source_page is None:
                raise RuntimeError("source registration completed but matching source page could not be found")

        context = load_context(root)
        system_prompt, user_prompt = build_prompt(root, raw_path, source_page, source_text, context)
        response = chat_completion(
            config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        draft = parse_json_response(response)

        source_page_old = read_text(source_page) if source_page and source_page.exists() else ""
        source_page_new: str | None = None
        diff_text = ""
        changed_files: list[str] = []

        if source_page:
            source_page_new = build_source_page_content(source_page_old, draft)
            diff_text = unified_diff(
                source_page_old,
                source_page_new,
                fromfile=str(source_page.relative_to(root)),
                tofile=str(source_page.relative_to(root)) + " (draft)",
            )

        validation = validate_draft(draft, source_page_new)

        report_path: Path | None = None
        if args.mode == "apply_source_page":
            if not source_page or source_page_new is None:
                raise RuntimeError("apply_source_page requires a registered source page")
            assert_apply_safe(validation)

            write_text(source_page, source_page_new)
            changed_files.append(relative_to_root(root, source_page))

            report_path = write_ingest_report(
                root,
                raw_path,
                source_page,
                draft,
                args.mode,
                changed_files,
                diff_text,
                validation,
            )
            changed_files.append(relative_to_root(root, report_path))

            # Refresh index after report creation so the report is indexed.
            reindex = run_llm_wiki(root, "reindex")
            if reindex.returncode == 0:
                changed_files.append("wiki/_meta/index.md")
            else:
                validation["reindex_error"] = (reindex.stderr or reindex.stdout).strip()[:500]

            log = run_llm_wiki(
                root,
                "log",
                "ingest",
                f"Full ingest source-page draft | {raw_path.name}",
                f"Updated `{relative_to_root(root, source_page)}` from configured LLM draft.",
                f"Wrote ingest report `{relative_to_root(root, report_path)}`.",
                "JSONL registries remain pending/not implemented in this runner version.",
            )
            if log.returncode == 0:
                changed_files.append("wiki/_meta/log.md")
            else:
                validation["log_error"] = (log.stderr or log.stdout).strip()[:500]

        output = {
            "root": str(root),
            "source": relative_to_root(root, raw_path),
            "mode": args.mode,
            "configured_model": {
                "config_source": config.source_path,
                "provider": config.chat_model.provider if config.chat_model else None,
                "model": config.chat_model.model if config.chat_model else None,
            },
            "source_page": relative_to_root(root, source_page) if source_page else None,
            "draft": draft,
            "validation": validation,
            "changed_files": changed_files,
            "report_path": relative_to_root(root, report_path) if report_path else None,
            "source_page_diff": diff_text if args.mode == "dry_run" else "(written to ingest report)" if diff_text else "",
            "warnings": list(config.warnings),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
