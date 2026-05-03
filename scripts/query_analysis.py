#!/usr/bin/env python3
"""Persist durable query answers as wiki analyses without mutating active semantic pages."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def today() -> str:
    return dt.date.today().isoformat()


def slugify(value: str, *, max_len: int = 72) -> str:
    slug = re.sub(r"[^A-Za-z0-9가-힣]+", "-", value.strip().lower()).strip("-")
    return (slug[:max_len].strip("-") or "query-answer")


def _safe_rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _unique_analysis_path(root: Path, question: str) -> Path:
    date = today()
    base = f"analysis-{date}-{slugify(question)}"
    path = root / "wiki" / "analyses" / f"{base}.md"
    if not path.exists():
        return path
    index = 2
    while True:
        candidate = root / "wiki" / "analyses" / f"{base}-{index}.md"
        if not candidate.exists():
            return candidate
        index += 1


def _frontmatter_list(name: str, values: list[str]) -> list[str]:
    if not values:
        return [f"{name}: []"]
    lines = [f"{name}:"]
    for value in values:
        escaped = str(value).replace('"', '\\"')
        lines.append(f'  - "{escaped}"')
    return lines


def _format_evidence_mix(evidence_mix: dict[str, Any] | None) -> str:
    if not evidence_mix:
        return "- not recorded"
    lines: list[str] = []
    for key, value in evidence_mix.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def _format_list(values: list[str]) -> str:
    if not values:
        return "- none recorded"
    return "\n".join(f"- {value}" for value in values)


def build_analysis_markdown(
    *,
    title: str,
    question: str,
    answer_markdown: str,
    sources: list[str] | None = None,
    evidence_mix: dict[str, Any] | None = None,
    proposed_updates: list[str] | None = None,
    uncertainty: list[str] | None = None,
    status: str = "active",
    analysis_method: str = "chat_agent_llm",
    trust_level: str = "evidence_grounded",
) -> str:
    date = today()
    sources = sources or []
    proposed_updates = proposed_updates or []
    uncertainty = uncertainty or []
    frontmatter = [
        "---",
        f'title: "{title.replace(chr(34), chr(39))}"',
        "type: analysis",
        f"status: {status}",
        f"analysis_method: {analysis_method}",
        f"trust_level: {trust_level}",
        f"created: {date}",
        f"updated: {date}",
        "tags:",
        "  - llm-wiki",
        "  - query-answer",
        *_frontmatter_list("sources", sources),
        "---",
        "",
    ]
    body = [
        f"# {title}",
        "",
        "## Question",
        "",
        question,
        "",
        "## Answer",
        "",
        answer_markdown.strip() or "_No answer body recorded._",
        "",
        "## Evidence Mix",
        "",
        _format_evidence_mix(evidence_mix),
        "",
        "## Sources",
        "",
        _format_list(sources),
        "",
        "## Uncertainty",
        "",
        _format_list(uncertainty),
        "",
        "## Proposed Wiki Updates",
        "",
        "_These are candidates only. Do not treat them as active wiki truth until reviewed._",
        "",
        _format_list(proposed_updates),
        "",
    ]
    return "\n".join(frontmatter + body)


def _upsert_index(root: Path, analysis_path: Path, summary: str) -> None:
    index_path = root / "wiki" / "_meta" / "index.md"
    if not index_path.exists():
        return
    text = index_path.read_text(encoding="utf-8")
    stem = analysis_path.stem
    if f"[[{stem}]]" in text:
        return
    line = f"- [[{stem}]] - {summary.strip() or 'Saved durable query answer.'}"
    text = re.sub(r"updated: \d{4}-\d{2}-\d{2}", f"updated: {today()}", text, count=1)
    marker = "## Analyses\n\n"
    if marker in text:
        text = text.replace(marker, marker + line + "\n", 1)
    else:
        text += f"\n\n## Analyses\n\n{line}\n"
    index_path.write_text(text, encoding="utf-8")


def _append_log(root: Path, analysis_path: Path, question: str, summary: str) -> None:
    log_path = root / "wiki" / "_meta" / "log.md"
    if not log_path.exists():
        return
    stem = analysis_path.stem
    entry = "\n".join(
        [
            "",
            f"## [{today()}] query | {summary.strip() or stem}",
            "",
            f"- Saved [[{stem}]] in wiki/analyses/.",
            f"- Question: {question}",
            "- Active semantic page updates, if any, remain proposed updates pending review.",
            "",
        ]
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def save_query_analysis(
    root: Path,
    *,
    question: str,
    answer_markdown: str,
    title: str | None = None,
    summary: str | None = None,
    sources: list[str] | None = None,
    evidence_mix: dict[str, Any] | None = None,
    proposed_updates: list[str] | None = None,
    uncertainty: list[str] | None = None,
    status: str = "active",
    analysis_method: str = "chat_agent_llm",
    trust_level: str = "evidence_grounded",
) -> str:
    title = title or f"Query answer - {question[:80]}"
    summary = summary or (answer_markdown.strip().splitlines()[0][:160] if answer_markdown.strip() else "Saved durable query answer.")
    path = _unique_analysis_path(root, question)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        build_analysis_markdown(
            title=title,
            question=question,
            answer_markdown=answer_markdown,
            sources=sources,
            evidence_mix=evidence_mix,
            proposed_updates=proposed_updates,
            uncertainty=uncertainty,
            status=status,
            analysis_method=analysis_method,
            trust_level=trust_level,
        ),
        encoding="utf-8",
    )
    _upsert_index(root, path, summary)
    _append_log(root, path, question, summary)
    return _safe_rel(root, path)


def _parse_evidence_mix(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
        for item in raw.split(","):
            if not item.strip() or "=" not in item:
                continue
            key, value = item.split("=", 1)
            data[key.strip()] = value.strip()
    if not isinstance(data, dict):
        raise ValueError("--evidence-mix must be a JSON object or key=value list")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Save a durable query answer under wiki/analyses and update index/log.")
    parser.add_argument("--question", required=True)
    parser.add_argument("--answer-file", default="-", help="Markdown answer file. Use '-' for stdin.")
    parser.add_argument("--title")
    parser.add_argument("--summary")
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--evidence-mix", help='JSON object or comma list, e.g. raw=60,wiki=25,ontology=15')
    parser.add_argument("--proposed-update", action="append", default=[])
    parser.add_argument("--uncertainty", action="append", default=[])
    parser.add_argument("--status", default="active")
    parser.add_argument("--analysis-method", default="chat_agent_llm")
    parser.add_argument("--trust-level", default="evidence_grounded")
    args = parser.parse_args()

    answer_markdown = sys.stdin.read() if args.answer_file == "-" else Path(args.answer_file).read_text(encoding="utf-8")
    path = save_query_analysis(
        ROOT,
        question=args.question,
        answer_markdown=answer_markdown,
        title=args.title,
        summary=args.summary,
        sources=args.source,
        evidence_mix=_parse_evidence_mix(args.evidence_mix),
        proposed_updates=args.proposed_update,
        uncertainty=args.uncertainty,
        status=args.status,
        analysis_method=args.analysis_method,
        trust_level=args.trust_level,
    )
    print(json.dumps({"status": "ok", "analysis_path": path}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
