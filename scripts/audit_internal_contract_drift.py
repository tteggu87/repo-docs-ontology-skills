#!/usr/bin/env python3
"""Lightweight contract-drift audit for DocTology.

Checks a few high-value alignment points between:
- root AGENTS/docs
- bootstrap/sample workspace messaging
- intelligence manifests / capability registry
- current workbench/runtime surfaces

This is intentionally lightweight. It is not a full validator.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_path_contract(path: str) -> str:
    path = path.strip()
    if not path:
        return path
    if "?" in path:
        base, query = path.split("?", 1)
        query = re.sub(r"<[^>]+>", "<arg>", query)
        return f"{base}?{query}"
    return re.sub(r"<[^>]+>", "<arg>", path)


def find_manifest_paths(text: str) -> set[str]:
    return {
        normalize_path_contract(match.group(1))
        for match in re.finditer(r"^\s*path:\s*([^\n]+)$", text, re.MULTILINE)
    }


def find_manifest_action_keys(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"^\s*-\s+key:\s*([^\n]+)$", text, re.MULTILINE)
    }


def find_capability_keys(text: str) -> set[str]:
    return {
        match.group(1).strip()
        for match in re.finditer(r"^\s*-\s+key:\s*([^\n]+)$", text, re.MULTILINE)
    }


def required_items_present(text: str, required: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for item in required:
        if item not in text:
            missing.append(item)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit lightweight internal contract drift for DocTology.")
    parser.add_argument("--root", default=".", help="DocTology repo root")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    agents_root = read_text(root / "AGENTS.md")
    current_state = read_text(root / "docs" / "CURRENT_STATE.md")
    layers = read_text(root / "docs" / "LAYERS.md")
    wiki_agents = read_text(root / "wiki" / "AGENTS.md")
    wiki_readme = read_text(root / "wiki" / "README.md")
    actions_manifest = read_text(root / "intelligence" / "manifests" / "actions.yaml")
    workbench_manifest = read_text(root / "intelligence" / "manifests" / "workbench.yaml")
    capabilities = read_text(root / "intelligence" / "registry" / "capabilities.yaml")

    manifest_paths = find_manifest_paths(workbench_manifest)
    manifest_action_keys = find_manifest_action_keys(workbench_manifest)
    capability_keys = find_capability_keys(capabilities)

    expected_paths = {
        "/api/workbench/summary",
        "/api/workbench/feed",
        "/api/workbench/review",
        "/api/wiki/index",
        "/api/wiki/page/<arg>",
        "/api/wiki/related/<arg>",
        "/api/sources/<arg>",
        "/api/query/preview?q=<arg>",
        "/api/graph/inspect?seed_type=<arg>&seed=<arg>",
        "/api/warehouse/summary",
        "/api/meta/log/recent",
        "/api/actions/status",
        "/api/actions/reindex",
        "/api/actions/lint",
        "/api/actions/doctor",
        "/api/actions/save-analysis",
        "/api/actions/review-claim",
        "/api/actions/draft-source-summary",
    }

    expected_action_keys = {
        "status",
        "reindex",
        "lint",
        "doctor",
        "save_analysis",
        "review_claim",
        "draft_source_summary",
    }

    expected_capabilities = {
        "wiki.doctor",
        "workbench.summary",
        "workbench.review.summary",
        "workbench.source.detail",
        "workbench.graph.inspect",
        "workbench.warehouse.summary",
    }

    warnings: list[str] = []

    if "wiki/wiki/_meta/index.md" in agents_root:
        warnings.append("root AGENTS.md still points startup at wiki/wiki/_meta/index.md")
    if "wiki/_meta/index.md" not in agents_root:
        warnings.append("root AGENTS.md does not point startup at root wiki/_meta/index.md")
    if "docs/CURRENT_STATE.md" not in agents_root:
        warnings.append("root AGENTS.md does not require CURRENT_STATE.md at startup")

    for text_name, text in {
        "docs/CURRENT_STATE.md": current_state,
        "docs/LAYERS.md": layers,
    }.items():
        missing = required_items_present(text, ["wiki/wiki", "sample", "historical"]) 
        if missing:
            warnings.append(f"{text_name} does not clearly mention the deeper wiki/wiki sample/historical subtree")

    for text_name, text in {
        "wiki/AGENTS.md": wiki_agents,
        "wiki/README.md": wiki_readme,
    }.items():
        missing = required_items_present(text, ["sample workspace", "parent DocTology runtime"])
        if missing:
            warnings.append(f"{text_name} does not clearly describe the checked-in wiki tree as a lighter sample workspace with a separate parent runtime")

    if "shadow-first" not in actions_manifest:
        warnings.append("actions.yaml does not mention shadow-first ontology ingest behavior")
    if "ontology_reconcile_preview.json" not in actions_manifest:
        warnings.append("actions.yaml does not mention ontology shadow preview output")
    if "Do not silently rewrite source pages" not in actions_manifest:
        warnings.append("actions.yaml does not forbid silent wiki rewrite strongly enough")

    missing_paths = sorted(expected_paths - manifest_paths)
    if missing_paths:
        warnings.append("workbench manifest missing paths: " + ", ".join(missing_paths))

    missing_action_keys = sorted(expected_action_keys - manifest_action_keys)
    if missing_action_keys:
        warnings.append("workbench manifest missing action keys: " + ", ".join(missing_action_keys))

    missing_capabilities = sorted(expected_capabilities - capability_keys)
    if missing_capabilities:
        warnings.append("capabilities registry missing keys: " + ", ".join(missing_capabilities))

    payload = {
        "kind": "internal_contract_drift_audit",
        "root": str(root),
        "status": "pass" if not warnings else "warning",
        "warning_count": len(warnings),
        "warnings": warnings,
        "checked": {
            "workbench_path_count": len(manifest_paths),
            "workbench_action_key_count": len(manifest_action_keys),
            "capability_key_count": len(capability_keys),
        },
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("DocTology internal contract drift audit")
        print(f"- Root: {payload['root']}")
        print(f"- Status: {payload['status']}")
        print(f"- Warning count: {payload['warning_count']}")
        if warnings:
            print("")
            print("Warnings")
            for item in warnings:
                print(f"- {item}")
        else:
            print("")
            print("No high-value contract drift warnings detected.")

    return 0 if not warnings else 1


if __name__ == "__main__":
    raise SystemExit(main())
