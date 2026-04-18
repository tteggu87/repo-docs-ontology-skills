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


if __name__ == "__main__":
    unittest.main()
