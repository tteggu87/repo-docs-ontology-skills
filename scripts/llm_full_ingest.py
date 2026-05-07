#!/usr/bin/env python3
"""DocTology LLM-backed full ingest runner.

This is a separate configured-LLM workflow layered above `scripts/llm_wiki.py`.
`llm_wiki.py ingest` remains source-registration-only.

The public workflow is intentionally small:

* dry-run: ask the configured LLM for a source-backed growth draft without writes
* apply: close the controlled wiki growth loop

`apply` may create/append affected wiki pages and proposed JSONL records, but it
must never mutate raw sources, create accepted truth, delete content, rename
pages, merge pages, or auto-commit.
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


RESERVED_APPLY_MODES = {"apply_wiki", "apply_jsonl_proposals", "apply_all"}
APPLY_MODES = {"dry_run", "dry-run", "apply", "apply_source_page", *RESERVED_APPLY_MODES}
PUBLIC_APPLY_MODES = {"dry_run", "dry-run", "apply"}
SOURCE_STATUS_AFTER_SOURCE_PAGE_APPLY = "pending-wiki-projection"
SOURCE_STATUS_AFTER_FULL_APPLY = "growth-applied"
PROPOSED_JSONL_FILES = {
    "proposed_entities": "proposed_entities.jsonl",
    "proposed_claims": "proposed_claims.jsonl",
    "proposed_evidence": "proposed_evidence.jsonl",
    "proposed_relations": "proposed_relations.jsonl",
}
ALLOWED_AFFECTED_PAGE_PREFIXES = (
    "wiki/concepts/",
    "wiki/entities/",
    "wiki/people/",
    "wiki/projects/",
    "wiki/timelines/",
    "wiki/analyses/",
)
FORBIDDEN_ACTION_TOKENS = {
    "delete",
    "remove",
    "rename",
    "merge",
    "move",
    "replace",
    "overwrite",
    "supersede",
}


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
    user_prompt = f"""Create a full-ingest growth draft for this source.

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
  "affected_page_updates": [
    {{
      "path": "wiki/concepts/example.md",
      "title": "Example",
      "type": "concept | entity | person | project | timeline | analysis",
      "action": "create | append",
      "reason": "string",
      "summary_append": "source-backed synthesis text to append",
      "key_points": ["source-backed bullet", "..."],
      "evidence_timeline": [
        {{
          "date": "YYYY-MM-DD or unknown",
          "text": "source-backed event/fact",
          "evidence_excerpt": "string"
        }}
      ],
      "open_questions": ["string", "..."]
    }}
  ],
  "proposed_entities": [
    {{
      "name": "string",
      "type": "string",
      "status": "proposed",
      "review_state": "needs_review",
      "evidence_excerpt": "string"
    }}
  ],
  "proposed_claims": [
    {{
      "claim_text": "string",
      "status": "proposed",
      "review_state": "needs_review",
      "confidence": "low | medium | high",
      "evidence_excerpt": "string"
    }}
  ],
  "proposed_evidence": [
    {{
      "evidence_text": "string",
      "status": "proposed",
      "review_state": "needs_review",
      "evidence_excerpt": "string"
    }}
  ],
  "proposed_relations": [
    {{
      "from": "string",
      "to": "string",
      "relation_type": "string",
      "status": "proposed",
      "review_state": "needs_review",
      "evidence_excerpt": "string"
    }}
  ],
  "completion_notes": ["string", "..."]
}}

Rules:
- `important_claims[*].status` must always be "proposed".
- This runner never emits accepted claims.
- Proposed JSONL records must use `status: proposed` and `review_state: needs_review`.
- `affected_page_updates[*].path` must be an explicit path under wiki/concepts,
  wiki/entities, wiki/people, wiki/projects, wiki/timelines, or wiki/analyses.
- `affected_page_updates[*].action` may only be create or append.
- Do not request delete, remove, rename, merge, move, replace, overwrite, or
  supersede actions.
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


def add_changed(changed_files: list[str], path: str) -> None:
    if path not in changed_files:
        changed_files.append(path)


def normalize_mode(mode: str, apply_flag: bool = False) -> str:
    normalized = mode.replace("-", "_")
    if normalized not in APPLY_MODES:
        raise RuntimeError(
            f"unsupported mode `{mode}`. Public modes are dry_run/dry-run and apply."
        )
    if apply_flag:
        if normalized not in {"dry_run", "apply"}:
            raise RuntimeError("--apply cannot be combined with another apply mode")
        return "apply"
    return normalized


