from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.workbench.repository import WorkbenchRepository
from scripts.workbench.server import route_request


ROOT = Path(__file__).resolve().parent.parent


class WorkbenchStrictRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        for directory in [
            "raw/inbox",
            "wiki/_meta",
            "wiki/sources",
            "wiki/concepts",
            "wiki/analyses",
            "warehouse/jsonl",
        ]:
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / "intelligence" / "packs", self.root / "intelligence" / "packs")
        shutil.copytree(ROOT / "intelligence" / "manifests", self.root / "intelligence" / "manifests")
        shutil.copytree(ROOT / "intelligence" / "policies", self.root / "intelligence" / "policies")
        shutil.copy2(ROOT / "intelligence" / "contract_index.yaml", self.root / "intelligence" / "contract_index.yaml")
        (self.root / "wiki/_meta/index.md").write_text("---\ntitle: Index\ntype: meta\n---\n# Index\n", encoding="utf-8")
        (self.root / "wiki/concepts/concept-sample.md").write_text(
            "---\ntitle: Sample Concept\ntype: concept\nstatus: active\n---\n# Sample Concept\n\nDurable sample content.\n",
            encoding="utf-8",
        )
        (self.root / "warehouse/jsonl/entities.jsonl").write_text("", encoding="utf-8")
        (self.root / "warehouse/jsonl/claims.jsonl").write_text("", encoding="utf-8")
        (self.root / "warehouse/jsonl/segments.jsonl").write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_query_preview_is_lexical_diagnostics(self) -> None:
        status, payload = route_request(WorkbenchRepository(self.root), "GET", "/api/query/preview?q=sample")
        self.assertEqual(status, 200)
        self.assertEqual(payload["mode"], "lexical_diagnostics")
        self.assertIn("Lexical diagnostics", payload["answer_markdown"])
        self.assertIn("not an answer draft", payload["answer_markdown"])

    def test_save_analysis_is_disabled_in_strict_mode(self) -> None:
        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/save-analysis",
            body_text=json.dumps({"question": "sample"}),
        )
        self.assertEqual(status, 400)
        self.assertIn("strict LLM mode", payload["error"])

    def test_llm_query_hands_off_to_agent_without_helper(self) -> None:
        status, payload = route_request(WorkbenchRepository(self.root), "GET", "/api/query/llm?q=sample")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "agent_handoff")
        self.assertIn("chat agent", payload["message"])

        status, payload = route_request(WorkbenchRepository(self.root), "GET", "/api/query/llm?q=sample&emit_selection_prompt=1")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "selection_prompt")


if __name__ == "__main__":
    unittest.main()
