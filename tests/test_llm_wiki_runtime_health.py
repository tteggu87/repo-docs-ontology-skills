from __future__ import annotations

import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import llm_wiki
from scripts.workbench.common import summarize_action_output


class LlmWikiRuntimeHealthTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="doctology-runtime-health-"))
        (root / "raw" / "processed").mkdir(parents=True)
        (root / "raw" / "processed" / "alpha.md").write_text("alpha raw", encoding="utf-8")
        (root / "raw" / "notes").mkdir(parents=True)
        (root / "raw" / "notes" / "note.txt").write_text("note", encoding="utf-8")
        (root / "wiki" / "_meta").mkdir(parents=True)
        (root / "wiki" / "sources").mkdir(parents=True)
        (root / "warehouse" / "jsonl").mkdir(parents=True)
        (root / "warehouse" / "graph_projection").mkdir(parents=True)
        (root / "wiki" / "_meta" / "index.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Index
                type: meta
                status: active
                created: 2026-04-19
                updated: 2026-04-19
                ---

                # Index

                ## Sources

                - [[source-alpha]] - alpha
                - [[source-beta]] - beta
                """
            ),
            encoding="utf-8",
        )
        (root / "wiki" / "_meta" / "log.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Log
                type: meta
                status: active
                created: 2026-04-19
                updated: 2026-04-19
                ---

                # Log

                ## [2026-04-19] setup | Initialized

                - Created the repo.
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
                raw_path: raw/processed/alpha.md
                ---

                # Source Alpha
                """
            ),
            encoding="utf-8",
        )
        (root / "wiki" / "sources" / "source-beta.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Source Beta
                type: source
                status: active
                raw_path: raw/processed/alpha.md
                ---

                # Source Beta
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
        (root / "warehouse" / "graph_projection" / "nodes.jsonl").write_text(
            '{"id":"source:source-alpha","label":"Source Alpha","kind":"source"}\n', encoding="utf-8"
        )
        (root / "warehouse" / "graph_projection" / "edges.jsonl").write_text(
            '{"source":"source:source-alpha","target":"source:source-alpha","label":"self"}\n', encoding="utf-8"
        )
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True)
        (root / ".codex" / "context").mkdir(parents=True)
        (root / ".codex" / "context" / "note.md").write_text("context", encoding="utf-8")
        (root / "wiki" / "state").mkdir(parents=True)
        (root / "wiki" / "state" / "wiki_index.sqlite").write_text("placeholder", encoding="utf-8")
        subprocess.run(["git", "status", "--short"], cwd=root, check=True, capture_output=True)
        return root

    def test_build_doctor_payload_reports_source_page_and_registry_health(self) -> None:
        repo_root = self.make_repo()

        payload = llm_wiki.build_doctor_payload(repo_root)

        self.assertEqual(payload["raw_counts"]["total"], 2)
        self.assertEqual(payload["wiki_health"]["source_page_count"], 2)
        self.assertEqual(payload["source_page_health"]["missing_raw_path_count"], 0)
        self.assertEqual(len(payload["source_page_health"]["duplicate_raw_path_owners"]), 1)
        self.assertTrue(payload["graph_projection"]["available"])
        self.assertFalse(payload["docs_readiness"]["current_state_exists"])

    def test_build_doctor_payload_ignores_superseded_source_pages_without_raw_path(self) -> None:
        repo_root = self.make_repo()
        (repo_root / "wiki" / "sources" / "source-legacy.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: Source Legacy
                type: source
                status: superseded
                ---

                # Source Legacy
                """
            ),
            encoding="utf-8",
        )

        payload = llm_wiki.build_doctor_payload(repo_root)

        self.assertEqual(payload["wiki_health"]["source_page_count"], 3)
        self.assertEqual(payload["source_page_health"]["missing_raw_path_count"], 0)
        self.assertEqual(payload["source_page_health"]["missing_raw_path_pages"], [])

    def test_classify_working_tree_entries_groups_agent_runtime_and_live_workspace_paths(self) -> None:
        payload = llm_wiki.classify_working_tree_entries(
            [
                "?? .codex/context/note.md",
                "?? wiki/state/wiki_index.sqlite",
                "?? raw/processed/alpha.md",
                "?? docs/CURRENT_STATE.md",
            ]
        )

        self.assertEqual(payload["counts"]["agent_local"], 1)
        self.assertEqual(payload["counts"]["runtime_state"], 1)
        self.assertEqual(payload["counts"]["live_workspace"], 1)
        self.assertEqual(payload["counts"]["durable_repo_change"], 1)

    def test_summarize_action_output_parses_doctor_json(self) -> None:
        summary = summarize_action_output(
            "doctor",
            [json.dumps({"kind": "doctor", "docs_readiness": {"current_state_exists": True}})],
        )

        self.assertEqual(summary["kind"], "doctor")
        self.assertTrue(summary["docs_readiness"]["current_state_exists"])

    def test_doctor_cli_json_outputs_machine_readable_payload_for_real_repo(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["python3", "scripts/llm_wiki.py", "doctor", "--json"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("raw_counts", payload)
        self.assertIn("working_tree", payload)
        self.assertIn("docs_readiness", payload)


if __name__ == "__main__":
    unittest.main()
