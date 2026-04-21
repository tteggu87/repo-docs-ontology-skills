#!/usr/bin/env python3
"""Build a bounded graph projection from canonical benchmark JSONL registries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from incremental_support import read_jsonl, write_jsonl
except ModuleNotFoundError:
    from scripts.incremental_support import read_jsonl, write_jsonl

REPO_ROOT = Path(__file__).resolve().parent.parent


def assert_safe_root(project_root: Path, *, allow_main_repo: bool = False) -> None:
    if allow_main_repo:
        return
    if project_root.resolve() == REPO_ROOT.resolve():
        raise ValueError(
            "Refusing to build graph projection against the main DocTology repo root without allow_main_repo=True."
        )


def warehouse_jsonl_dir(project_root: Path) -> Path:
    return project_root / "warehouse" / "jsonl"


def graph_projection_dir(project_root: Path) -> Path:
    return project_root / "warehouse" / "graph_projection"


def build_graph_projection_from_jsonl(project_root_arg: str | Path, *, allow_main_repo: bool = False) -> dict[str, Any]:
    project_root = Path(project_root_arg).resolve()
    assert_safe_root(project_root, allow_main_repo=allow_main_repo)
    warehouse_dir = warehouse_jsonl_dir(project_root)
    graph_dir = graph_projection_dir(project_root)
    graph_dir.mkdir(parents=True, exist_ok=True)

    documents = read_jsonl(warehouse_dir / "documents.jsonl")
    entities = read_jsonl(warehouse_dir / "entities.jsonl")
    claims = read_jsonl(warehouse_dir / "claims.jsonl")
    derived_edges = read_jsonl(warehouse_dir / "derived_edges.jsonl")

    nodes: list[dict[str, Any]] = []
    node_ids: set[str] = set()

    def add_node(node_id: str | None, label: str | None, kind: str, **extra: Any) -> None:
        if not node_id or node_id in node_ids:
            return
        node_ids.add(node_id)
        payload = {"id": node_id, "label": label or node_id, "kind": kind}
        payload.update({key: value for key, value in extra.items() if value not in (None, "", [], {})})
        nodes.append(payload)

    for row in documents:
        add_node(
            row.get("document_id"),
            str(row.get("title") or row.get("document_id") or "document"),
            "document",
            source_page=row.get("source_page"),
            raw_path=row.get("raw_path"),
        )
    for row in entities:
        add_node(
            row.get("entity_id"),
            str(row.get("label") or row.get("entity_id") or "entity"),
            "entity",
            source_page=row.get("source_page"),
            aliases=row.get("aliases"),
            entity_type=row.get("type"),
            lifecycle_state=row.get("lifecycle_state"),
            state_updated_at=row.get("state_updated_at"),
            temporal_scope=row.get("temporal_scope"),
        )
    for row in claims:
        add_node(
            row.get("claim_id"),
            str(row.get("claim_text") or row.get("claim_id") or "claim"),
            "claim",
            source_page=row.get("source_page"),
            review_state=row.get("review_state"),
            confidence=row.get("confidence"),
            support_status=row.get("support_status"),
            truth_basis=row.get("truth_basis"),
            evidence_count=row.get("evidence_count"),
            lifecycle_state=row.get("lifecycle_state"),
            state_updated_at=row.get("state_updated_at"),
            temporal_scope=row.get("temporal_scope"),
        )

    edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    for row in derived_edges:
        source = str(row.get("source") or "")
        target = str(row.get("target") or "")
        label = str(row.get("label") or "related_to")
        if not source or not target:
            continue
        if source not in node_ids or target not in node_ids:
            continue
        key = (source, target, label)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        payload = {"source": source, "target": target, "label": label}
        payload.update(
            {
                key: value
                for key, value in row.items()
                if key not in {"source", "target", "label"} and value not in (None, "", [], {})
            }
        )
        edges.append(payload)

    nodes_path = graph_dir / "nodes.jsonl"
    edges_path = graph_dir / "edges.jsonl"
    write_jsonl(nodes_path, nodes)
    write_jsonl(edges_path, edges)

    return {
        "root": str(project_root),
        "nodes_path": str(nodes_path.relative_to(project_root)),
        "edges_path": str(edges_path.relative_to(project_root)),
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build graph projection from canonical benchmark JSONL.")
    parser.add_argument("--root", default=".", help="Project root containing warehouse/jsonl/.")
    parser.add_argument(
        "--allow-main-repo",
        action="store_true",
        help="Explicitly allow writes against the main DocTology repo root.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_graph_projection_from_jsonl(args.root, allow_main_repo=args.allow_main_repo)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
