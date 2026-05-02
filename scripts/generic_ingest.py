#!/usr/bin/env python3
from __future__ import annotations
import sys, argparse, json
import importlib
from pathlib import Path
from datetime import UTC, datetime

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from scripts.ingest.resolver import resolve_family, resolve_profile_for_family
from scripts.ingest.adapters.common import file_content_hash, source_version_id
from scripts.ingest.adapters.markdown import parse_markdown
from scripts.packs.loader import get_profile
from scripts.wiki_projection import refresh_wiki_after_ingest

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
    try:
        rp = src.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("source path must live inside this repository") from exc
    if not any(rp.startswith(p+"/") for p in ALLOWED_RAW_PREFIXES):
        raise ValueError(f"source path must be under {ALLOWED_RAW_PREFIXES}")
    if src.suffix.lower() not in {".md", ".txt"}:
        raise ValueError("unsupported extension")
    return rp


def _load_parse_callable(target: str):
    module_name, function_name = target.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def _parse_with_profile(root: Path, src: Path, profile_id: str, family: str, raw_path: str):
    try:
        profile = get_profile(root, profile_id)
        parser = _load_parse_callable(profile.parse_target)
        return parser(src, profile_id=profile_id, source_family_id=family, raw_path=raw_path)
    except KeyError:
        return parse_markdown(src, profile_id, family, raw_path=raw_path)


def ingest_source(root: Path, source: str, profile_id: str | None = None, allow_profile_family_mismatch: bool = False) -> dict:
    src = (root / source).resolve() if not Path(source).is_absolute() else Path(source).resolve()
    raw_path = _safety(root, src)
    warnings: list[str] = []

    if profile_id:
        profile = get_profile(root, profile_id)
        family = profile.source_families[0]
        try:
            detected = resolve_family(root, src)
            if detected != family:
                msg = f"profile/family mismatch: detected={detected} profile_family={family}"
                if allow_profile_family_mismatch:
                    warnings.append(msg)
                else:
                    raise ValueError(msg)
        except ValueError as exc:
            if "Ambiguous source family" in str(exc):
                warnings.append(f"family detection ambiguous; profile family forced: {family}")
            else:
                raise
    else:
        family = resolve_family(root, src)
        profile_id = resolve_profile_for_family(root, family)

    parsed = _parse_with_profile(root, src, profile_id, family, raw_path)

    warnings.extend(parsed.document.get("warnings", []))
    content_hash=file_content_hash(src)
    srcver=source_version_id(parsed.document['document_id'], content_hash)
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    registry_paths=["warehouse/jsonl/documents.jsonl","warehouse/jsonl/content_units.jsonl","warehouse/jsonl/source_versions.jsonl"]
    doc = dict(parsed.document)
    doc.update({"raw_path": raw_path, "content_hash": content_hash, "latest_source_version_id": srcver, "ingested_at": now, "title": src.stem})
    srcver_row={"source_version_id":srcver,"document_id":doc['document_id'],"raw_path":raw_path,"content_hash":content_hash,"profile_id":profile_id,"source_family_id":family,"unit_count":len(parsed.units),"adapter":f"{profile_id}:parse","affected_registry_paths":registry_paths,"affected_wiki_paths":[],"warnings":warnings,"ingested_at":now}
    affected_wiki_paths = refresh_wiki_after_ingest(root, doc, srcver_row, parsed.units, warnings, raw_path)
    srcver_row["affected_wiki_paths"] = affected_wiki_paths

    upsert_jsonl(root/'warehouse/jsonl/documents.jsonl', 'document_id', [doc])
    upsert_jsonl(root/'warehouse/jsonl/content_units.jsonl', 'unit_id', parsed.units)
    upsert_jsonl(root/'warehouse/jsonl/source_versions.jsonl', 'source_version_id', [srcver_row])
    return {"profile_id":profile_id,"source_family_id":family,"warnings":warnings,"units":len(parsed.units),"affected_registry_paths":registry_paths,"affected_wiki_paths":affected_wiki_paths}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('source'); ap.add_argument('--profile'); ap.add_argument('--allow-profile-family-mismatch', action='store_true')
    args=ap.parse_args(); print(json.dumps(ingest_source(ROOT,args.source,args.profile,args.allow_profile_family_mismatch), ensure_ascii=False))

if __name__=='__main__':
    main()
