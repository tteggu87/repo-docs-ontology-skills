from __future__ import annotations
from pathlib import Path

PROFILE_BY_FAMILY = {
    "email-md-txt": "email-analysis",
    "education-md-txt": "education-analysis",
    "report-md-txt": "report-consistency-analysis",
}


def resolve_family(root: Path, source: Path) -> str:
    s = source.as_posix().lower()
    hits = []
    if "/email/" in s:
        hits.append("email-md-txt")
    if "/education/" in s:
        hits.append("education-md-txt")
    if "/reports/" in s:
        hits.append("report-md-txt")
    if "kakaotalk_chat_" in s:
        hits.append("kakao-agent-korea-chat")
    if len(hits) > 1:
        raise ValueError(f"Ambiguous source family: {hits}")
    if hits:
        return hits[0]
    if source.suffix.lower() in {".md", ".txt"}:
        return "generic-md-note"
    raise ValueError("No source family match")
