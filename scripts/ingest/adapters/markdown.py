from __future__ import annotations
from pathlib import Path
from .common import ParsedSource, file_document_id, stable_unit_id

def parse_markdown(path: Path, profile_id: str, source_family_id: str, unit_kind: str = "paragraph", raw_path: str | None = None) -> ParsedSource:
    lines = path.read_text(encoding="utf-8").splitlines()
    rel = raw_path or path.as_posix()
    doc_id = file_document_id(rel)
    units=[]
    seq=0
    heading=None
    in_frontmatter=False
    frontmatter_done=False
    if lines and lines[0].strip() == "---":
        in_frontmatter=True
    buf=[]; start=None
    for i,l in enumerate(lines, start=1):
        if in_frontmatter:
            if i > 1 and l.strip() == "---":
                in_frontmatter=False
                frontmatter_done=True
            continue
        if l.startswith("#"):
            if buf:
                seq += 1
                text = "\n".join(buf).strip()
                units.append({"unit_id": stable_unit_id(doc_id, unit_kind, seq, text), "document_id": doc_id, "source_family_id": source_family_id, "profile_id": profile_id, "unit_kind": unit_kind, "sequence": seq, "heading": heading, "text": text, "line_start": start, "line_end": i-1})
                buf=[]
            heading=l.lstrip('#').strip()
            start=None
            continue
        if not l.strip():
            if buf:
                seq+=1
                text="\n".join(buf).strip()
                units.append({"unit_id": stable_unit_id(doc_id, unit_kind, seq, text), "document_id": doc_id, "source_family_id": source_family_id, "profile_id": profile_id, "unit_kind": unit_kind, "sequence": seq, "heading": heading, "text": text, "line_start": start, "line_end": i-1})
                buf=[]
                start=None
        else:
            if start is None:
                start=i
            buf.append(l)
    if buf:
        seq+=1
        text="\n".join(buf).strip()
        units.append({"unit_id": stable_unit_id(doc_id, unit_kind, seq, text), "document_id": doc_id, "source_family_id": source_family_id, "profile_id": profile_id, "unit_kind": unit_kind, "sequence": seq, "heading": heading, "text": text, "line_start": start, "line_end": len(lines)})
    return ParsedSource(document={"document_id":doc_id,"raw_path":rel,"profile_id":profile_id,"source_family_id":source_family_id}, units=units)
