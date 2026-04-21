from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path


class GrowthOperatorMinimalTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="doctology-growth-minimal-"))
        for rel in [
            "raw/processed",
            "wiki/_meta",
            "wiki/sources",
            "wiki/state",
            "warehouse/jsonl",
            "warehouse/graph_projection",
            "templates",
        ]:
            (root / rel).mkdir(parents=True, exist_ok=True)

        (root / "templates" / "source_page_template.md").write_text(
            "# {{title}}\n\nraw_path: {{raw_path}}\n",
            encoding="utf-8",
        )
        (root / "wiki" / "_meta" / "index.md").write_text(
            "---\ntitle: \"Index\"\ntype: meta\nstatus: active\ncreated: 2026-04-21\nupdated: 2026-04-21\n---\n\n# Index\n",
            encoding="utf-8",
        )
        (root / "wiki" / "_meta" / "log.md").write_text(
            "---\ntitle: Log\ntype: meta\nstatus: active\ncreated: 2026-04-21\nupdated: 2026-04-21\n---\n\n# Log\n",
            encoding="utf-8",
        )
        (root / "wiki" / "sources" / "source-alpha.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Source Alpha
                type: source
                status: active
                created: 2026-04-21
                updated: 2026-04-21
                raw_path: raw/processed/source-alpha.txt
                ---

                # Source Alpha

                ## Summary

                - Source summary only.
                """
            ),
            encoding="utf-8",
        )
        (root / "raw" / "processed" / "source-alpha.txt").write_text(
            textwrap.dedent(
                """\
                Graph Memory supports offline reasoning for operators.
                Neo4j supports graph reasoning for operators.
                """
            ),
            encoding="utf-8",
        )
        for registry in [
            "source_versions",
            "documents",
            "messages",
            "entities",
            "claims",
            "claim_evidence",
            "segments",
            "derived_edges",
        ]:
            (root / "warehouse" / "jsonl" / f"{registry}.jsonl").write_text("", encoding="utf-8")
        return root

    def test_root_llm_wiki_surface_exposes_doctor_payload(self) -> None:
        try:
            from scripts import llm_wiki
        except ModuleNotFoundError as exc:
            self.fail(f"scripts.llm_wiki is missing: {exc}")

        repo_root = self.make_repo()
        payload = llm_wiki.build_doctor_payload(repo_root)

        self.assertEqual(payload["kind"], "doctor")
        self.assertIn("operator_readiness", payload)
        self.assertIn("wiki_health", payload)

    def test_production_ingest_populates_canonical_rows_and_shadow_preview(self) -> None:
        try:
            from scripts.ontology_ingest import ingest_ontology
        except ModuleNotFoundError as exc:
            self.fail(f"scripts.ontology_ingest is missing: {exc}")

        repo_root = self.make_repo()
        result = ingest_ontology(repo_root, clean=True, build_graph_projection=True, wiki_reconcile_mode="shadow")

        claims = [
            json.loads(line)
            for line in (repo_root / "warehouse" / "jsonl" / "claims.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertGreater(result["claim_count"], 0)
        self.assertTrue(any("Graph Memory supports offline reasoning for operators." == row["claim_text"] for row in claims))
        self.assertTrue((repo_root / "warehouse" / "graph_projection" / "nodes.jsonl").exists())
        self.assertTrue((repo_root / "wiki" / "state" / "ontology_reconcile_preview.json").exists())

    def test_repo_root_includes_source_page_template_for_ingest_registration(self) -> None:
        template_path = Path(__file__).resolve().parents[1] / "templates" / "source_page_template.md"

        self.assertTrue(template_path.exists(), msg=f"missing template: {template_path}")
        content = template_path.read_text(encoding="utf-8")
        self.assertIn("{{title}}", content)
        self.assertIn("{{raw_path}}", content)


if __name__ == "__main__":
    unittest.main()
