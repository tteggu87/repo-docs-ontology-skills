from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.analysis_profiles.common import (
    citation_for,
    now_id,
    record_analysis_findings,
    record_analysis_run,
    slugify,
    units_for_profile,
    write_analysis_page,
)


def _finding_key(text: str) -> str:
    words = [word.lower() for word in text.split()[:10]]
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()[:12]


def write_consistency_memo(root: Path, title: str = "Report Consistency Draft") -> dict:
    units = units_for_profile(root, "report-consistency-analysis", "report_section")
    warnings: list[str] = []
    if not units:
        warnings.append("No report_section units found.")

    previous = []
    findings_path = root / "warehouse/jsonl/analysis_findings.jsonl"
    if findings_path.exists():
        previous = [line for line in findings_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    run_id = now_id("analysis-run", title)
    findings = []
    body_lines = []
    citations = []
    previous_blob = "\n".join(previous)
    for unit in units[:20]:
        text = str(unit.get("text") or "")
        key = _finding_key(text)
        status = "stable" if key in previous_blob else ("changed_with_new_evidence" if previous else "insufficient_history")
        citation = citation_for(root, unit)
        citations.append(citation)
        findings.append(
            {
                "finding_id": f"finding-{key}-{run_id[-10:]}",
                "finding_key": key,
                "analysis_run_id": run_id,
                "profile_id": "report-consistency-analysis",
                "unit_id": unit.get("unit_id"),
                "document_id": unit.get("document_id"),
                "consistency_status": status,
                "text": text[:500],
            }
        )
        body_lines.append(f"- **{status}** `{key}`: {text[:220]} — {citation}")

    stem = f"report-consistency-{slugify(title)}-{run_id[-10:]}"
    body = (
        "## Consistency Status Draft\n\n"
        + ("\n".join(body_lines) if body_lines else "- No report findings available.")
        + "\n\n## Interpretation\n\n"
        "- `stable`: 동일 finding_key가 기존 analysis_findings에 이미 존재합니다.\n"
        "- `changed_with_new_evidence`: 기존 finding_key와 직접 일치하지 않지만 비교 가능한 과거 finding이 있습니다.\n"
        "- `insufficient_history`: 비교할 과거 finding이 없습니다.\n"
        "- `unclear`: 이번 MVP의 deterministic draft에서는 semantic contradiction 판정까지 수행하지 않습니다.\n"
        "\n## Warnings\n\n"
        + "\n".join(f"- {warning}" for warning in warnings or ["None"])
    )
    path = write_analysis_page(root, stem, title, body, "report.consistency_memo", citations)
    record_analysis_findings(root, findings)
    record_analysis_run(
        root,
        {
            "analysis_run_id": run_id,
            "profile_id": "report-consistency-analysis",
            "analysis_type": "report.consistency_memo",
            "output_path": path.relative_to(root).as_posix(),
            "finding_ids": [row["finding_id"] for row in findings],
            "warnings": warnings,
        },
    )
    return {"status": "ok", "profile_id": "report-consistency-analysis", "output_path": path.relative_to(root).as_posix(), "warnings": warnings, "findings": len(findings)}
