from __future__ import annotations
from pathlib import Path
from .common import ParsedSource, file_document_id, stable_unit_id


def parse_markdown(path: Path, profile_id: str, source_family_id: str, unit_kind: str = "paragraph") -> ParsedSource:
    lines = path.read_text(encoding="utf-8").splitlines()
    doc_id = file_document_id(path)
    units=[]
    buf=[]; start=1; seq=0; heading=None
    for i,l in enumerate(lines, start=1):
        if l.startswith("#"):
            heading=l.lstrip('#').strip()
        if not l.strip():
            if buf:
                seq+=1
                text="\n".join(buf).strip()
                units.append({"unit_id": stable_unit_id(doc_id, unit_kind, seq, text), "document_id": doc_id, "source_family_id": source_family_id, "profile_id": profile_id, "unit_kind": unit_kind, "sequence": seq, "heading": heading, "text": text, "line_start": start, "line_end": i-1})
                buf=[]
            start=i+1
        else:
            if not buf:
                start=i
            buf.append(l)
    if buf:
        seq+=1
        text="\n".join(buf).strip()
        units.append({"unit_id": stable_unit_id(doc_id, unit_kind, seq, text), "document_id": doc_id, "source_family_id": source_family_id, "profile_id": profile_id, "unit_kind": unit_kind, "sequence": seq, "heading": heading, "text": text, "line_start": start, "line_end": len(lines)})
    return ParsedSource(document={"document_id":doc_id,"path":path.as_posix(),"profile_id":profile_id,"source_family_id":source_family_id}, units=units)
