from __future__ import annotations

import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.build_graph_projection_from_jsonl import build_graph_projection_from_jsonl
from scripts.incremental_support import read_jsonl
from scripts.run_ontology_graph_benchmark import run_ontology_graph_benchmark
from scripts.workbench.repository import WorkbenchRepository

try:
    from scripts.ontology_ingest import ingest_ontology
except ModuleNotFoundError:  # expected in RED phase before implementation
    ingest_ontology = None  # type: ignore[assignment]


class ProductionOntologyIngestTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="doctology-ontology-production-"))
        for rel in [
            "raw/processed",
            "wiki/sources",
            "wiki/concepts",
            "wiki/projects",
            "wiki/_meta",
            "wiki/state",
            "warehouse/jsonl",
            "warehouse/graph_projection",
            "templates",
            "scripts",
        ]:
            (root / rel).mkdir(parents=True, exist_ok=True)

        (root / "templates" / "source_page_template.md").write_text(
            "# {{title}}\n\nraw_path: {{raw_path}}\n",
            encoding="utf-8",
        )
        real_repo_root = Path(__file__).resolve().parent.parent
        (root / "scripts" / "llm_wiki.py").write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import runpy
                import sys
                from pathlib import Path

                REAL_ROOT = Path({str(Path('/Users/hoyasung007hotmail.com/Documents/my_project/DocTology')).__repr__()})
                sys.path.insert(0, str(REAL_ROOT))
                runpy.run_path(str(REAL_ROOT / 'scripts' / 'llm_wiki.py'), run_name='__main__')
                """
            ),
            encoding="utf-8",
        )
        (root / "wiki" / "_meta" / "index.md").write_text(
            "---\ntitle: \"Index\"\ntype: meta\nstatus: active\ncreated: 2026-04-18\nupdated: 2026-04-18\n---\n\n# Index\n",
            encoding="utf-8",
        )
        (root / "wiki" / "_meta" / "log.md").write_text(
            "---\ntitle: Log\ntype: meta\nstatus: active\ncreated: 2026-04-18\nupdated: 2026-04-18\n---\n\n# Log\n",
            encoding="utf-8",
        )
        (root / "wiki" / "concepts" / "graph-memory.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Graph Memory
                type: concept
                status: active
                created: 2026-04-18
                updated: 2026-04-18
                ---

                # Graph Memory

                Graph Memory is a concept page.
                """
            ),
            encoding="utf-8",
        )
        (root / "wiki" / "projects" / "operators-project.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Operators Project
                type: project
                status: active
                created: 2026-04-18
                updated: 2026-04-18
                ---

                # Operators Project

                Operators Project keeps graph-aware workflows organized.
                """
            ),
            encoding="utf-8",
        )

        self.write_source_page(
            root,
            stem="source-alpha",
            title="Source Alpha",
            raw_filename="source-alpha.txt",
            body=textwrap.dedent(
                """\
                # Source Alpha

                ## Summary

                - This source page summary is intentionally misleading.

                ## Important Claims

                - SOURCE PAGE ONLY CLAIM SHOULD NOT BECOME PRODUCTION CLAIM.

                ## Notes

                Mentions [[graph-memory]] and [[operators-project]] for wiki navigation.
                """
            ),
        )
        (root / "raw" / "processed" / "source-alpha.txt").write_text(
            textwrap.dedent(
                """\
                Graph Memory supports offline reasoning for operators.
                Neo4j supports graph reasoning for operators.
                Neo 4J also appears as Neo-4j in archived operator notes.

                OpenAI says "Graph Memory is incomplete" for low-risk tasks.
                Another memo says Graph Memory does not support offline reasoning today.
                """
            ),
            encoding="utf-8",
        )

        self.write_source_page(
            root,
            stem="source-beta",
            title="Source Beta",
            raw_filename="source-beta.txt",
            body=textwrap.dedent(
                """\
                # Source Beta

                ## Summary

                - Additional source page summary.

                ## Key Facts

                - Benchmark-only note.
                """
            ),
        )
        (root / "raw" / "processed" / "source-beta.txt").write_text(
            textwrap.dedent(
                """\
                Ladybug works with Kuzu in embedded graph workflows.
                NEO4J integrates with Kuzu for enterprise routing.
                그래프 메모리(Graph Memory) helps operators keep bounded context.
                """
            ),
            encoding="utf-8",
        )
        return root

    def write_source_page(self, root: Path, *, stem: str, title: str, raw_filename: str, body: str) -> None:
        content = "\n".join(
            [
                "---",
                f"title: {title}",
                "type: source",
                "status: active",
                "created: 2026-04-18",
                "updated: 2026-04-18",
                f"raw_path: raw/processed/{raw_filename}",
                "---",
                "",
                body.strip(),
                "",
            ]
        )
        (root / "wiki" / "sources" / f"{stem}.md").write_text(content, encoding="utf-8")

    def require_production_ingest(self):
        if ingest_ontology is None:
            self.fail("scripts.ontology_ingest is not implemented yet")
        return ingest_ontology

    def test_production_ingest_uses_raw_content_not_source_page_claim_sections(self) -> None:
        repo_root = self.make_repo()

        ingest = self.require_production_ingest()
        ingest(repo_root, clean=True)
        claims = read_jsonl(repo_root / "warehouse" / "jsonl" / "claims.jsonl")
        claim_texts = [row["claim_text"] for row in claims]

        self.assertIn("Graph Memory supports offline reasoning for operators.", claim_texts)
        self.assertNotIn("SOURCE PAGE ONLY CLAIM SHOULD NOT BECOME PRODUCTION CLAIM.", claim_texts)

    def test_production_ingest_generates_messages_and_segments_with_raw_spans(self) -> None:
        repo_root = self.make_repo()

        ingest = self.require_production_ingest()
        result = ingest(repo_root, clean=True)
        messages = read_jsonl(repo_root / "warehouse" / "jsonl" / "messages.jsonl")
        segments = read_jsonl(repo_root / "warehouse" / "jsonl" / "segments.jsonl")

        self.assertGreater(result["message_count"], 0)
        self.assertTrue(messages)
        self.assertTrue(segments)
        self.assertIn("raw_sentence", messages[0]["event_type"])
        self.assertIn("char_start", segments[0])
        self.assertIn("char_end", segments[0])
        self.assertIn("paragraph_index", segments[0])
        self.assertIn("message_index", segments[0])
        self.assertGreater(segments[0]["char_end"], segments[0]["char_start"])

    def test_production_ingest_merges_alias_entities_and_aggregates_sources(self) -> None:
        repo_root = self.make_repo()

        ingest = self.require_production_ingest()
        ingest(repo_root, clean=True)
        entities = read_jsonl(repo_root / "warehouse" / "jsonl" / "entities.jsonl")
        neo4j_rows = [row for row in entities if row.get("canonical_name") == "Neo4j"]

        self.assertEqual(len(neo4j_rows), 1)
        aliases = set(neo4j_rows[0].get("aliases") or [])
        self.assertIn("Neo4j", aliases)
        self.assertIn("Neo 4J", aliases)
        self.assertIn("Neo-4j", aliases)
        self.assertIn("NEO4J", aliases)
        self.assertEqual(
            sorted(neo4j_rows[0].get("source_document_ids") or []),
            ["document:source-alpha", "document:source-beta"],
        )

    def test_production_ingest_surfaces_review_signals_and_workbench_compatibility(self) -> None:
        repo_root = self.make_repo()

        ingest = self.require_production_ingest()
        ingest(repo_root, clean=True, build_graph_projection=True)
        repo = WorkbenchRepository(repo_root)
        review_payload = repo.review_summary(limit=10)
        source_payload = repo.source_detail("source-alpha")
        preview_payload = repo.query_preview("neo4j graph memory", limit=5)
        inspect_payload = repo.graph_inspect("source", "source-alpha")

        self.assertTrue(review_payload["low_confidence_claims"])
        self.assertTrue(review_payload.get("contradiction_candidates"))
        self.assertTrue(review_payload.get("merge_candidates"))
        self.assertGreater(source_payload["coverage"]["claim_count"], 0)
        self.assertGreater(source_payload["coverage"]["segment_count"], 0)
        self.assertTrue(source_payload["review_queue"])
        self.assertGreater(
            next(section["count"] for section in preview_payload["provenance_sections"] if section["label"] == "Canonical registries"),
            0,
        )
        self.assertEqual(inspect_payload["mode"], "available")

    def test_partial_rerun_preserves_unrelated_rows_and_tracks_supersession(self) -> None:
        repo_root = self.make_repo()

        ingest = self.require_production_ingest()
        ingest(repo_root, clean=True)
        first_versions = read_jsonl(repo_root / "warehouse" / "jsonl" / "source_versions.jsonl")
        first_alpha = next(row for row in first_versions if row["document_id"] == "document:source-alpha")

        (repo_root / "raw" / "processed" / "source-alpha.txt").write_text(
            textwrap.dedent(
                """\
                Graph Memory supports offline reasoning for operators.
                Neo4j supports graph reasoning for operators.
                Neo 4J also appears as Neo-4j in archived operator notes.
                Revised note says Graph Memory now supports audited offline reasoning.
                """
            ),
            encoding="utf-8",
        )

        ingest(
            repo_root,
            raw_paths=["raw/processed/source-alpha.txt"],
            build_graph_projection=True,
        )
        documents = read_jsonl(repo_root / "warehouse" / "jsonl" / "documents.jsonl")
        source_versions = read_jsonl(repo_root / "warehouse" / "jsonl" / "source_versions.jsonl")
        latest_alpha = [row for row in source_versions if row["document_id"] == "document:source-alpha"][-1]

        self.assertEqual(len(documents), 2)
        self.assertEqual(len([row for row in documents if row["document_id"] == "document:source-beta"]), 1)
        self.assertGreaterEqual(len(source_versions), 3)
        self.assertEqual(latest_alpha["supersedes_export_version_id"], first_alpha["export_version_id"])

    def test_wiki_only_edit_does_not_create_new_production_source_version(self) -> None:
        repo_root = self.make_repo()

        ingest = self.require_production_ingest()
        ingest(repo_root, clean=True)
        first_versions = read_jsonl(repo_root / "warehouse" / "jsonl" / "source_versions.jsonl")
        first_alpha = next(row for row in first_versions if row["document_id"] == "document:source-alpha")

        (repo_root / "wiki" / "sources" / "source-alpha.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Source Alpha Retitled In Wiki Only
                type: source
                status: active
                created: 2026-04-18
                updated: 2026-04-18
                raw_path: raw/processed/source-alpha.txt
                ---

                # Source Alpha

                ## Summary

                - Wiki-only metadata edit should not create a new production source version.
                """
            ),
            encoding="utf-8",
        )
        ingest(repo_root)
        second_versions = read_jsonl(repo_root / "warehouse" / "jsonl" / "source_versions.jsonl")
        second_alpha_versions = [row for row in second_versions if row["document_id"] == "document:source-alpha"]

        self.assertEqual(len(second_alpha_versions), 1)
        self.assertEqual(second_alpha_versions[0]["export_version_id"], first_alpha["export_version_id"])

    def test_duplicate_raw_path_source_pages_fail_loudly(self) -> None:
        repo_root = self.make_repo()
        self.write_source_page(
            repo_root,
            stem="source-alpha-duplicate",
            title="Source Alpha Duplicate",
            raw_filename="source-alpha.txt",
            body="# Duplicate mapping\n",
        )

        ingest = self.require_production_ingest()
        with self.assertRaises(ValueError):
            ingest(repo_root, clean=True)

    def test_markdown_raw_preprocessing_filters_frontmatter_headers_and_urls(self) -> None:
        repo_root = self.make_repo()
        self.write_source_page(
            repo_root,
            stem="source-gamma",
            title="Source Gamma",
            raw_filename="source-gamma.md",
            body="# Source Gamma\n",
        )
        (repo_root / "raw" / "processed" / "source-gamma.md").write_text(
            textwrap.dedent(
                """\
                ---
                source_page: source-gamma
                status: immutable
                ---

                # Source Gamma

                Primary URL: https://example.com/docs

                Graph Memory remains useful for bounded operators.
                """
            ),
            encoding="utf-8",
        )

        ingest = self.require_production_ingest()
        ingest(repo_root, clean=True)
        claims = read_jsonl(repo_root / "warehouse" / "jsonl" / "claims.jsonl")
        gamma_claims = [row["claim_text"] for row in claims if row["source_page"] == "source-gamma"]

        self.assertIn("Graph Memory remains useful for bounded operators.", gamma_claims)
        self.assertTrue(all("https://" not in claim for claim in gamma_claims))
        self.assertTrue(all("---" not in claim for claim in gamma_claims))

    def test_shadow_reconcile_preview_lists_pages_without_overwriting_wiki(self) -> None:
        repo_root = self.make_repo()
        original_source_page = (repo_root / "wiki" / "sources" / "source-alpha.md").read_text(encoding="utf-8")

        ingest = self.require_production_ingest()
        result = ingest(repo_root, clean=True, wiki_reconcile_mode="shadow")
        preview_path = repo_root / result["wiki_reconcile"]["preview_path"]

        self.assertTrue(preview_path.exists())
        preview_payload = json.loads(preview_path.read_text(encoding="utf-8"))
        self.assertIn("source-alpha", preview_payload["affected_source_pages"])
        self.assertEqual((repo_root / "wiki" / "sources" / "source-alpha.md").read_text(encoding="utf-8"), original_source_page)

        process = subprocess.run(
            [
                "python3",
                "scripts/llm_wiki.py",
                "reconcile-shadow",
                "--root",
                str(repo_root),
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0)
        self.assertIn("source-alpha", process.stdout)

    def test_benchmark_runner_compares_baseline_benchmark_and_production(self) -> None:
        repo_root = self.make_repo()
        build_graph_projection_from_jsonl(repo_root)
        sandbox_root = repo_root.parent / f"{repo_root.name}-sandbox"

        result = run_ontology_graph_benchmark(repo_root, sandbox_root, reset_sandbox=True)

        self.assertIn("baseline", result)
        self.assertIn("benchmark_harness", result)
        self.assertIn("production", result)
        self.assertTrue(Path(result["artifact_path"]).exists())
        self.assertIn("query_preview", result["comparisons"])
        self.assertIn("graph_inspect", result["comparisons"])

    def test_benchmark_runner_cli_executes(self) -> None:
        repo_root = self.make_repo()
        sandbox_root = repo_root.parent / f"{repo_root.name}-cli-sandbox"
        real_repo_root = Path(__file__).resolve().parent.parent
        process = subprocess.run(
            [
                "python3",
                str(real_repo_root / "scripts" / "run_ontology_graph_benchmark.py"),
                "--baseline-root",
                str(repo_root),
                "--sandbox-root",
                str(sandbox_root),
                "--limit-sources",
                "2",
            ],
            cwd=real_repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(process.returncode, 0, process.stderr)
        payload = json.loads(process.stdout)
        self.assertIn("comparisons", payload)
        self.assertIn("production", payload)


if __name__ == "__main__":
    unittest.main()
