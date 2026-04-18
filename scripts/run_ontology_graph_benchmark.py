#!/usr/bin/env python3
"""Reproduce baseline-vs-benchmark-vs-production measurements for DocTology."""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import time
from pathlib import Path
from typing import Any

try:
    from ontology_benchmark_ingest import ingest_ontology_benchmark
    from ontology_ingest import ingest_ontology
    from workbench.repository import WorkbenchRepository
except ModuleNotFoundError:
    from scripts.ontology_benchmark_ingest import ingest_ontology_benchmark
    from scripts.ontology_ingest import ingest_ontology
    from scripts.workbench.repository import WorkbenchRepository

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SANDBOX = REPO_ROOT.parent / "DocTology-benchmark-sandbox-ontology"
DEFAULT_QUERY_FIXTURES = [
    "neo4j kuzu ladybug",
    "ontology graphrag framework",
    "graph memory operators",
]


def prepare_sandbox(baseline_root: Path, sandbox_root: Path, *, reset: bool = True) -> None:
    baseline_root = baseline_root.resolve()
    sandbox_root = sandbox_root.resolve()
    if sandbox_root == baseline_root:
        raise ValueError("sandbox_root must differ from baseline_root")
    if sandbox_root in baseline_root.parents or baseline_root in sandbox_root.parents:
        raise ValueError("sandbox_root must be a separate sibling-style workspace, not nested under baseline_root")
    if sandbox_root in {REPO_ROOT.resolve(), REPO_ROOT.parent.resolve(), Path.home().resolve(), Path('/').resolve()}:
        raise ValueError("sandbox_root is unsafe for destructive reset")
    if reset and sandbox_root.exists():
        shutil.rmtree(sandbox_root)
    sandbox_root.mkdir(parents=True, exist_ok=True)
    for rel in ["raw", "wiki"]:
        src = baseline_root / rel
        dst = sandbox_root / rel
        if dst.exists():
            shutil.rmtree(dst)
        if src.exists():
            shutil.copytree(src, dst)
    (sandbox_root / "warehouse" / "jsonl").mkdir(parents=True, exist_ok=True)
    (sandbox_root / "warehouse" / "graph_projection").mkdir(parents=True, exist_ok=True)


def time_call(fn, rounds: int = 5) -> tuple[dict[str, Any], list[float]]:
    timings: list[float] = []
    last: dict[str, Any] | None = None
    for _ in range(rounds):
        start = time.perf_counter()
        last = fn()
        timings.append((time.perf_counter() - start) * 1000)
    assert last is not None
    return last, timings


def stats(timings: list[float]) -> dict[str, float]:
    return {
        "avg_ms": round(statistics.mean(timings), 2),
        "min_ms": round(min(timings), 2),
        "max_ms": round(max(timings), 2),
    }


def benchmark_fixtures(repo: WorkbenchRepository) -> tuple[list[str], list[tuple[str, str]], str | None]:
    records = repo.all_page_records()
    source_stems = [record["stem"] for record in records if record["section"] == "sources"]
    page_stems = [record["stem"] for record in records if record["section"] not in {"sources", "_meta"}]
    query_fixtures = list(DEFAULT_QUERY_FIXTURES)
    for record in records[:3]:
        query_fixtures.append(record["title"].lower())
    query_fixtures = list(dict.fromkeys(query_fixtures))[:4]

    inspect_fixtures: list[tuple[str, str]] = []
    if page_stems:
        inspect_fixtures.append(("page", page_stems[0]))
    if source_stems:
        inspect_fixtures.append(("source", source_stems[0]))
    source_fixture = source_stems[0] if source_stems else None
    return query_fixtures, inspect_fixtures, source_fixture


def benchmark_repo(repo: WorkbenchRepository) -> dict[str, Any]:
    summary = repo.summary()
    query_inputs, inspect_inputs, source_fixture = benchmark_fixtures(repo)
    query_results: dict[str, Any] = {}
    for query in query_inputs:
        payload, timings = time_call(lambda q=query: repo.query_preview(q, limit=5))
        canonical_hits = next(
            (section["count"] for section in payload["provenance_sections"] if section["label"] == "Canonical registries"),
            0,
        )
        query_results[query] = {
            **stats(timings),
            "coverage": payload["coverage"],
            "graph_available": bool(payload["graph_hints"]["available"]),
            "graph_seed_count": len(payload["graph_hints"]["seeds"]),
            "graph_path_hint_count": len(payload["graph_hints"]["path_hints"]),
            "canonical_registry_count": canonical_hits,
        }

    inspect_results: dict[str, Any] = {}
    for seed_type, seed in inspect_inputs:
        payload, timings = time_call(lambda st=seed_type, s=seed: repo.graph_inspect(st, s))
        inspect_results[f"{seed_type}:{seed}"] = {
            **stats(timings),
            "mode": payload["mode"],
            "node_count": payload["neighborhood"]["node_count"],
            "edge_count": payload["neighborhood"]["edge_count"],
            "path_hint_count": len(payload["path_hints"]),
        }

    review_payload, review_timings = time_call(lambda: repo.review_summary(limit=5))
    source_payload = {"coverage": {}, "review_queue": []}
    source_timings = [0.0]
    if source_fixture:
        source_payload, source_timings = time_call(lambda: repo.source_detail(source_fixture))

    return {
        "summary": summary,
        "queries": query_results,
        "inspect": inspect_results,
        "review": {
            **stats(review_timings),
            "uncertainty_candidates": len(review_payload["uncertainty_candidates"]),
            "stale_pages": len(review_payload["stale_pages"]),
            "low_confidence_claims": len(review_payload["low_confidence_claims"]),
            "contradiction_candidates": len(review_payload.get("contradiction_candidates") or []),
            "merge_candidates": len(review_payload.get("merge_candidates") or []),
        },
        "source_detail": {
            **stats(source_timings),
            **source_payload.get("coverage", {}),
            "review_queue_count": len(source_payload.get("review_queue", [])),
        },
    }


