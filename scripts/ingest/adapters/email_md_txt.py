from pathlib import Path
from .markdown import parse_markdown
from .common import stable_unit_id

def parse_email_source(path: Path, profile_id: str = "email-analysis", source_family_id: str = "email-md-txt", raw_path: str | None = None):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if "--- email ---" not in text:
        parsed = parse_markdown(path, profile_id, source_family_id, unit_kind="email_message", raw_path=raw_path)
        parsed.document["warnings"] = ["email delimiter not found; used markdown fallback"]
        return parsed
    rel = raw_path or path.as_posix()
    doc = parse_markdown(path, profile_id, source_family_id, unit_kind="email_message", raw_path=rel).document
    units=[]
    seq=0
    i=0
    while i < len(lines):
        if lines[i].strip() != "--- email ---":
            i += 1
            continue
        block_start=i+1
        i += 1
        header=[]; body=[]; in_body=False
        while i < len(lines) and lines[i].strip() != "--- email ---":
            if not in_body and lines[i].strip() == "":
                in_body=True
            elif in_body:
                body.append(lines[i])
            else:
                header.append(lines[i])
            i += 1
        meta={}
        for h in header:
            low=h.lower()
            if ":" in h:
                k,v=h.split(":",1)
                meta[k.strip().lower()] = v.strip()
        seq += 1
        body_text="\n".join([b for b in body if b.strip()]).strip()
        units.append({
            "unit_id": stable_unit_id(doc["document_id"], "email_message", seq, body_text), "document_id": doc["document_id"],
            "source_family_id": source_family_id, "profile_id": profile_id, "unit_kind": "email_message", "sequence": seq,
            "heading": None, "text": body_text, "line_start": block_start, "line_end": i,
            "author_name": meta.get("from"), "recipients": meta.get("to"), "timestamp": meta.get("date"), "subject": meta.get("subject"), "thread_id": meta.get("thread-id")
        })
    return type("Parsed", (), {"document": doc, "units": units})
