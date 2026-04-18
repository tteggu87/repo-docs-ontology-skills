from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.build_graph_projection_from_jsonl import build_graph_projection_from_jsonl
from scripts.ontology_benchmark_ingest import REPO_ROOT, ingest_ontology_benchmark
from scripts.incremental_support import read_jsonl
from scripts.workbench.repository import WorkbenchRepository


class OntologyBenchmarkIngestTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="doctology-ontology-benchmark-"))
        (root / "raw" / "processed").mkdir(parents=True)
        (root / "wiki" / "sources").mkdir(parents=True)
        (root / "wiki" / "concepts").mkdir(parents=True)
        (root / "wiki" / "projects").mkdir(parents=True)
        (root / "wiki" / "_meta").mkdir(parents=True)
        (root / "warehouse" / "jsonl").mkdir(parents=True)
        (root / "warehouse" / "graph_projection").mkdir(parents=True)

        (root / "wiki" / "concepts" / "graph-memory.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Graph Memory
                type: concept
                status: active
                ---

                # Graph Memory

                Graph memory refers to bounded graph context for operators.
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
                ---

                # Operators Project

                Operators project studies graph-aware operator workflows.
                """
            ),
            encoding="utf-8",
        )
        self.write_source(
            root,
            stem="source-alpha",
            title="Source Alpha",
            raw_filename="source-alpha.md",
            body=textwrap.dedent(
                """\
                # Source Alpha

                ## Summary

                - Source alpha summary for graph-aware operators.

                ## Key Facts

                - Alpha documents local graph memory usage.
                - tiny

                ## Important Claims

                - Source alpha claims bounded graph context.
                - Graph memory supports operators in the local workflow.

                ## Notes

                Alpha paragraph explains how [[graph-memory]] supports [[operators-project]].
                The same paragraph references [[graph-memory]] again for dedupe testing.
                """
            ),
        )
        return root

    def write_source(self, root: Path, *, stem: str, title: str, raw_filename: str, body: str) -> None:
        raw_path = root / "raw" / "processed" / raw_filename
        raw_path.write_text(f"Raw body for {title}.\n", encoding="utf-8")
        content = "\n".join(
            [
                "---",
                f"title: {title}",
                "type: source",
                "status: active",
                f"raw_path: raw/processed/{raw_filename}",
                "---",
                "",
                body.strip(),
                "",
            ]
        )
        (root / "wiki" / "sources" / f"{stem}.md").write_text(content, encoding="utf-8")

    def test_ingest_generates_documents_and_source_versions_for_source_pages(self) -> None:
        repo_root = self.make_repo()

        result = ingest_ontology_benchmark(repo_root)

        self.assertEqual(result["document_count"], 1)
        self.assertEqual(result["source_version_count"], 1)

        documents = read_jsonl(repo_root / "warehouse" / "jsonl" / "documents.jsonl")
        source_versions = read_jsonl(repo_root / "warehouse" / "jsonl" / "source_versions.jsonl")

        self.assertEqual(len(documents), 1)
        self.assertEqual(len(source_versions), 1)
        self.assertEqual(documents[0]["title"], "Source Alpha")
        self.assertEqual(documents[0]["raw_path"], "raw/processed/source-alpha.md")
        self.assertEqual(documents[0]["source_page"], "source-alpha")
        self.assertEqual(source_versions[0]["document_id"], documents[0]["document_id"])
        self.assertEqual(source_versions[0]["raw_path"], "raw/processed/source-alpha.md")

    def test_ingest_is_stable_on_rerun_without_duplicate_documents(self) -> None:
        repo_root = self.make_repo()

        first = ingest_ontology_benchmark(repo_root)
        first_documents_text = (repo_root / "warehouse" / "jsonl" / "documents.jsonl").read_text(encoding="utf-8")
        first_versions_text = (repo_root / "warehouse" / "jsonl" / "source_versions.jsonl").read_text(encoding="utf-8")
        second = ingest_ontology_benchmark(repo_root)

        documents = read_jsonl(repo_root / "warehouse" / "jsonl" / "documents.jsonl")
        source_versions = read_jsonl(repo_root / "warehouse" / "jsonl" / "source_versions.jsonl")

        self.assertEqual(first["document_count"], 1)
        self.assertEqual(second["document_count"], 1)
        self.assertEqual(len(documents), 1)
        self.assertEqual(len(source_versions), 1)
        self.assertEqual(documents[0]["document_id"], source_versions[0]["document_id"])
        self.assertEqual(first_documents_text, (repo_root / "warehouse" / "jsonl" / "documents.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(first_versions_text, (repo_root / "warehouse" / "jsonl" / "source_versions.jsonl").read_text(encoding="utf-8"))

    def test_ingest_serializes_yaml_dates_as_iso_strings(self) -> None:
        repo_root = self.make_repo()
        (repo_root / "wiki" / "sources" / "source-alpha.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Source Alpha
                type: source
                status: active
                created: 2026-04-18
                updated: 2026-04-18
                raw_path: raw/processed/source-alpha.md
                ---

                # Source Alpha

                ## Summary

                - Source alpha summary.
                """
            ),
            encoding="utf-8",
        )

        ingest_ontology_benchmark(repo_root)
        documents = read_jsonl(repo_root / "warehouse" / "jsonl" / "documents.jsonl")

        self.assertEqual(documents[0]["ingested_at"], "2026-04-18")

    def test_ingest_updates_export_version_when_source_page_metadata_changes(self) -> None:
        repo_root = self.make_repo()

        ingest_ontology_benchmark(repo_root)
        first_versions = read_jsonl(repo_root / "warehouse" / "jsonl" / "source_versions.jsonl")
        first_export_version_id = first_versions[0]["export_version_id"]

        (repo_root / "wiki" / "sources" / "source-alpha.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Source Alpha Retitled
                type: source
                status: active
                raw_path: raw/processed/source-alpha.md
                ---

                # Source Alpha Retitled

                ## Summary

                - Source alpha summary.
                """
            ),
            encoding="utf-8",
        )

        ingest_ontology_benchmark(repo_root)
        second_versions = read_jsonl(repo_root / "warehouse" / "jsonl" / "source_versions.jsonl")

        self.assertNotEqual(first_export_version_id, second_versions[0]["export_version_id"])

    def test_ingest_refuses_main_repo_root_without_explicit_override(self) -> None:
        with self.assertRaises(ValueError):
            ingest_ontology_benchmark(REPO_ROOT)

    def test_ingest_generates_segments_from_bullets_and_paragraphs(self) -> None:
        repo_root = self.make_repo()

        ingest_ontology_benchmark(repo_root)
        segments = read_jsonl(repo_root / "warehouse" / "jsonl" / "segments.jsonl")

        self.assertTrue(segments)
        texts = [row["text"] for row in segments]
        self.assertIn("Source alpha summary for graph-aware operators.", texts)
        self.assertIn("Source alpha claims bounded graph context.", texts)
        self.assertIn(
            "Alpha paragraph explains how [[graph-memory]] supports [[operators-project]]. The same paragraph references [[graph-memory]] again for dedupe testing.",
            texts,
        )
        self.assertNotIn("tiny", texts)
        self.assertTrue(all(not text.startswith("##") for text in texts))
        self.assertEqual(segments[0]["segment_id"], "segment:source-alpha:1")

    def test_ingest_generates_entities_for_source_pages_and_wikilinks_deduped(self) -> None:
        repo_root = self.make_repo()
        self.write_source(
            repo_root,
            stem="source-beta",
            title="Source Beta",
            raw_filename="source-beta.md",
            body=textwrap.dedent(
                """\
                # Source Beta

                ## Summary

                - Beta summary references [[graph-memory]].
                """
            ),
        )

        ingest_ontology_benchmark(repo_root)
        entities = read_jsonl(repo_root / "warehouse" / "jsonl" / "entities.jsonl")
        labels = {row["label"] for row in entities}
        graph_memory_rows = [row for row in entities if row["entity_id"] == "entity:graph-memory"]

        self.assertIn("Source Alpha", labels)
        self.assertIn("Graph Memory", labels)
        self.assertIn("Operators Project", labels)
        self.assertEqual(len(graph_memory_rows), 1)
        self.assertEqual(sorted(graph_memory_rows[0]["source_document_ids"]), ["document:source-alpha", "document:source-beta"])

    def test_ingest_generates_claims_and_evidence_with_needs_review(self) -> None:
        repo_root = self.make_repo()

        ingest_ontology_benchmark(repo_root)
        claims = read_jsonl(repo_root / "warehouse" / "jsonl" / "claims.jsonl")
        evidence = read_jsonl(repo_root / "warehouse" / "jsonl" / "claim_evidence.jsonl")

        self.assertGreaterEqual(len(claims), 2)
        self.assertEqual(len(claims), len(evidence))
        self.assertTrue(all(row["review_state"] == "needs_review" for row in claims))
        self.assertTrue(all(isinstance(row["confidence"], float) for row in claims))
        self.assertTrue(all(item["segment_id"] for item in evidence))

    def test_ingest_generates_derived_edges_for_documents_claims_and_entities(self) -> None:
        repo_root = self.make_repo()

        ingest_ontology_benchmark(repo_root)
        edges = read_jsonl(repo_root / "warehouse" / "jsonl" / "derived_edges.jsonl")

        edge_tuples = {(row["source"], row["target"], row["label"]) for row in edges}
        claims = read_jsonl(repo_root / "warehouse" / "jsonl" / "claims.jsonl")
        first_claim = claims[0]["claim_id"]

        self.assertIn(("document:source-alpha", first_claim, "documents"), edge_tuples)
        self.assertIn((first_claim, "entity:source-alpha", "about_subject"), edge_tuples)
        self.assertTrue(any(label == "about_object" for _, _, label in edge_tuples))
        self.assertIn(("entity:source-alpha", "entity:graph-memory", "related_to"), edge_tuples)

    def test_projection_builder_creates_nodes_and_edges_from_canonical_jsonl(self) -> None:
        repo_root = self.make_repo()

        ingest_ontology_benchmark(repo_root)
        result = build_graph_projection_from_jsonl(repo_root)
        nodes = read_jsonl(repo_root / "warehouse" / "graph_projection" / "nodes.jsonl")
        edges = read_jsonl(repo_root / "warehouse" / "graph_projection" / "edges.jsonl")

        self.assertGreater(result["node_count"], 0)
        self.assertGreater(result["edge_count"], 0)
        node_ids = {row["id"] for row in nodes}
        self.assertIn("document:source-alpha", node_ids)
        self.assertIn("entity:graph-memory", node_ids)
        self.assertTrue(any(row["id"].startswith("claim:source-alpha:") for row in nodes))
        self.assertTrue(any(edge["label"] == "documents" for edge in edges))

    def test_ingest_with_projection_build_supports_workbench_consumers(self) -> None:
        repo_root = self.make_repo()

        result = ingest_ontology_benchmark(repo_root, build_graph_projection=True)
        repo = WorkbenchRepository(repo_root)
        source_payload = repo.source_detail("source-alpha")
        preview_payload = repo.query_preview("graph memory operators", limit=5)
        inspect_payload = repo.graph_inspect("source", "source-alpha")

        self.assertGreater(result["segment_count"], 0)
        self.assertGreater(result["entity_count"], 0)
        self.assertGreater(result["claim_count"], 0)
        self.assertGreater(result["derived_edge_count"], 0)
        self.assertEqual(source_payload["coverage"]["document_count"], 1)
        self.assertGreater(source_payload["coverage"]["entity_count"], 0)
        self.assertGreater(source_payload["coverage"]["claim_count"], 0)
        self.assertGreater(source_payload["coverage"]["segment_count"], 0)
        self.assertTrue(source_payload["review_queue"])
        self.assertGreater(next(section["count"] for section in preview_payload["provenance_sections"] if section["label"] == "Canonical registries"), 0)
        self.assertEqual(inspect_payload["mode"], "available")


if __name__ == "__main__":
    unittest.main()
