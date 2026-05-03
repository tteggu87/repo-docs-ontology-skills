from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml_file(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency error path
        raise RuntimeError("PyYAML is required for intelligence contract loading.") from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML contract must be a mapping: {path}")
    return data


def manifest_path(root: Path, name: str) -> Path:
    return root / "intelligence" / "manifests" / name


def policy_path(root: Path, name: str) -> Path:
    return root / "intelligence" / "policies" / name


def load_manifest(root: Path, name: str) -> dict[str, Any]:
    return load_yaml_file(manifest_path(root, name))


def load_policy(root: Path, name: str) -> dict[str, Any]:
    return load_yaml_file(policy_path(root, name))


def semantic_workflow_targets(root: Path) -> set[str]:
    data = load_manifest(root, "semantic_workflows.yaml")
    workflows = data.get("workflows", {}) or {}
    return {str(row.get("function", "")) for row in workflows.values() if row.get("function")}


def load_contract_index(root: Path) -> dict[str, Any]:
    return load_yaml_file(root / "intelligence" / "contract_index.yaml")


def load_proposal_policy(root: Path, proposal_kind: str = "compile_proposal") -> dict[str, Any]:
    data = load_policy(root, "proposal_lifecycle.yaml")
    lifecycle = data.get("proposal_lifecycle", {}) or {}
    policy = lifecycle.get(proposal_kind, {}) or {}
    if not isinstance(policy, dict) or not policy:
        raise ValueError(f"Missing proposal lifecycle policy: {proposal_kind}")
    return policy


def meta_surface_contents(root: Path, stage: str, default_max_chars: int = 16000) -> dict[str, str]:
    data = load_manifest(root, "meta_surfaces.yaml")
    surfaces = data.get("surfaces", {}) or {}
    out: dict[str, str] = {}
    for name, spec in surfaces.items():
        if not isinstance(spec, dict):
            continue
        if stage not in (spec.get("used_by", []) or []):
            continue
        rel_path = str(spec.get("path", ""))
        if not rel_path:
            continue
        max_chars = int(spec.get("max_chars", default_max_chars) or default_max_chars)
        path = root / rel_path
        out[str(name)] = path.read_text(encoding="utf-8")[:max_chars] if path.exists() else ""
    return out
