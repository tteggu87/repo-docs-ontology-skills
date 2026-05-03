from pathlib import Path

from .common import ParsedSource, stable_unit_id
from .markdown import parse_markdown


def parse_email_source(
    path: Path,
    profile_id: str = "email-analysis",
    source_family_id: str = "email-md-txt",
    raw_path: str | None = None,
):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if "--- email ---" not in text:
        parsed = parse_markdown(path, profile_id, source_family_id, unit_kind="email_message", raw_path=raw_path)
        parsed.document["warnings"] = ["email delimiter not found; used markdown fallback"]
        return parsed

    rel = raw_path or path.as_posix()
    doc = parse_markdown(path, profile_id, source_family_id, unit_kind="email_message", raw_path=rel).document
    units = []
    warnings: list[str] = []
    seq = 0
    i = 0
    while i < len(lines):
        if lines[i].strip() != "--- email ---":
            i += 1
            continue
        delimiter_line = i + 1
        i += 1
        header = []
        body = []
        in_body = False
        header_start_line = i + 1
        body_start_line = None

        while i < len(lines) and lines[i].strip() != "--- email ---":
            if not in_body and lines[i].strip() == "":
                in_body = True
                body_start_line = i + 2
            elif in_body:
                body.append(lines[i])
            else:
                header.append(lines[i])
            i += 1

        header_end_line = (body_start_line - 2) if body_start_line else i
        meta = {}
        for h in header:
            if ":" in h:
                k, v = h.split(":", 1)
                meta[k.strip().lower()] = v.strip()

        seq += 1
        body_lines = [b for b in body if b.strip()]
        body_text = "\n".join(body_lines).strip()
        if not body_text:
            warnings.append(f"empty email body skipped at delimiter line {delimiter_line}")
            continue

        if body_start_line is None:
            body_start_line = delimiter_line + 1
        body_end_line = i

        units.append(
            {
                "unit_id": stable_unit_id(doc["document_id"], "email_message", seq, body_text),
                "document_id": doc["document_id"],
                "source_family_id": source_family_id,
                "profile_id": profile_id,
                "unit_kind": "email_message",
                "sequence": seq,
                "heading": None,
                "text": body_text,
                "line_start": body_start_line,
                "line_end": body_end_line,
                "header_start_line": header_start_line,
                "header_end_line": header_end_line,
                "author_name": meta.get("from"),
                "recipients": meta.get("to"),
                "timestamp": meta.get("date"),
                "subject": meta.get("subject"),
                "thread_id": meta.get("thread-id"),
            }
        )
    if warnings:
        doc["warnings"] = warnings
    return ParsedSource(document=doc, units=units)
