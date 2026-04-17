from __future__ import annotations

import importlib.util
import sqlite3
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPO_ROOT / ".agents" / "skills" / "llm-wiki-bootstrap" / "scripts" / "bootstrap_llm_wiki.py"


def run_py(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(path), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


class LlmWikiBootstrapThreeLayerTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="llmwiki-three-layer-test-"))
        run_py(BOOTSTRAP, str(temp_dir), "--profile", "wiki-plus-ontology")
        return temp_dir

    def test_bootstrap_generates_three_layer_support_files(self) -> None:
        repo = self.make_repo()

        expected_paths = [
            repo / "scripts" / "reindex_sqlite_operational.py",
            repo / "scripts" / "refresh_duckdb_analytics.py",
            repo / "scripts" / "verify_three_layer_drift.py",
            repo / "templates" / "llm-wiki-three-layer" / "sqlite_operational.schema.sql",
            repo / "templates" / "llm-wiki-three-layer" / "duckdb_analytical.schema.sql",
            repo / "warehouse" / "jsonl" / "messages.jsonl",
            repo / "warehouse" / "jsonl" / "documents.jsonl",
            repo / "warehouse" / "jsonl" / "entities.jsonl",
            repo / "warehouse" / "jsonl" / "claims.jsonl",
            repo / "warehouse" / "jsonl" / "claim_evidence.jsonl",
            repo / "warehouse" / "jsonl" / "segments.jsonl",
            repo / "warehouse" / "jsonl" / "derived_edges.jsonl",
        ]

        self.assertTrue((repo / "state").is_dir())
        for path in expected_paths:
            self.assertTrue(path.exists(), f"Missing expected path: {path}")

        readme = (repo / "README.md").read_text(encoding="utf-8")
        self.assertIn("Rebuild SQLite Or Refresh Wiki Analytics DuckDB", readme)
        self.assertNotIn("Rebuild SQLite Or Refresh DuckDB", readme)

    def test_sqlite_rebuild_parses_frontmatter_tags_sources_and_body_links_correctly(self) -> None:
        repo = self.make_repo()

        page = repo / "wiki" / "concepts" / "sample.md"
        page.write_text(
            textwrap.dedent(
                """\
                ---
                title: Sample
                type: concept
                status: active
                created: 2026-04-17
                updated: 2026-04-17
                tags:
                  - alpha
                sources:
                  - "[[source-1]]"
                ---

                # Sample

                - body-bullet
                [[other-page]]
                """
            ),
            encoding="utf-8",
        )

        sqlite_script = repo / "scripts" / "reindex_sqlite_operational.py"
        run_py(sqlite_script, "--repo-root", str(repo))

        connection = sqlite3.connect(repo / "state" / "wiki_index.sqlite")
        try:
            tags = connection.execute("SELECT tag FROM tags ORDER BY tag").fetchall()
            sources = connection.execute(
                "SELECT source_id, relation_type FROM page_sources ORDER BY source_id"
            ).fetchall()
            links = connection.execute(
                "SELECT to_link_text, status FROM page_links ORDER BY to_link_text"
            ).fetchall()
        finally:
            connection.close()

        self.assertEqual(tags, [("alpha",)])
        self.assertEqual(sources, [("source-1", "primary")])
        self.assertEqual(links, [("other-page", "unresolved")])

    def test_duckdb_refresh_and_drift_check_pass_on_fresh_scaffold(self) -> None:
        if importlib.util.find_spec("duckdb") is None:
            self.skipTest("duckdb is not installed")

        repo = self.make_repo()
        sqlite_script = repo / "scripts" / "reindex_sqlite_operational.py"
        duckdb_script = repo / "scripts" / "refresh_duckdb_analytics.py"
        drift_script = repo / "scripts" / "verify_three_layer_drift.py"

        run_py(sqlite_script, "--repo-root", str(repo))
        run_py(duckdb_script, "--repo-root", str(repo))
        result = run_py(drift_script, "--repo-root", str(repo))

        self.assertTrue((repo / "state" / "wiki_analytics.duckdb").exists())
        self.assertIn("DRIFT_OK", result.stdout)
        self.assertIn("sqlite: present", result.stdout)
        self.assertIn("duckdb: present", result.stdout)


if __name__ == "__main__":
    unittest.main()