def normalize_status(value: Any, default: str = "proposed") -> str:
    text = str(value or "").strip().lower()
    return text or default


def has_accepted_status(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    status = normalize_status(item.get("status"))
    review_state = normalize_status(item.get("review_state"), default="needs_review")
    return status == "accepted" or review_state == "accepted"


def assert_no_accepted_records(draft: dict[str, Any]) -> None:
    for field in ["important_claims", *PROPOSED_JSONL_FILES.keys()]:
        for item in normalize_list(draft.get(field)):
            if has_accepted_status(item):
                raise RuntimeError(f"Refusing to apply: configured LLM attempted accepted truth in {field}")


def action_has_forbidden_token(value: Any) -> bool:
    action = str(value or "").strip().lower()
    tokens = set(re.split(r"[^a-z]+", action))
    return bool(tokens & FORBIDDEN_ACTION_TOKENS)


def validate_affected_update_action(item: dict[str, Any]) -> None:
    action = str(item.get("action") or "append").strip().lower()
    if action_has_forbidden_token(action):
        raise RuntimeError(f"Refusing to apply: forbidden affected-page action `{action}`")
    if action not in {"create", "append"}:
        raise RuntimeError(f"Refusing to apply: unsupported affected-page action `{action}`")


def resolve_affected_page_path(root: Path, raw_path_value: Any) -> Path:
    value = str(raw_path_value or "").strip()
    if value.startswith("[[") and value.endswith("]]"):
        raise RuntimeError("affected_page_updates must use explicit wiki/... paths, not wikilink-only page names")
    value = value.lstrip("/")
    candidate = (root / value).resolve()
    rel = relative_to_root(root, candidate)
    if rel.startswith("raw/") or rel == "raw":
        raise RuntimeError(f"Refusing to apply: affected page targets raw path `{rel}`")
    if any(part == ".." for part in Path(rel).parts):
        raise RuntimeError(f"Refusing to apply: unsafe affected page path `{rel}`")
    if not rel.endswith(".md"):
        raise RuntimeError(f"Refusing to apply: affected page path must end with .md: `{rel}`")
    if not any(rel.startswith(prefix) for prefix in ALLOWED_AFFECTED_PAGE_PREFIXES):
        raise RuntimeError(f"Refusing to apply: affected page path is outside allowed wiki folders: `{rel}`")
    return candidate


def infer_page_type_from_path(path: Path, item_type: Any = None) -> str:
    if item_type:
        return str(item_type).strip().lower()
    parts = path.as_posix().split("/")
    if "concepts" in parts:
        return "concept"
    if "entities" in parts:
        return "entity"
    if "people" in parts:
        return "person"
    if "projects" in parts:
        return "project"
    if "timelines" in parts:
        return "timeline"
    if "analyses" in parts:
        return "analysis"
    return "concept"


def title_from_page_path(path: Path, item: dict[str, Any]) -> str:
    title = str(item.get("title") or "").strip()
    return title or path.stem.replace("-", " ").strip().title() or "Untitled"


def append_under_heading(markdown: str, heading: str, body: str) -> str:
    body = body.strip()
    if not body:
        return markdown if markdown.endswith("\n") else markdown + "\n"
    pattern = re.compile(
        rf"(^##\s+{re.escape(heading)}\s*\n)([\s\S]*?)(?=^##\s+|\Z)",
        re.MULTILINE,
    )

    def replacement(match: re.Match[str]) -> str:
        existing = match.group(2).rstrip()
        separator = "\n\n" if existing else "\n"
        return match.group(1) + existing + separator + body + "\n\n"

    if pattern.search(markdown):
        return pattern.sub(replacement, markdown, count=1)
    return markdown.rstrip() + f"\n\n## {heading}\n\n{body}\n"


def render_source_backed_block(source_page: Path, item: dict[str, Any]) -> str:
    source_link = f"[[{source_page.stem}]]"
    reason = str(item.get("reason") or "").strip()
    summary = str(item.get("summary_append") or item.get("summary") or "").strip()
    key_points = normalize_list(item.get("key_points"))
    open_questions = normalize_list(item.get("open_questions"))
    lines = [f"### {today()} — {source_link}"]
    if reason:
        lines.append(f"- Reason: {reason}")
    if summary:
        lines.append(f"- Summary: {summary}")
    for point in key_points:
        lines.append(f"- {str(point).strip()}")
    if open_questions:
        lines.append("- Open questions:")
        lines.extend(f"  - {str(question).strip()}" for question in open_questions)
    return "\n".join(lines).rstrip()


def render_evidence_timeline_block(source_page: Path, item: dict[str, Any]) -> str:
    source_link = f"[[{source_page.stem}]]"
    entries = normalize_list(item.get("evidence_timeline"))
    lines: list[str] = []
    for entry in entries:
        if isinstance(entry, dict):
            when = str(entry.get("date") or "unknown").strip()
            text = str(entry.get("text") or entry.get("event") or "").strip()
            evidence = str(entry.get("evidence_excerpt") or "").strip()
            if not text and evidence:
                text = evidence
            if not text:
                continue
            line = f"- {when}: {text} Source: {source_link}"
            if evidence:
                line += f" Evidence: “{evidence[:500]}”"
            lines.append(line)
        else:
            text = str(entry).strip()
            if text:
                lines.append(f"- unknown: {text} Source: {source_link}")
    return "\n".join(lines).rstrip()


def create_affected_page_content(path: Path, item: dict[str, Any], source_page: Path) -> str:
    title = title_from_page_path(path, item)
    page_type = infer_page_type_from_path(path, item.get("type"))
    source_link = f"[[{source_page.stem}]]"
    update_block = render_source_backed_block(source_page, item)
    timeline_block = render_evidence_timeline_block(source_page, item)
    lines = [
        "---",
        f'title: "{title}"',
        f"type: {page_type}",
        "status: active",
        f"created: {today()}",
        f"updated: {today()}",
        "sources:",
        f'  - "{source_link}"',
        "---",
        "",
        f"# {title}",
        "",
        "## Source-backed Updates",
        "",
        update_block or f"### {today()} — {source_link}\n- Created from source-backed ingest.",
        "",
        "## Evidence Timeline",
        "",
        timeline_block or f"- {today()}: Source-backed page created. Source: {source_link}",
        "",
        "## Open Questions",
        "",
    ]
    open_questions = normalize_list(item.get("open_questions"))
    lines.extend([f"- {str(question).strip()}" for question in open_questions] or ["- None identified."])
    lines.extend(["", "## Related Sources", "", f"- {source_link}", ""])
    return "\n".join(lines).rstrip() + "\n"


def refresh_generic_frontmatter_updated(markdown: str) -> str:
    match = re.match(r"\A---\n(.*?)\n---\n?", markdown, flags=re.DOTALL)
    if not match:
        return markdown
    frontmatter = match.group(1)
    if re.search(r"^updated:\s*.*$", frontmatter, flags=re.MULTILINE):
        frontmatter = re.sub(
            r"^updated:\s*.*$",
            f"updated: {today()}",
            frontmatter,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        frontmatter = frontmatter.rstrip() + f"\nupdated: {today()}"
    return "---\n" + frontmatter.rstrip() + "\n---\n" + markdown[match.end():]


def update_existing_affected_page(markdown: str, source_page: Path, item: dict[str, Any]) -> str:
    updated = refresh_generic_frontmatter_updated(markdown)
    update_block = render_source_backed_block(source_page, item)
    timeline_block = render_evidence_timeline_block(source_page, item)
    if update_block:
        updated = append_under_heading(updated, "Source-backed Updates", update_block)
    if timeline_block:
        updated = append_under_heading(updated, "Evidence Timeline", timeline_block)
    related_source = f"- [[{source_page.stem}]]"
    if related_source not in updated:
        updated = append_under_heading(updated, "Related Sources", related_source)
    return updated if updated.endswith("\n") else updated + "\n"


def apply_affected_page_updates(
    root: Path,
    source_page: Path,
    draft: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    changed_files: list[str] = []
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for raw_item in normalize_list(draft.get("affected_page_updates")):
        if not isinstance(raw_item, dict):
            skipped.append({"item": str(raw_item), "reason": "affected page update is not an object"})
            continue
        try:
            validate_affected_update_action(raw_item)
            target = resolve_affected_page_path(root, raw_item.get("path"))
            rel = relative_to_root(root, target)
            action = str(raw_item.get("action") or "append").strip().lower()
            existed = target.exists()
            if action == "create" and existed:
                action = "append"
            if existed:
                old = read_text(target)
                new = update_existing_affected_page(old, source_page, raw_item)
            else:
                new = create_affected_page_content(target, raw_item, source_page)
            write_text(target, new)
            add_changed(changed_files, rel)
            applied.append({"path": rel, "action": "created" if not existed else "appended"})
        except Exception as exc:
            message = str(exc)
            if (
                "forbidden affected-page action" in message
                or "targets raw path" in message
                or "outside repo" in message
                or "Unsafe" in message
            ):
                raise
            skipped.append({"item": raw_item, "reason": message})
    return changed_files, applied, skipped


def validate_affected_page_updates_for_apply(root: Path, draft: dict[str, Any]) -> None:
    for index, raw_item in enumerate(normalize_list(draft.get("affected_page_updates")), start=1):
        if not isinstance(raw_item, dict):
            raise RuntimeError(f"Refusing to apply: affected_page_updates[{index}] is not an object")
        validate_affected_update_action(raw_item)
        resolve_affected_page_path(root, raw_item.get("path"))


def proposed_jsonl_record(
    root: Path,
    raw_path: Path,
    source_page: Path,
    field: str,
    item: Any,
) -> dict[str, Any]:
    if isinstance(item, dict):
        record = dict(item)
    else:
        value_key = {
            "proposed_entities": "name",
            "proposed_claims": "claim_text",
            "proposed_evidence": "evidence_text",
            "proposed_relations": "relation_text",
        }.get(field, "text")
        record = {value_key: str(item).strip()}
    if has_accepted_status(record):
        raise RuntimeError(f"Refusing to apply: configured LLM attempted accepted truth in {field}")
    record["status"] = "proposed"
    record["review_state"] = "needs_review"
    record.setdefault("created_at", today())
    record["raw_path"] = relative_to_root(root, raw_path)
    record["source_page"] = relative_to_root(root, source_page)
    record["source_wikilink"] = f"[[{source_page.stem}]]"
    record["ingest_runner"] = "scripts/llm_full_ingest.py"
    record["record_family"] = field
    return record


def append_proposed_jsonl_records(
    root: Path,
    raw_path: Path,
    source_page: Path,
    draft: dict[str, Any],
) -> tuple[list[str], dict[str, int]]:
    changed_files: list[str] = []
    counts: dict[str, int] = {}
    jsonl_dir = root / "warehouse" / "jsonl"
    for field, filename in PROPOSED_JSONL_FILES.items():
        items = normalize_list(draft.get(field))
        if not items:
            counts[field] = 0
            continue
        path = jsonl_dir / filename
        existing = read_text(path) if path.exists() else ""
        lines = []
        for item in items:
            record = proposed_jsonl_record(root, raw_path, source_page, field, item)
            lines.append(json.dumps(record, ensure_ascii=False, sort_keys=True))
        content = existing
        if content and not content.endswith("\n"):
            content += "\n"
        content += "\n".join(lines) + "\n"
        write_text(path, content)
        add_changed(changed_files, relative_to_root(root, path))
        counts[field] = len(lines)
    return changed_files, counts


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


def refresh_source_frontmatter(markdown: str, status: str = SOURCE_STATUS_AFTER_SOURCE_PAGE_APPLY) -> str:
    match = re.match(r"\A---\n(.*?)\n---\n?", markdown, flags=re.DOTALL)
    if not match:
        return markdown

    frontmatter = match.group(1)
    replacements = {
        "status": status,
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


def build_source_page_content(
    existing: str,
    draft: dict[str, Any],
    *,
    status: str = SOURCE_STATUS_AFTER_SOURCE_PAGE_APPLY,
) -> str:
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
    updated = refresh_source_frontmatter(updated, status=status)
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
    accepted_fields: list[str] = []
    for field in ["important_claims", *PROPOSED_JSONL_FILES.keys()]:
        if any(has_accepted_status(item) for item in normalize_list(draft.get(field))):
            accepted_fields.append(field)
    forbidden_actions = [
        str(item.get("action") or "").strip()
        for item in normalize_list(draft.get("affected_page_updates"))
        if isinstance(item, dict) and action_has_forbidden_token(item.get("action"))
    ]
    result: dict[str, Any] = {
        "draft_has_summary": bool(str(draft.get("summary") or "").strip()),
        "claims_are_proposed": all(
            not isinstance(item, dict) or normalize_status(item.get("status")) == "proposed"
            for item in claims
        ),
        "accepted_truth_fields": accepted_fields,
        "has_accepted_truth": bool(accepted_fields),
        "forbidden_affected_actions": forbidden_actions,
        "claim_count": len(claims),
        "key_fact_count": len(normalize_list(draft.get("key_facts"))),
        "affected_page_count": len(normalize_list(draft.get("affected_pages"))),
        "affected_page_update_count": len(normalize_list(draft.get("affected_page_updates"))),
        "proposed_jsonl_count": sum(
            len(normalize_list(draft.get(field))) for field in PROPOSED_JSONL_FILES
        ),
    }
    if source_page_new is not None:
        result["remaining_TBD_count"] = len(re.findall(r"\bTBD\b", source_page_new))
    return result


def assert_apply_safe(validation: dict[str, Any]) -> None:
    if not validation.get("draft_has_summary"):
        raise RuntimeError("Refusing to apply: draft has no summary")
    if not validation.get("claims_are_proposed"):
        raise RuntimeError("Refusing to apply: configured LLM attempted non-proposed claims")
    if validation.get("has_accepted_truth"):
        fields = ", ".join(validation.get("accepted_truth_fields") or [])
        raise RuntimeError(f"Refusing to apply: configured LLM attempted accepted truth in {fields}")
    if validation.get("forbidden_affected_actions"):
        actions = ", ".join(validation.get("forbidden_affected_actions") or [])
        raise RuntimeError(f"Refusing to apply: configured LLM attempted forbidden affected-page actions: {actions}")
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
    *,
    applied_pages: list[dict[str, Any]] | None = None,
    skipped_pages: list[dict[str, Any]] | None = None,
    jsonl_counts: dict[str, int] | None = None,
) -> Path:
    reports_dir = root / "wiki" / "_meta" / "ingest_reports"
    source_slug = slugify(source_page.stem if source_page else raw_path.stem)
    report_path = reports_dir / f"ingest-{today()}-{source_slug}.md"

    source_link = f"[[{source_page.stem}]]" if source_page else "(not registered)"
    claims = normalize_list(draft.get("important_claims"))
    uncertainties = normalize_list(draft.get("uncertainties"))
    open_questions = normalize_list(draft.get("open_questions"))
    affected_pages = normalize_list(draft.get("affected_pages"))
    applied_pages = applied_pages or []
    skipped_pages = skipped_pages or []
    jsonl_counts = jsonl_counts or {}
    report_status = "draft" if apply_mode == "dry_run" else "applied" if apply_mode == "apply" else "partial"

    lines = [
        "---",
        f'title: "Ingest Report: {raw_path.name}"',
        "type: ingest_report",
        f"status: {report_status}",
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
    ]
    if jsonl_counts:
        for field, count in jsonl_counts.items():
            filename = PROPOSED_JSONL_FILES.get(field, f"{field}.jsonl")
            lines.append(f"- `{filename}`: appended `{count}` proposed records")
    else:
        lines.append("- proposed JSONL: none emitted by configured LLM")
    lines.extend(
        [
            "- accepted truth: not automated / review-gated",
            "- raw source mutation: forbidden",
            "",
            "## Wiki Pages",
            "",
        ]
    )
    if changed_files:
        lines.extend([f"- `{item}`: changed" for item in changed_files])
    else:
        lines.append("- No files changed.")
    lines.extend(["", "## Applied Affected Pages", ""])
    if applied_pages:
        lines.extend([f"- `{item.get('path')}`: {item.get('action')}" for item in applied_pages])
    else:
        lines.append("- None applied.")
    lines.extend(["", "## Skipped Affected Pages", ""])
    if skipped_pages:
        for item in skipped_pages:
            lines.append(f"- `{item.get('reason')}`")
    else:
        lines.append("- None skipped.")
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
    lines.extend(
        [
            "",
            "## Review Instructions",
            "",
            "- Review the automatic growth with `git diff` before committing.",
            "- Clean or split any over-eager wiki additions manually.",
            "- Promote proposed JSONL records to accepted truth only after explicit review.",
            "- Do not treat this report as accepted semantic truth.",
        ]
    )
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
        default="dry_run",
        help="Apply mode. Public modes are dry_run/dry-run and apply. apply_source_page remains a legacy compatibility mode.",
    )
    parser.add_argument("--apply", action="store_true", help="Alias for --mode apply.")
    parser.add_argument("--max-source-chars", type=int, default=60_000)
    parser.add_argument("--max-tokens", type=int, default=3500)
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args(argv)

    try:
        mode = normalize_mode(args.mode, apply_flag=args.apply)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    if mode in RESERVED_APPLY_MODES:
        print(
            json.dumps(
                {
                    "error": f"{mode} is no longer a public mode. Use --apply for the full growth loop.",
                    "public_modes": sorted(PUBLIC_APPLY_MODES),
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

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

    try:
        config = load_helper_config(root, args.config)
        if not config.enabled or config.chat_model is None:
            raise RuntimeError("configured chat model is not enabled/configured")

        source_text = safe_read(raw_path, max_chars=args.max_source_chars)
        source_page = find_source_page_by_raw_path(root, raw_path)

        if mode in {"apply", "apply_source_page"} and source_page is None:
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
            source_status = (
                SOURCE_STATUS_AFTER_FULL_APPLY
                if mode == "apply"
                else SOURCE_STATUS_AFTER_SOURCE_PAGE_APPLY
            )
            source_page_new = build_source_page_content(source_page_old, draft, status=source_status)
            diff_text = unified_diff(
                source_page_old,
                source_page_new,
                fromfile=str(source_page.relative_to(root)),
                tofile=str(source_page.relative_to(root)) + " (draft)",
            )

        validation = validate_draft(draft, source_page_new)

        report_path: Path | None = None
        applied_pages: list[dict[str, Any]] = []
        skipped_pages: list[dict[str, Any]] = []
        jsonl_counts: dict[str, int] = {}

        if mode in {"apply", "apply_source_page"}:
            if not source_page or source_page_new is None:
                raise RuntimeError(f"{mode} requires a registered source page")
            assert_no_accepted_records(draft)
            assert_apply_safe(validation)
            if mode == "apply":
                validate_affected_page_updates_for_apply(root, draft)

            write_text(source_page, source_page_new)
            add_changed(changed_files, relative_to_root(root, source_page))

            if mode == "apply":
                affected_changed, applied_pages, skipped_pages = apply_affected_page_updates(root, source_page, draft)
                for item in affected_changed:
                    add_changed(changed_files, item)
                jsonl_changed, jsonl_counts = append_proposed_jsonl_records(root, raw_path, source_page, draft)
                for item in jsonl_changed:
                    add_changed(changed_files, item)

            report_path = write_ingest_report(
                root,
                raw_path,
                source_page,
                draft,
                mode,
                changed_files,
                diff_text,
                validation,
                applied_pages=applied_pages,
                skipped_pages=skipped_pages,
                jsonl_counts=jsonl_counts,
            )
            add_changed(changed_files, relative_to_root(root, report_path))

            # Refresh index after report creation so the report is indexed.
            reindex = run_llm_wiki(root, "reindex")
            if reindex.returncode == 0:
                add_changed(changed_files, "wiki/_meta/index.md")
            else:
                validation["reindex_error"] = (reindex.stderr or reindex.stdout).strip()[:500]

            if mode == "apply":
                log_messages = [
                    f"Full ingest apply | {raw_path.name}",
                    f"Updated source page `{relative_to_root(root, source_page)}`.",
                    f"Applied `{len(applied_pages)}` affected wiki page updates.",
                    f"Appended proposed JSONL records: `{sum(jsonl_counts.values())}`.",
                    f"Wrote ingest report `{relative_to_root(root, report_path)}`.",
                    "Review automatic growth with `git diff` before committing.",
                ]
            else:
                log_messages = [
                    f"Full ingest source-page draft | {raw_path.name}",
                    f"Updated `{relative_to_root(root, source_page)}` from configured LLM draft.",
                    f"Wrote ingest report `{relative_to_root(root, report_path)}`.",
                    "JSONL registries remain pending/not implemented in source-page compatibility mode.",
                ]
            log = run_llm_wiki(root, "log", "ingest", *log_messages)
            if log.returncode == 0:
                add_changed(changed_files, "wiki/_meta/log.md")
            else:
                validation["log_error"] = (log.stderr or log.stdout).strip()[:500]

        output = {
            "root": str(root),
            "source": relative_to_root(root, raw_path),
            "mode": mode,
            "configured_model": {
                "config_source": config.source_path,
                "provider": config.chat_model.provider if config.chat_model else None,
                "model": config.chat_model.model if config.chat_model else None,
            },
            "source_page": relative_to_root(root, source_page) if source_page else None,
            "draft": draft,
            "validation": validation,
            "applied_pages": applied_pages,
            "skipped_pages": skipped_pages,
            "jsonl_counts": jsonl_counts,
            "changed_files": changed_files,
            "report_path": relative_to_root(root, report_path) if report_path else None,
            "source_page_diff": diff_text if mode == "dry_run" else "(written to ingest report)" if diff_text else "",
            "warnings": list(config.warnings),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
