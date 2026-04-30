from __future__ import annotations

from pathlib import Path

from scripts.analysis_profiles.common import (
    citation_for,
    now_id,
    record_analysis_run,
    score_units,
    slugify,
    units_for_profile,
    write_analysis_page,
)
from scripts.wiki_projection import rebuild_index, slugify as wiki_slugify, today, write_text


def write_concept_pages(root: Path, units: list[dict], limit: int = 10) -> list[str]:
    created_or_updated: list[str] = []
    seen: set[str] = set()
    for unit in units:
        heading = str(unit.get("heading") or "").strip()
        if not heading or heading.casefold() in seen:
            continue
        seen.add(heading.casefold())
        path = root / "wiki" / "concepts" / f"{wiki_slugify(heading)}.md"
        citation = citation_for(root, unit)
        title = heading.replace('"', '\\"')
        body = (
            "---\n"
            f'title: "{title}"\n'
            "type: concept\n"
            "status: draft\n"
            f"created: {today()}\n"
            f"updated: {today()}\n"
            "tags:\n"
            "  - education-analysis\n"
            "---\n\n"
            f"# {heading}\n\n"
            "## Draft Definition\n\n"
            f"- {str(unit.get('text') or '')[:400]}\n\n"
            "## Source Citation\n\n"
            f"- {citation}\n"
        )
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if citation not in existing:
                write_text(path, existing.rstrip() + "\n\n## Additional Source Citation\n\n" + f"- {citation}\n")
        else:
            write_text(path, body)
        created_or_updated.append(path.relative_to(root).as_posix())
        if len(created_or_updated) >= limit:
            break
    if created_or_updated:
        rebuild_index(root)
    return created_or_updated


def write_education_summary(root: Path, question: str = "핵심 개념 요약", top_k: int = 5) -> dict:
    units = units_for_profile(root, "education-analysis", "education_section")
    scored = score_units(units, question)
    selected = [unit for _score, unit in scored[:top_k]]
    warnings: list[str] = []
    if not selected:
        selected = units[:top_k]
        warnings.append("No keyword match found; used first available education units.")
    if not selected:
        warnings.append("No education content units found.")

    citations = [citation_for(root, unit) for unit in selected]
    summary_lines = [f"- {unit.get('heading') or 'Untitled section'}: {str(unit.get('text') or '')[:220]}" for unit in selected]
    evidence_lines = [f"- {citation}" for citation in citations]
    warning_lines = [f"- {warning}" for warning in warnings] or ["- None"]

    title = f"Education Q&A Draft - {question}"
    run_id = now_id("analysis-run", title)
    stem = f"analysis-{slugify(question) or 'education-qa'}-{run_id[-10:]}"
    body = (
        "## 답변 요약\n\n"
        + ("\n".join(summary_lines) if summary_lines else "- 답변할 근거 unit이 없습니다.")
        + "\n\n## 핵심 설명\n\n"
        "초기 MVP는 LLM 생성 대신 keyword/heading/text match로 관련 unit을 찾아 citation-first 답변 초안을 만듭니다.\n\n"
        "## 반드시 알아야 할 내용\n\n"
        + ("\n".join(summary_lines[:3]) if summary_lines else "- 추가 ingest가 필요합니다.")
        + "\n\n## 근거 자료\n\n"
        + ("\n".join(evidence_lines) if evidence_lines else "- No citation available.")
        + "\n\n## 주의할 점\n\n"
        + "\n".join(warning_lines)
    )
    path = write_analysis_page(root, stem, title, body, "education.cited_qa", citations)
    concept_paths = write_concept_pages(root, selected)
    record_analysis_run(
        root,
        {
            "analysis_run_id": run_id,
            "profile_id": "education-analysis",
            "analysis_type": "education.cited_qa",
            "question": question,
            "output_path": path.relative_to(root).as_posix(),
            "concept_paths": concept_paths,
            "unit_ids": [unit.get("unit_id") for unit in selected],
            "warnings": warnings,
        },
    )
    return {"status": "ok", "profile_id": "education-analysis", "output_path": path.relative_to(root).as_posix(), "concept_paths": concept_paths, "warnings": warnings, "citations": citations}