def average_section_ms(section: dict[str, Any]) -> float:
    if not section:
        return 0.0
    values = [float(item["avg_ms"]) for item in section.values() if isinstance(item, dict) and "avg_ms" in item]
    if not values:
        return 0.0
    return round(statistics.mean(values), 2)


def run_ontology_graph_benchmark(
    baseline_root: Path,
    sandbox_root: Path,
    *,
    limit_sources: int | None = None,
    reset_sandbox: bool = True,
) -> dict[str, Any]:
    baseline_root = baseline_root.resolve()
    sandbox_root = sandbox_root.resolve()
    benchmark_root = sandbox_root / "benchmark_harness"
    production_root = sandbox_root / "production"
    prepare_sandbox(baseline_root, benchmark_root, reset=reset_sandbox)
    prepare_sandbox(baseline_root, production_root, reset=reset_sandbox)

    benchmark_ingest_result = ingest_ontology_benchmark(
        benchmark_root,
        clean=True,
        limit_sources=limit_sources,
        build_graph_projection=True,
    )
    production_ingest_result = ingest_ontology(
        production_root,
        clean=True,
        limit_sources=limit_sources,
        build_graph_projection=True,
    )

    baseline_repo = WorkbenchRepository(baseline_root)
    benchmark_repo_payload = WorkbenchRepository(benchmark_root)
    production_repo = WorkbenchRepository(production_root)

    baseline = benchmark_repo(baseline_repo)
    benchmark_harness = benchmark_repo(benchmark_repo_payload)
    production = benchmark_repo(production_repo)

    comparisons = {
        "query_preview": {
            "baseline": average_section_ms(baseline["queries"]),
            "benchmark_harness": average_section_ms(benchmark_harness["queries"]),
            "production": average_section_ms(production["queries"]),
        },
        "graph_inspect": {
            "baseline": average_section_ms(baseline["inspect"]),
            "benchmark_harness": average_section_ms(benchmark_harness["inspect"]),
            "production": average_section_ms(production["inspect"]),
        },
        "review_summary": {
            "baseline": baseline["review"]["avg_ms"],
            "benchmark_harness": benchmark_harness["review"]["avg_ms"],
            "production": production["review"]["avg_ms"],
        },
        "source_detail": {
            "baseline": baseline["source_detail"].get("avg_ms", 0.0),
            "benchmark_harness": benchmark_harness["source_detail"].get("avg_ms", 0.0),
            "production": production["source_detail"].get("avg_ms", 0.0),
        },
    }

    result = {
        "baseline_root": str(baseline_root),
        "sandbox_root": str(sandbox_root),
        "benchmark_root": str(benchmark_root),
        "production_root": str(production_root),
        "benchmark_ingest_result": benchmark_ingest_result,
        "production_ingest_result": production_ingest_result,
        "baseline": baseline,
        "benchmark_harness": benchmark_harness,
        "production": production,
        "comparisons": comparisons,
    }
    artifact_dir = sandbox_root / "benchmark_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "ontology_graph_benchmark_results.json"
    artifact_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["artifact_path"] = str(artifact_path)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run baseline-vs-benchmark-vs-production benchmark for DocTology.")
    parser.add_argument("--baseline-root", default=str(REPO_ROOT), help="Baseline DocTology repo root.")
    parser.add_argument("--sandbox-root", default=str(DEFAULT_SANDBOX), help="Sandbox root for benchmark runs.")
    parser.add_argument("--limit-sources", type=int, default=None, help="Optional source cap for quick runs.")
    parser.add_argument("--no-reset-sandbox", action="store_true", help="Do not recreate the sandbox before running.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_ontology_graph_benchmark(
        Path(args.baseline_root).resolve(),
        Path(args.sandbox_root).resolve(),
        limit_sources=args.limit_sources,
        reset_sandbox=not args.no_reset_sandbox,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
