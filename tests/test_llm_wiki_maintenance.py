from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import llm_wiki


class MaintenancePlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "wiki" / "_meta").mkdir(parents=True, exist_ok=True)
        (self.root / "wiki" / "concepts").mkdir(parents=True, exist_ok=True)
        (self.root / "wiki" / "sources").mkdir(parents=True, exist_ok=True)
        (self.root / "raw" / "inbox").mkdir(parents=True, exist_ok=True)

        (self.root / "wiki" / "_meta" / "index.md").write_text(
            "---\n"
            "title: Index\n"
            "type: meta\n"
            "status: active\n"
            "created: 2026-01-01\n"
            "updated: 2026-01-01\n"
            "---\n\n"
            "# Index\n\n",
            encoding="utf-8",
        )

        self.low_coverage_page = self.root / "wiki" / "concepts" / "bounded-loop.md"
        self.low_coverage_page.write_text(
            "---\n"
            "title: Bounded Loop\n"
            "type: concept\n"
            "status: draft\n"
            "created: 2026-01-01\n"
            "updated: 2026-01-01\n"
            "---\n\n"
            "# Bounded Loop\n\n"
            "Short stub.\n",
            encoding="utf-8",
        )

        self.registered_raw = self.root / "raw" / "inbox" / "registered.md"
        self.registered_raw.write_text("# Registered\n", encoding="utf-8")
        self.unregistered_raw = self.root / "raw" / "inbox" / "unregistered.md"
        self.unregistered_raw.write_text("# Unregistered\n", encoding="utf-8")

        (self.root / "wiki" / "sources" / "source-registered.md").write_text(
            "---\n"
            "title: Registered Source\n"
            "type: source\n"
            "status: active\n"
            "created: 2026-01-01\n"
            "updated: 2026-01-01\n"
            "---\n\n"
            "- Raw file: `raw/inbox/registered.md`\n",
            encoding="utf-8",
        )

        self._previous_root = llm_wiki.ROOT
        self._previous_wiki_dir = llm_wiki.WIKI_DIR
        self._previous_meta_dir = llm_wiki.META_DIR
        self._previous_raw_dir = llm_wiki.RAW_DIR
        llm_wiki.ROOT = self.root
        llm_wiki.WIKI_DIR = self.root / "wiki"
        llm_wiki.META_DIR = self.root / "wiki" / "_meta"
        llm_wiki.RAW_DIR = self.root / "raw"

    def tearDown(self) -> None:
        llm_wiki.ROOT = self._previous_root
        llm_wiki.WIKI_DIR = self._previous_wiki_dir
        llm_wiki.META_DIR = self._previous_meta_dir
        llm_wiki.RAW_DIR = self._previous_raw_dir
        self.temp_dir.cleanup()

    def test_maintenance_write_plan_creates_meta_page(self) -> None:
        result = llm_wiki.maintenance_plan(write_plan=True)
        self.assertEqual(result, 0)
        plan_path = self.root / "wiki" / "_meta" / "maintenance-plan.md"
        self.assertTrue(plan_path.exists())

    def test_low_coverage_page_is_flagged(self) -> None:
        plan = llm_wiki.build_maintenance_plan()
        flagged = {path.name for path, _ in plan["low_coverage_pages"]}
        self.assertIn("bounded-loop.md", flagged)

    def test_unregistered_raw_inbox_file_is_flagged(self) -> None:
        plan = llm_wiki.build_maintenance_plan()
        flagged = {path.name for path in plan["unregistered_raw_inbox_files"]}
        self.assertIn("unregistered.md", flagged)
        self.assertNotIn("registered.md", flagged)

    def test_maintenance_does_not_modify_raw_files(self) -> None:
        before = self.unregistered_raw.read_text(encoding="utf-8")
        llm_wiki.maintenance_plan(write_plan=True)
        after = self.unregistered_raw.read_text(encoding="utf-8")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
