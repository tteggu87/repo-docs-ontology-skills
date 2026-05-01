from __future__ import annotations

from pathlib import Path

from scripts.analysis_profiles.common import (
    citation_for,
    common_terms,
    group_by,
    now_id,
    record_analysis_run,
    units_for_profile,
    write_analysis_page,
)


def write_weekly_digest(root: Path, title: str = "Email Weekly Digest") -> dict:
    units = units_for_profile(root, "email-analysis", "email_message")
    warnings: list[str] = []
    if not units:
        warnings.append("No email_message units found.")

    topic_lines = [f"- {term}: {count}" for term, count in common_terms(units, 10)] or ["- No topic candidates."]
    sender_lines = [f"- {sender}: {len(rows)} messages" for sender, rows in sorted(group_by(units, "author_name").items(), key=lambda item: -len(item[1]))[:10]]
    thread_lines = [f"- {thread}: {len(rows)} messages" for thread, rows in sorted(group_by(units, "thread_id").items(), key=lambda item: -len(item[1]))[:10]]
    action_lines = []
    open_question_lines = []
    for unit in units:
        text = str(unit.get("text") or "")
        low = text.lower()
        if any(marker in low for marker in ("todo", "action", "해야", "필요", "please", "next")):
            action_lines.append(f"- {text[:180]} — {citation_for(root, unit)}")
        if "?" in text or any(marker in low for marker in ("question", "궁금", "어떻게", "왜 ")):
            open_question_lines.append(f"- {text[:180]} — {citation_for(root, unit)}")
    citations = [citation_for(root, unit) for unit in units[:10]]

    run_id = now_id("analysis-run", title)
    stem = f"email-weekly-digest-{run_id[-10:]}"
    body = (
        "## 이번주 주요 주제\n\n"
        + "\n".join(topic_lines)
        + "\n\n## 핵심 발언자\n\n"
        + ("\n".join(sender_lines) if sender_lines else "- No senders detected.")
        + "\n\n## 주제별 공통 의견과 다른 의견\n\n"
        + "\n".join(thread_lines or ["- No thread grouping available."])
        + "\n\n## Action Items\n\n"
        + "\n".join(action_lines[:10] or ["- No action item candidates."])
        + "\n\n## Open Questions\n\n"
        + "\n".join(open_question_lines[:10] or ["- No open question candidates."])
        + "\n\n## 다음주 Watchlist\n\n"
        + "\n".join(topic_lines[:5])
        + "\n\n## 근거 자료\n\n"
        + "\n".join(f"- {citation}" for citation in citations)
        + "\n\n## Warnings\n\n"
        + "\n".join(f"- {warning}" for warning in warnings or ["None"])
    )
    path = write_analysis_page(root, stem, title, body, "email.weekly_digest", citations, analysis_method="heuristic_draft", trust_level="low")
    record_analysis_run(
        root,
        {
            "analysis_run_id": run_id,
            "profile_id": "email-analysis",
            "analysis_type": "email.weekly_digest",
            "output_path": path.relative_to(root).as_posix(),
            "unit_ids": [unit.get("unit_id") for unit in units],
            "warnings": warnings,
        },
    )
    return {"status": "ok", "profile_id": "email-analysis", "output_path": path.relative_to(root).as_posix(), "warnings": warnings}
