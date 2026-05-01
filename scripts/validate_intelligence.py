#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.intelligence_contracts import load_contract_index, load_manifest, load_policy
from scripts.packs.loader import load_profiles


def _fail(message: str) -> None:
    raise SystemExit(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _help_text(script: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(ROOT / script), "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    _require(proc.returncode == 0, f"workflow CLI help failed: {script}")
    return proc.stdout


def _validate_contract_index() -> None:
    index = load_contract_index(ROOT)
    _require(index.get("rules", {}).get("yaml_role") == "contract_only", "contract_index must declare YAML as contract_only")
    read_order = index.get("read_order", []) or []
    _require(bool(read_order), "contract_index read_order must not be empty")
    for rel_path in read_order:
        _require((ROOT / str(rel_path)).exists(), f"contract_index read_order missing file: {rel_path}")


def _validate_semantic_boundary() -> None:
    boundary = load_policy(ROOT, "semantic_boundary.yaml")
    _require(boundary.get("semantic_fallback_allowed") is False, "semantic fallback must not be allowed")
    _require(boundary.get("helper_llm_required_for_semantic_workflows") is True, "helper LLM must be required")
    forbidden = set(boundary.get("deterministic_code_forbidden", []) or [])
    _require("infer_semantic_truth" in forbidden, "deterministic code must not infer semantic truth")
    _require("draft_answers" in forbidden, "deterministic code must not draft answers")
    units = boundary.get("content_units", {}) or {}
    _require(units.get("role") == "citation_anchor", "content_units must be citation anchors")
    _require(units.get("forbidden_role") == "rag_answer_chunk", "content_units must not be RAG answer chunks")


def _validate_workflows() -> set[str]:
    data = load_manifest(ROOT, "semantic_workflows.yaml")
    workflows: dict[str, Any] = data.get("workflows", {}) or {}
    _require(bool(workflows), "semantic_workflows must declare workflows")
    allowed_targets: set[str] = set()
    for name, workflow in workflows.items():
        _require(workflow.get("requires_helper_llm") is True, f"{name} must require helper LLM")
        _require(workflow.get("fallback_allowed") is False, f"{name} must not allow semantic fallback")
        function = str(workflow.get("function", ""))
        _require(bool(function), f"{name} missing function target")
        allowed_targets.add(function)
        cli = str(workflow.get("cli", ""))
        _require(bool(cli), f"{name} missing cli")
        help_text = _help_text(cli)
        for flag in workflow.get("explicit_prompt_flags", []) or []:
            _require(str(flag) in help_text, f"{name} CLI flag mismatch: {flag}")
    return allowed_targets


def _validate_page_policy() -> None:
    data = load_manifest(ROOT, "page_policy.yaml")
    queryable = data.get("queryable", {}) or {}
    denied_status = set(queryable.get("denied_status", []) or [])
    denied_methods = set(queryable.get("denied_analysis_methods", []) or [])
    denied_sections = set(queryable.get("denied_sections", []) or [])
    _require("draft" in denied_status, "queryable draft pages must be denied")
    _require("llm_compile_proposal" in denied_methods, "compile proposals must be denied as query evidence")
    _require("_meta" in denied_sections, "meta pages must not be direct query evidence")


def _validate_relation_types() -> None:
    text = (ROOT / "intelligence/manifests/relation_types.yaml").read_text(encoding="utf-8")
    seen: set[str] = set()
    for raw in text.splitlines():
        if not raw.startswith("  ") or raw.startswith("    "):
            continue
        if ":" not in raw:
            continue
        key = raw.strip().split(":", 1)[0]
        if key in {"version", "purpose", "yaml_role", "relation_types"}:
            continue
        _require(key not in seen, f"duplicate relation type: {key}")
        seen.add(key)
    data = load_manifest(ROOT, "relation_types.yaml")
    relation_types = data.get("relation_types", {}) or {}
    _require(set(relation_types) == seen, "relation type parser mismatch")
    _require(bool(relation_types), "relation_types must not be empty")
    for name, spec in relation_types.items():
        _require(isinstance(spec, dict), f"relation type must be a mapping: {name}")
        _require(bool(spec.get("inverse")), f"relation type missing inverse: {name}")
        _require(bool(spec.get("from")), f"relation type missing from: {name}")
        _require(bool(spec.get("to")), f"relation type missing to: {name}")
        _require("evidence_required" in spec, f"relation type missing evidence_required: {name}")
        _require("approval_required" in spec, f"relation type missing approval_required: {name}")
        _require(isinstance(spec.get("evidence_required"), bool), f"relation evidence_required must be bool: {name}")
        _require(isinstance(spec.get("approval_required"), bool), f"relation approval_required must be bool: {name}")


def _validate_profile_compile_targets(allowed_targets: set[str]) -> None:
    for profile in load_profiles(ROOT):
        _require(profile.compile_target in allowed_targets, f"profile compile target mismatch: {profile.profile_id} -> {profile.compile_target}")


def _validate_meta_surfaces() -> None:
    data = load_manifest(ROOT, "meta_surfaces.yaml")
    surfaces = data.get("surfaces", {}) or {}
    _require(bool(surfaces), "meta_surfaces must declare surfaces")
    selection = [name for name, spec in surfaces.items() if "query_selection" in (spec.get("used_by", []) or [])]
    answer = [name for name, spec in surfaces.items() if "query_answer" in (spec.get("used_by", []) or [])]
    _require(bool(selection), "query_selection must have meta surfaces")
    _require(bool(answer), "query_answer must have meta surfaces")
    for name, spec in surfaces.items():
        _require(bool(spec.get("path")), f"meta surface missing path: {name}")


def main() -> int:
    _validate_contract_index()
    _validate_semantic_boundary()
    allowed_targets = _validate_workflows()
    _validate_page_policy()
    _validate_relation_types()
    _validate_profile_compile_targets(allowed_targets)
    _validate_meta_surfaces()
    print("OK intelligence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
