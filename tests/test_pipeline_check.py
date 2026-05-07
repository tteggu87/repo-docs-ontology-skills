from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_CHECK_PATH = ROOT / "scripts" / "pipeline_check.py"
BOOTSTRAP_PATH = ROOT / ".agents" / "skills" / "llm-wiki-bootstrap" / "scripts" / "bootstrap_llm_wiki.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PipelineCheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pipeline_check = load_module(PIPELINE_CHECK_PATH, "pipeline_check_under_test")
        cls.bootstrap = load_module(BOOTSTRAP_PATH, "bootstrap_for_pipeline_check_test")

    def test_missing_source_is_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "vault"
            self.bootstrap.scaffold(root, force=False, profile="wiki-plus-ontology")

            result = self.pipeline_check.check_source(root, "raw/inbox/missing.md")

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["source_page_stage"], "failed")
        self.assertIn("source_exists", [item["name"] for item in result["checks"]])

    def test_existing_source_without_source_page_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "vault"
            self.bootstrap.scaffold(root, force=False, profile="wiki-plus-ontology")
            source = root / "raw" / "inbox" / "example.md"
            source.write_text("# Example\n", encoding="utf-8")

            result = self.pipeline_check.check_source(root, "raw/inbox/example.md")

        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["source_page_stage"], "pending")
        self.assertEqual(result["semantic_status"], "pending")

    def test_log_matching_uses_exact_source_identity_not_basename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "vault"
            self.bootstrap.scaffold(root, force=False, profile="wiki-plus-ontology")
            source_a = root / "raw" / "inbox" / "a" / "same.md"
            source_b = root / "raw" / "inbox" / "b" / "same.md"
            source_a.parent.mkdir(parents=True, exist_ok=True)
            source_b.parent.mkdir(parents=True, exist_ok=True)
            source_a.write_text("# A\n", encoding="utf-8")
            source_b.write_text("# B\n", encoding="utf-8")
            source_page_b = root / "wiki" / "sources" / "source-b-same.md"
            source_page_b.write_text(
                """---
title: "B Same"
type: source
status: inbox
created: 2026-05-07
updated: 2026-05-07
raw_path: "raw/inbox/b/same.md"
---

# B Same
""",
                encoding="utf-8",
            )
            log_path = root / "wiki" / "_meta" / "log.md"
            log_path.write_text(
                "# Log\n\n- Registered source at `raw/inbox/a/same.md`\n",
                encoding="utf-8",
            )

            result = self.pipeline_check.check_source(root, "raw/inbox/b/same.md")

        log_check = next(item for item in result["checks"] if item["name"] == "log_mentions_source")
        self.assertEqual(log_check["status"], "pending")

    def test_ingest_report_matching_uses_exact_source_identity_not_basename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "vault"
            self.bootstrap.scaffold(root, force=False, profile="wiki-plus-ontology")
            source_a = root / "raw" / "inbox" / "a" / "same.md"
            source_b = root / "raw" / "inbox" / "b" / "same.md"
            source_a.parent.mkdir(parents=True, exist_ok=True)
            source_b.parent.mkdir(parents=True, exist_ok=True)
            source_a.write_text("# A\n", encoding="utf-8")
            source_b.write_text("# B\n", encoding="utf-8")
            source_page_b = root / "wiki" / "sources" / "source-b-same.md"
            source_page_b.write_text(
                """---
title: "B Same"
type: source
status: inbox
created: 2026-05-07
updated: 2026-05-07
raw_path: "raw/inbox/b/same.md"
---

# B Same
""",
                encoding="utf-8",
            )
            reports_dir = root / "wiki" / "_meta" / "ingest_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            (reports_dir / "ingest-a-same.md").write_text(
                """---
title: "A Same Report"
type: ingest_report
status: partial
---

## Source Registered

- Raw path: `raw/inbox/a/same.md`
- Source page: [[source-a-same]]
""",
                encoding="utf-8",
            )

            result = self.pipeline_check.check_source(root, "raw/inbox/b/same.md")

        report_check = next(item for item in result["checks"] if item["name"] == "ingest_report_exists")
        self.assertEqual(report_check["status"], "pending")


if __name__ == "__main__":
    unittest.main()
