from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.workbench.repository import WorkbenchRepository
from scripts.workbench.server import route_request


class WorkbenchGraphInspectTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="doctology-graph-inspect-"))
        (root / "raw" / "inbox").mkdir(parents=True)
        (root / "wiki" / "concepts").mkdir(parents=True)
        (root / "wiki" / "sources").mkdir(parents=True)
        (root / "warehouse" / "jsonl").mkdir(parents=True)
        (root / "warehouse" / "graph_projection").mkdir(parents=True)
        (root / "wiki" / "_meta").mkdir(parents=True)

        (root / "wiki" / "concepts" / "graph-memory.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Graph Memory
                type: concept
                status: active
                ---

                # Graph Memory

                Links to [[source-alpha]].
                """
            ),
            encoding="utf-8",
        )
        (root / "wiki" / "sources" / "source-alpha.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Source Alpha
                type: source
                status: active
                ---

                # Source Alpha

                Example source body.
                """
            ),
            encoding="utf-8",
        )
        (root / "wiki" / "concepts" / "future-page.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Orphan Ledger
                type: concept
                status: active
                ---

                # Orphan Ledger

                Orphan ledger remains detached from all current projections.
                """
            ),
            encoding="utf-8",
        )
        (root / "warehouse" / "jsonl" / "claims.jsonl").write_text(
            '{"claim_id":"claim:graph-memory-supports-operators","claim_text":"Graph memory supports operators","subject_id":"entity:graph-memory"}\n',
            encoding="utf-8",
        )
        (root / "warehouse" / "graph_projection" / "nodes.jsonl").write_text(
            "\n".join(
                [
                    '{"id":"entity:graph-memory","label":"Graph Memory","kind":"entity"}',
                    '{"id":"source:source-alpha","label":"Source Alpha","kind":"source"}',
                    '{"id":"claim:graph-memory-supports-operators","label":"Graph memory supports operators","kind":"claim"}',
                    '{"id":"entity:operators","label":"Operators","kind":"entity"}',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "warehouse" / "graph_projection" / "edges.jsonl").write_text(
            "\n".join(
                [
                    '{"source":"entity:graph-memory","target":"claim:graph-memory-supports-operators","label":"supports"}',
                    '{"source":"claim:graph-memory-supports-operators","target":"entity:operators","label":"about"}',
                    '{"source":"source:source-alpha","target":"claim:graph-memory-supports-operators","label":"documents"}',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return root

    def test_graph_inspect_route_returns_bounded_neighborhood_for_page_seed(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)

        status, payload = route_request(
            repo,
            "GET",
            "/api/graph/inspect?seed_type=page&seed=graph-memory",
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["mode"], "available")
        self.assertEqual(payload["seed"]["type"], "page")
        self.assertEqual(payload["seed"]["value"], "graph-memory")
        self.assertGreaterEqual(payload["neighborhood"]["node_count"], 2)
        self.assertGreaterEqual(payload["neighborhood"]["edge_count"], 1)
        self.assertTrue(payload["path_hints"])

    def test_graph_inspect_route_reports_unavailable_when_projection_is_missing(self) -> None:
        repo_root = self.make_repo()
        (repo_root / "warehouse" / "graph_projection" / "nodes.jsonl").unlink()
        (repo_root / "warehouse" / "graph_projection" / "edges.jsonl").unlink()
        repo = WorkbenchRepository(repo_root)

        status, payload = route_request(
            repo,
            "GET",
            "/api/graph/inspect?seed_type=source&seed=source-alpha",
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["mode"], "unavailable")
        self.assertIn("graph projection", payload["summary"].lower())


    def test_query_preview_includes_graph_hints_when_projection_is_available(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)

        payload = repo.query_preview("graph memory operators", limit=5)

        self.assertEqual(payload["coverage"], "supported")
        self.assertIn("graph_hints", payload)
        self.assertTrue(payload["graph_hints"]["available"])
        self.assertTrue(payload["graph_hints"]["related_nodes"])
        self.assertTrue(payload["graph_hints"]["path_hints"])
        self.assertEqual(payload["contract"]["route"], "repo_local_search")
        self.assertEqual(payload["contract"]["save_readiness"], "ready")
        self.assertIsNone(payload["contract"]["fallback_reason"])
        self.assertTrue(any(layer["name"] == "canonical_jsonl" and layer["used"] for layer in payload["contract"]["truth_layers"]))

    def test_query_preview_empty_query_returns_tokens_and_hides_graph_hints(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)

        payload = repo.query_preview("", limit=5)

        self.assertEqual(payload["tokens"], [])
        self.assertNotIn("## Graph hints", payload["answer_markdown"])
        self.assertEqual(payload["contract"]["fallback_reason"], "empty_query")
        self.assertEqual(payload["contract"]["save_readiness"], "blocked")

    def test_query_preview_renders_seed_only_graph_hints_when_neighborhood_is_empty(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)

        payload = repo.query_preview("orphan ledger", limit=5)

        self.assertFalse(payload["graph_hints"]["available"])
        self.assertTrue(payload["graph_hints"]["seeds"])
        self.assertIn("## Graph hints", payload["answer_markdown"])
        self.assertEqual(payload["contract"]["save_readiness"], "review_required")
        self.assertEqual(payload["contract"]["fallback_reason"], "thin_coverage")

    def test_query_preview_reports_blocked_save_when_no_direct_matches_exist(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)

        payload = repo.query_preview("topic that does not exist here", limit=5)

        self.assertEqual(payload["coverage"], "none")
        self.assertEqual(payload["contract"]["fallback_reason"], "no_direct_matches")
        self.assertEqual(payload["contract"]["save_readiness"], "blocked")

    def test_query_preview_handles_malformed_graph_projection_without_crashing(self) -> None:
        repo_root = self.make_repo()
        (repo_root / "warehouse" / "graph_projection" / "nodes.jsonl").write_text("{not-json}\n", encoding="utf-8")
        repo = WorkbenchRepository(repo_root)

        payload = repo.query_preview("graph memory operators", limit=5)

        self.assertFalse(payload["graph_hints"]["available"])
        self.assertEqual(payload["graph_hints"]["warnings"], ["graph_projection_invalid"])
        self.assertNotIn("## Graph hints", payload["answer_markdown"])

    def test_review_summary_enriches_items_with_graph_hints(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)

        payload = repo.review_summary(limit=5)

        low_coverage = payload["low_coverage_pages"]
        self.assertTrue(low_coverage)
        self.assertIn("graph_hint", low_coverage[0])
        self.assertTrue(low_coverage[0]["graph_hint"])

    def test_review_summary_only_enriches_returned_items(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)
        calls: list[tuple[str, str]] = []

        def fake_graph_hint(seed_type: str, seed: str) -> str | None:
            calls.append((seed_type, seed))
            return f"{seed_type}:{seed}"

        repo._graph_hint_text = fake_graph_hint  # type: ignore[method-assign]
        payload = repo.review_summary(limit=1)

        returned_count = (
            len(payload["low_coverage_pages"])
            + len(payload["uncertainty_candidates"])
            + len(payload["stale_pages"])
            + len(payload["low_confidence_claims"])
        )
        self.assertLessEqual(len(calls), returned_count)

    def test_save_query_analysis_persists_graph_context_section(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)

        payload = repo.save_query_analysis("graph memory operators", limit=5)
        analysis_path = repo_root / payload["analysis_path"]
        analysis_text = analysis_path.read_text(encoding="utf-8")

        self.assertIn("## Query contract", analysis_text)
        self.assertIn("- Route: `repo_local_search`", analysis_text)
        self.assertIn("## Graph context", analysis_text)
        self.assertIn("Graph hints", analysis_text)
        self.assertIn("Graph seeds", analysis_text)
        self.assertNotIn("### Graph paths", analysis_text)

    def test_save_query_analysis_persists_seed_only_graph_context(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)

        payload = repo.save_query_analysis("orphan ledger", limit=5)
        analysis_path = repo_root / payload["analysis_path"]
        analysis_text = analysis_path.read_text(encoding="utf-8")

        self.assertIn("## Graph hints", payload["preview"]["answer_markdown"])
        self.assertIn("## Graph context", analysis_text)
        self.assertIn("### Graph seeds", analysis_text)

    def test_save_query_analysis_skips_graph_context_when_preview_did_not_render_it(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)

        payload = repo.save_query_analysis("topic that does not exist here", limit=5)
        analysis_path = repo_root / payload["analysis_path"]
        analysis_text = analysis_path.read_text(encoding="utf-8")

        self.assertNotIn("## Graph hints", payload["preview"]["answer_markdown"])
        self.assertNotIn("## Graph context", analysis_text)

    def test_save_query_analysis_skips_graph_context_for_empty_query_preview(self) -> None:
        repo_root = self.make_repo()
        repo = WorkbenchRepository(repo_root)

        payload = repo.save_query_analysis("", limit=5)
        analysis_path = repo_root / payload["analysis_path"]
        analysis_text = analysis_path.read_text(encoding="utf-8")

        self.assertNotIn("## Graph hints", payload["preview"]["answer_markdown"])
        self.assertNotIn("## Graph context", analysis_text)


if __name__ == "__main__":
    unittest.main()
