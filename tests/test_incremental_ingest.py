from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from incremental_ingest import ingest_incremental
from incremental_support import read_jsonl
from llm_wiki import rebuild_index


class IncrementalIngestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "intelligence" / "manifests").mkdir(parents=True, exist_ok=True)
        (self.root / "warehouse" / "jsonl").mkdir(parents=True, exist_ok=True)
        (self.root / "raw" / "inbox").mkdir(parents=True, exist_ok=True)
        shutil.copy(
            PROJECT_ROOT / "intelligence" / "manifests" / "source_families.yaml",
            self.root / "intelligence" / "manifests" / "source_families.yaml",
        )

        fixture_dir = PROJECT_ROOT / "tests" / "fixtures" / "incremental_ingest"
        for name in ["KakaoTalk_Chat_에이전트코리아_A.csv", "KakaoTalk_Chat_에이전트코리아_AB.csv", "unknown.csv"]:
            shutil.copy(fixture_dir / name, self.root / "raw" / "inbox" / name)
        (self.root / "raw" / "inbox" / "note-export-sample.md").write_text(
            "# Sample Note Export\n\nThis note mentions ontology builders and review loops.\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_identical_rerun_is_idempotent(self) -> None:
        source = self.root / "raw" / "inbox" / "KakaoTalk_Chat_에이전트코리아_A.csv"
        first = ingest_incremental(str(source), str(self.root))
        second = ingest_incremental(str(source), str(self.root))

        self.assertEqual(first["new_message_count"], 2)
        self.assertEqual(second["new_message_count"], 0)
        self.assertEqual(second["unchanged_message_count"], 2)
        self.assertEqual(len(read_jsonl(self.root / "warehouse" / "jsonl" / "messages.jsonl")), 2)

    def test_cumulative_export_adds_only_new_tail(self) -> None:
        source_a = self.root / "raw" / "inbox" / "KakaoTalk_Chat_에이전트코리아_A.csv"
        source_ab = self.root / "raw" / "inbox" / "KakaoTalk_Chat_에이전트코리아_AB.csv"

        first = ingest_incremental(str(source_a), str(self.root))
        second = ingest_incremental(str(source_ab), str(self.root))

        messages = read_jsonl(self.root / "warehouse" / "jsonl" / "messages.jsonl")
        source_versions = read_jsonl(self.root / "warehouse" / "jsonl" / "source_versions.jsonl")

        self.assertEqual(second["new_message_count"], 1)
        self.assertEqual(second["unchanged_message_count"], 2)
        self.assertEqual(len(messages), 3)
        self.assertEqual(len(source_versions), 2)
        self.assertIsNone(first["supersedes_export_version_id"])
        self.assertEqual(second["supersedes_export_version_id"], first["export_version_id"])
        self.assertIn("warehouse/jsonl/documents.jsonl", second["affected_registry_paths"])
        self.assertIn("wiki/_meta/log.md", second["affected_wiki_paths"])
        latest_version = next(row for row in source_versions if row["export_version_id"] == second["export_version_id"])
        self.assertIn("warehouse/jsonl/messages.jsonl", latest_version["affected_registry_paths"])
        self.assertIn("wiki/sources/source-kakao-agent-korea-chat-incremental-status.md", latest_version["affected_wiki_paths"])

        status_page = self.root / "wiki" / "sources" / "source-kakao-agent-korea-chat-incremental-status.md"
        self.assertTrue(status_page.exists())
        content = status_page.read_text(encoding="utf-8")
        self.assertIn("New messages in this export: `1`", content)
        self.assertIn("Unchanged messages in this export: `2`", content)
        self.assertIn("Supersedes export version:", content)
        self.assertIn("### Canonical registries", content)
        self.assertIn("### Wiki surfaces", content)

    def test_dedicated_status_page_does_not_overwrite_curated_source_page(self) -> None:
        source = self.root / "raw" / "inbox" / "KakaoTalk_Chat_에이전트코리아_A.csv"
        curated_page = self.root / "wiki" / "sources" / "source-kakao-agent-korea-chat.md"
        curated_page.parent.mkdir(parents=True, exist_ok=True)
        curated_page.write_text("# Curated Source Page\n\nKeep this content.\n", encoding="utf-8")

        ingest_incremental(str(source), str(self.root))

        self.assertEqual(curated_page.read_text(encoding="utf-8"), "# Curated Source Page\n\nKeep this content.\n")
        status_page = self.root / "wiki" / "sources" / "source-kakao-agent-korea-chat-incremental-status.md"
        self.assertTrue(status_page.exists())

    def test_duplicate_same_second_messages_are_preserved(self) -> None:
        source = self.root / "raw" / "inbox" / "KakaoTalk_Chat_에이전트코리아_DUP.csv"
        source.write_text(
            "Date,User,Message\n"
            "2026-04-01 10:00:00,Alpha,ㅋㅋ\n"
            "2026-04-01 10:00:00,Alpha,ㅋㅋ\n",
            encoding="utf-8",
        )

        first = ingest_incremental(str(source), str(self.root))
        second = ingest_incremental(str(source), str(self.root))
        messages = read_jsonl(self.root / "warehouse" / "jsonl" / "messages.jsonl")

        self.assertEqual(first["new_message_count"], 2)
        self.assertEqual(second["new_message_count"], 0)
        self.assertEqual(second["unchanged_message_count"], 2)
        self.assertEqual(len(messages), 2)
        self.assertEqual(sorted(message["occurrence_index"] for message in messages), [1, 2])
        self.assertIn("wiki/sources/source-kakao-agent-korea-chat-incremental-status.md", second["affected_wiki_paths"])

    def test_unknown_family_fails_clearly(self) -> None:
        source = self.root / "raw" / "inbox" / "unknown.csv"
        with self.assertRaises(SystemExit) as ctx:
            ingest_incremental(str(source), str(self.root))
        self.assertIn("No source family mapping matched", str(ctx.exception))

    def test_reindex_preserves_existing_created_date(self) -> None:
        wiki_meta = self.root / "wiki" / "_meta"
        wiki_meta.mkdir(parents=True, exist_ok=True)
        (self.root / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
        (self.root / "wiki" / "concepts" / "concept-sample.md").write_text(
            "---\n"
            "title: Sample Concept\n"
            "type: concept\n"
            "status: active\n"
            "created: 2026-04-08\n"
            "updated: 2026-04-08\n"
            "---\n\n"
            "# Sample Concept\n\n"
            "A sample page.\n",
            encoding="utf-8",
        )
        index_path = wiki_meta / "index.md"
        index_path.write_text(
            "---\n"
            'title: "Index"\n'
            "type: meta\n"
            "status: active\n"
            "created: 2026-01-01\n"
            "updated: 2026-04-08\n"
            "---\n\n"
            "# Index\n",
            encoding="utf-8",
        )

        import llm_wiki
        previous_root = llm_wiki.ROOT
        previous_wiki_dir = llm_wiki.WIKI_DIR
        previous_meta_dir = llm_wiki.META_DIR
        previous_raw_dir = llm_wiki.RAW_DIR
        try:
            llm_wiki.ROOT = self.root
            llm_wiki.WIKI_DIR = self.root / "wiki"
            llm_wiki.META_DIR = self.root / "wiki" / "_meta"
            llm_wiki.RAW_DIR = self.root / "raw"
            rebuild_index()
        finally:
            llm_wiki.ROOT = previous_root
            llm_wiki.WIKI_DIR = previous_wiki_dir
            llm_wiki.META_DIR = previous_meta_dir
            llm_wiki.RAW_DIR = previous_raw_dir

        content = index_path.read_text(encoding="utf-8")
        self.assertIn("created: 2026-01-01", content)

    def test_markdown_note_family_ingests_as_note_document(self) -> None:
        source = self.root / "raw" / "inbox" / "note-export-sample.md"
        result = ingest_incremental(str(source), str(self.root))

        documents = read_jsonl(self.root / "warehouse" / "jsonl" / "documents.jsonl")
        messages = read_jsonl(self.root / "warehouse" / "jsonl" / "messages.jsonl")

        self.assertEqual(result["source_family_id"], "family-markdown-note-export")
        self.assertEqual(documents[0]["document_type"], "note")
        self.assertEqual(documents[0]["source_kind"], "markdown_note_export")
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["event_type"], "note")


if __name__ == "__main__":
    unittest.main()
