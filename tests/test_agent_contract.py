from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENTS_PATH = PROJECT_ROOT / "AGENTS.md"


class AgentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = AGENTS_PATH.read_text(encoding="utf-8")
        cls.lower_content = cls.content.lower()

    def test_required_sections_exist(self) -> None:
        self.assertIn("## Agent Entry Contract", self.content)
        self.assertIn("## Operation Classifier", self.content)
        self.assertIn("## Capability And Fallback Matrix", self.content)
        self.assertIn("## Write Policy", self.content)
        self.assertIn("## Durable Answer Rule", self.content)

    def test_truth_boundaries_are_explicit(self) -> None:
        self.assertIn("raw/", self.lower_content)
        self.assertIn("immutable source truth", self.lower_content)
        self.assertIn("warehouse/jsonl", self.lower_content)
        self.assertIn("canonical structured truth", self.lower_content)
        self.assertIn("human-facing synthesis", self.lower_content)

    def test_durable_answers_save_to_wiki_analyses(self) -> None:
        self.assertIn("wiki/analyses/", self.content)


if __name__ == "__main__":
    unittest.main()
