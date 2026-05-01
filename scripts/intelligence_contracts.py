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

