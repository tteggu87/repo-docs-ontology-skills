#!/usr/bin/env python3
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.packs.loader import load_profiles
from scripts.intelligence_contracts import load_manifest


def load(name):
    p = ROOT / f"warehouse/jsonl/{name}.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def require_fields(obj, fields, label):
    for f in fields:
        if f not in obj:
            raise SystemExit(f"missing {label}.{f}")


registry_contract = (load_manifest(ROOT, "registries.yaml").get("registries", {}) or {})


def required_for(name, fallback):
    spec = registry_contract.get(name, {}) or {}
    return spec.get("required_fields", fallback)


profiles = {profile.profile_id: profile for profile in load_profiles(ROOT)}
unit_kinds_by_profile = {profile.profile_id: set(profile.unit_kinds) for profile in profiles.values()}

docs_rows = load("documents")
for d in docs_rows:
    require_fields(d, required_for("documents", ["document_id", "raw_path"]), "document")
    if d.get("profile_id") and d["profile_id"] not in profiles:
        raise SystemExit(f"unknown document.profile_id: {d['profile_id']}")
docs = {x["document_id"] for x in docs_rows if "document_id" in x}

units = load("content_units")
unit_ids = set()
for u in units:
    require_fields(u, required_for("content_units", ["unit_id", "document_id", "source_family_id", "profile_id", "unit_kind", "sequence", "text"]), "content_unit")
    uid = u["unit_id"]
    if uid in unit_ids:
        raise SystemExit("duplicate unit_id")
    unit_ids.add(uid)
    if u.get("document_id") not in docs:
        raise SystemExit("unresolved document_id")
    if u.get("profile_id") not in profiles:
        raise SystemExit(f"unknown content_unit.profile_id: {u.get('profile_id')}")
    allowed_unit_kinds = unit_kinds_by_profile.get(u.get("profile_id"), set())
    if allowed_unit_kinds and u.get("unit_kind") not in allowed_unit_kinds:
        raise SystemExit(f"unit_kind not declared for profile: {u.get('unit_kind')}")

source_versions = load("source_versions")
sv_ids = set()
for sv in source_versions:
    require_fields(sv, required_for("source_versions", ["document_id", "raw_path", "content_hash", "source_family_id", "ingested_at"]), "source_version")
    sid = sv.get("source_version_id") or sv.get("export_version_id")
    if not sid:
        raise SystemExit("missing source_version.source_version_id/export_version_id")
    if sid in sv_ids:
        raise SystemExit("duplicate source_version/export_version id")
    sv_ids.add(sid)
    if sv["document_id"] not in docs:
        raise SystemExit("unresolved source_version.document_id")
    if sv.get("profile_id") and sv["profile_id"] not in profiles:
        raise SystemExit(f"unknown source_version.profile_id: {sv['profile_id']}")
    has_projected_wiki = bool(sv.get("affected_wiki_paths"))
    if "unit_count" in sv and has_projected_wiki:
        actual_count = sum(1 for unit in units if unit.get("document_id") == sv["document_id"])
        if sv["unit_count"] != actual_count:
            raise SystemExit(f"unit_count mismatch for {sid}: expected {sv['unit_count']} actual {actual_count}")
    for rel_path in sv.get("affected_wiki_paths", []) or []:
        if not (ROOT / rel_path).exists():
            raise SystemExit(f"missing affected_wiki_path: {rel_path}")
    for rel_path in sv.get("affected_wiki_paths", []) or []:
        if rel_path.startswith("wiki/sources/") and rel_path.endswith(".md"):
            text = (ROOT / rel_path).read_text(encoding="utf-8")
            if sv["document_id"] not in text:
                raise SystemExit(f"source page missing document_id: {rel_path}")
            if sv.get("source_version_id") and sv["source_version_id"] not in text:
                raise SystemExit(f"source page missing source_version_id: {rel_path}")

obs = load("observations")
obs_ids = set()
for o in obs:
    require_fields(o, required_for("observations", ["observation_id", "profile_id", "observation_type"]), "observation")
    oid = o["observation_id"]
    if oid in obs_ids:
        raise SystemExit("duplicate observation_id")
    obs_ids.add(oid)
    if o.get("unit_id") and o["unit_id"] not in unit_ids:
        raise SystemExit("unresolved observation.unit_id")
    if "." not in o["observation_type"]:
        raise SystemExit("invalid observation_type namespace")

analysis_runs = load("analysis_runs")
analysis_run_ids = {row.get("analysis_run_id") for row in analysis_runs if row.get("analysis_run_id")}
for run in analysis_runs:
    require_fields(run, required_for("analysis_runs", []), "analysis_run")
    if run.get("profile_id") and run["profile_id"] not in profiles:
        raise SystemExit(f"unknown analysis_run.profile_id: {run['profile_id']}")
    if run.get("output_path") and not (ROOT / run["output_path"]).exists():
        raise SystemExit(f"missing analysis output_path: {run['output_path']}")

analysis_findings = load("analysis_findings")
for finding in analysis_findings:
    require_fields(finding, required_for("analysis_findings", []), "analysis_finding")
    if finding.get("analysis_run_id") and analysis_run_ids and finding["analysis_run_id"] not in analysis_run_ids:
        raise SystemExit(f"unresolved analysis_findings.analysis_run_id: {finding['analysis_run_id']}")
    if finding.get("unit_id") and finding["unit_id"] not in unit_ids:
        raise SystemExit(f"unresolved analysis_findings.unit_id: {finding['unit_id']}")

registry_rows = {
    "documents": docs_rows,
    "content_units": units,
    "source_versions": source_versions,
    "observations": obs,
    "analysis_runs": analysis_runs,
    "analysis_findings": analysis_findings,
    "profiles": [{"profile_id": key} for key in profiles],
}

registry_keys = {"profiles": set(profiles)}
for registry_name, rows in registry_rows.items():
    spec = registry_contract.get(registry_name, {}) or {}
    key = spec.get("key")
    if key:
        registry_keys[registry_name] = {row.get(key) for row in rows if row.get(key)}

for registry_name, rows in registry_rows.items():
    spec = registry_contract.get(registry_name, {}) or {}
    for field, ref in (spec.get("references", {}) or {}).items():
        target_registry = ref.get("registry")
        target_keys = registry_keys.get(target_registry, set())
        for row in rows:
            value = row.get(field)
            if value and target_keys and value not in target_keys:
                raise SystemExit(f"unresolved {registry_name}.{field}: {value}")

print("OK registries")
