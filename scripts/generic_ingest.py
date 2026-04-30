#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import argparse, json
from pathlib import Path
from scripts.ingest.resolver import resolve_family, PROFILE_BY_FAMILY
from scripts.ingest.adapters.email_md_txt import parse_email_source
from scripts.ingest.adapters.education_md_txt import parse_education_source
from scripts.ingest.adapters.report_md_txt import parse_report_source
from scripts.ingest.adapters.markdown import parse_markdown

ROOT = Path(__file__).resolve().parent.parent


def upsert_jsonl(path: Path, key: str, rows: list[dict]):
    existing=[]
    idx={}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip(): continue
            obj=json.loads(line); idx[obj[key]]=obj; existing.append(obj)
    for r in rows:
        idx[r[key]]=r
    out=list(idx.values())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in out)+("\n" if out else ""), encoding='utf-8')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source')
    ap.add_argument('--profile')
    args=ap.parse_args()
    src=(ROOT/args.source).resolve() if not Path(args.source).is_absolute() else Path(args.source)
    family=resolve_family(ROOT, src)
    profile=args.profile or PROFILE_BY_FAMILY.get(family, 'generic-analysis')
    if profile=='email-analysis': parsed=parse_email_source(src)
    elif profile=='education-analysis': parsed=parse_education_source(src)
    elif profile=='report-consistency-analysis': parsed=parse_report_source(src)
    else: parsed=parse_markdown(src, profile, family)
    upsert_jsonl(ROOT/'warehouse/jsonl/documents.jsonl', 'document_id', [parsed.document])
    upsert_jsonl(ROOT/'warehouse/jsonl/content_units.jsonl', 'unit_id', parsed.units)
    print(json.dumps({"profile_id":profile,"source_family_id":family,"affected_registry_paths":["warehouse/jsonl/documents.jsonl","warehouse/jsonl/content_units.jsonl"],"units":len(parsed.units)}, ensure_ascii=False))

if __name__=='__main__':
    main()
