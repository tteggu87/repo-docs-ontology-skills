#!/usr/bin/env python3
from __future__ import annotations
import sys, argparse, json
from pathlib import Path
from datetime import date, datetime

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from scripts.ingest.resolver import resolve_family, PROFILE_BY_FAMILY
from scripts.ingest.adapters.common import file_content_hash, source_version_id
from scripts.ingest.adapters.email_md_txt import parse_email_source
from scripts.ingest.adapters.education_md_txt import parse_education_source
from scripts.ingest.adapters.report_md_txt import parse_report_source
from scripts.ingest.adapters.markdown import parse_markdown
from scripts.packs.loader import get_profile

ALLOWED_RAW_PREFIXES = ["raw/inbox", "raw/processed", "raw/notes"]


def upsert_jsonl(path: Path, key: str, rows: list[dict]):
    idx={}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            if line.strip():
                obj=json.loads(line); idx[obj.get(key)] = obj
    for r in rows:
        idx[r[key]] = r
    out=[v for _,v in sorted(idx.items(), key=lambda x: str(x[0])) if _ is not None]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out)+("\n" if out else ""), encoding='utf-8')


def _safety(root: Path, src: Path) -> str:
    if not src.exists(): raise ValueError("source path does not exist")
    if not src.is_file(): raise ValueError("source path is not a file")
    rp = src.resolve().relative_to(root.resolve()).as_posix()
    if not any(rp.startswith(p+"/") for p in ALLOWED_RAW_PREFIXES):
        raise ValueError(f"source path must be under {ALLOWED_RAW_PREFIXES}")
    if src.suffix.lower() not in {".md", ".txt"}:
        raise ValueError("unsupported extension")
    return rp


def ingest_source(root: Path, source: str, profile_id: str | None = None) -> dict:
    src = (root / source).resolve() if not Path(source).is_absolute() else Path(source).resolve()
    raw_path = _safety(root, src)
    detected = resolve_family(root, src)
    warning = None
    if profile_id:
        profile = get_profile(root, profile_id)
        family = profile.source_families[0]
        if detected != family:
            warning = f"profile/family mismatch: detected={detected} profile_family={family}"
    else:
        family = detected
        profile_id = PROFILE_BY_FAMILY.get(family, "generic-analysis")
    if profile_id=='email-analysis': parsed=parse_email_source(src, profile_id=profile_id, source_family_id=family, raw_path=raw_path)
    elif profile_id=='education-analysis': parsed=parse_education_source(src, profile_id=profile_id, source_family_id=family)
    elif profile_id=='report-consistency-analysis': parsed=parse_report_source(src, profile_id=profile_id, source_family_id=family)
    else: parsed=parse_markdown(src, profile_id, family, raw_path=raw_path)

    content_hash=file_content_hash(src)
    srcver=source_version_id(parsed.document['document_id'], content_hash)
    now = datetime.utcnow().isoformat()+'Z'
    doc = dict(parsed.document)
    doc.update({"raw_path": raw_path, "content_hash": content_hash, "latest_source_version_id": srcver, "ingested_at": now, "title": src.stem})
    srcver_row={"source_version_id":srcver,"document_id":doc['document_id'],"raw_path":raw_path,"content_hash":content_hash,"unit_count":len(parsed.units),"ingested_at":now}

    upsert_jsonl(root/'warehouse/jsonl/documents.jsonl', 'document_id', [doc])
    upsert_jsonl(root/'warehouse/jsonl/content_units.jsonl', 'unit_id', parsed.units)
    upsert_jsonl(root/'warehouse/jsonl/source_versions.jsonl', 'source_version_id', [srcver_row])
    return {"profile_id":profile_id,"source_family_id":family,"warning":warning,"units":len(parsed.units),"affected_registry_paths":["warehouse/jsonl/documents.jsonl","warehouse/jsonl/content_units.jsonl","warehouse/jsonl/source_versions.jsonl"],"affected_wiki_paths":[]}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('source'); ap.add_argument('--profile')
    args=ap.parse_args(); print(json.dumps(ingest_source(ROOT,args.source,args.profile), ensure_ascii=False))

if __name__=='__main__':
    main()
