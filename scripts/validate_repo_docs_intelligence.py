#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.intelligence_contracts import load_contract_index, load_manifest, load_yaml_file


REQUIRED_DOCS = [
    "docs/README.md",
    "docs/CURRENT_STATE.md",
    "docs/ARCHITECTURE.md",
    "docs/LAYERS.md",
    "docs/ROADMAP.md",
    "docs/IMPACT_SUMMARY.md",
]


def _fail(message: str) -> None:
    raise SystemExit(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _list_rows(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    rows = data.get(key, []) or []
    _require(isinstance(rows, list), f"{key} must be a list")
    return [row for row in rows if isinstance(row, dict)]


def validate(repo_root: Path) -> None:
    for rel in REQUIRED_DOCS:
        _require((repo_root / rel).exists(), f"missing required docs file: {rel}")

    contract_index = load_contract_index(repo_root)
    for rel in contract_index.get("read_order", []) or []:
        _require((repo_root / str(rel)).exists(), f"contract_index read_order missing file: {rel}")

    actions = load_manifest(repo_root, "actions.yaml")
    action_keys = {row.get("key") for row in _list_rows(actions, "actions") if row.get("key")}
    _require(bool(action_keys), "actions.yaml must declare actions")

    capabilities = load_yaml_file(repo_root / "intelligence/registry/capabilities.yaml")
    for capability in _list_rows(capabilities, "capabilities"):
        key = capability.get("key")
        action = capability.get("action")
        implementation = capability.get("implementation")
        _require(bool(key), "capability missing key")
        _require(action in action_keys, f"capability references unknown action: {key} -> {action}")
        _require(bool(implementation), f"capability missing implementation: {key}")

    datasets = load_manifest(repo_root, "datasets.yaml")
    for dataset in _list_rows(datasets, "datasets"):
        rel_path = dataset.get("path")
        key = dataset.get("key")
        _require(bool(key), "dataset missing key")
        _require(bool(rel_path), f"dataset missing path: {key}")

    current_state = (repo_root / "docs/CURRENT_STATE.md").read_text(encoding="utf-8")
    _require("Strict LLM-first semantic workflow" in current_state, "CURRENT_STATE must document strict LLM-first workflow")
    _require("intelligence/contract_index.yaml" in current_state, "CURRENT_STATE must document contract_index")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate docs/intelligence alignment for DocTology.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Repository root to validate.")
    args = parser.parse_args()
    validate(Path(args.repo_root).resolve())
    print("OK repo docs intelligence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

