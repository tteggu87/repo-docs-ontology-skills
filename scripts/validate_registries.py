#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    p = ROOT / f"warehouse/jsonl/{name}.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def require_fields(obj, fields, label):
    for f in fields:
        if f not in obj:
            raise SystemExit(f"missing {label}.{f}")


docs_rows = load("documents")
docs = {x["document_id"] for x in docs_rows if "document_id" in x}

units = load("content_units")
unit_ids = set()
for u in units:
    require_fields(u, ["unit_id", "document_id", "source_family_id", "profile_id", "unit_kind", "sequence", "text"], "content_unit")
    uid = u["unit_id"]
    if uid in unit_ids:
        raise SystemExit("duplicate unit_id")
    unit_ids.add(uid)
    if u.get("document_id") not in docs:
        raise SystemExit("unresolved document_id")

source_versions = load("source_versions")
sv_ids = set()
for sv in source_versions:
    require_fields(sv, ["source_version_id", "document_id", "raw_path", "content_hash", "profile_id", "source_family_id", "unit_count", "ingested_at"], "source_version")
    sid = sv["source_version_id"]
    if sid in sv_ids:
        raise SystemExit("duplicate source_version_id")
    sv_ids.add(sid)
    if sv["document_id"] not in docs:
        raise SystemExit("unresolved source_version.document_id")

obs = load("observations")
obs_ids = set()
for o in obs:
    require_fields(o, ["observation_id", "profile_id", "observation_type"], "observation")
    oid = o["observation_id"]
    if oid in obs_ids:
        raise SystemExit("duplicate observation_id")
    obs_ids.add(oid)
    if o.get("unit_id") and o["unit_id"] not in unit_ids:
        raise SystemExit("unresolved observation.unit_id")
    if "." not in o["observation_type"]:
        raise SystemExit("invalid observation_type namespace")

print("OK registries")
