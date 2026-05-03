from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.query_analysis import save_query_analysis


class QueryAnalysisTests(unittest.TestCase):
    def test_save_query_analysis_creates_analysis_and_updates_meta(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "wiki/_meta").mkdir(parents=True)
            (root / "wiki/analyses").mkdir(parents=True)
            (root / "wiki/_meta/index.md").write_text(
                "---\ntitle: Index\ntype: meta\nupdated: 2026-01-01\n---\n\n# Index\n\n## Analyses\n\n",
                encoding="utf-8",
            )
            (root / "wiki/_meta/log.md").write_text("# Log\n", encoding="utf-8")

            rel = save_query_analysis(
                root,
                question="라텔이 좋아하는 생물은?",
                answer_markdown="답은 **개미**다.",
                sources=["[[source-kakao]]", "raw/processed/chat.txt:3375"],
                evidence_mix={"raw": 60, "wiki": 25, "ontology": 15},
                proposed_updates=["[[ratel]] 후보 업데이트: 개미 비유를 추가"],
                uncertainty=["개미핥기 발화는 농담성 후보로 남김"],
            )

            analysis_path = root / rel
            self.assertTrue(analysis_path.exists())
            content = analysis_path.read_text(encoding="utf-8")
            self.assertIn("analysis_method: chat_agent_llm", content)
            self.assertIn("trust_level: evidence_grounded", content)
            self.assertIn("답은 **개미**다.", content)
            self.assertIn("raw: 60", content)
            self.assertIn("Proposed Wiki Updates", content)

            index = (root / "wiki/_meta/index.md").read_text(encoding="utf-8")
            self.assertIn(f"[[{analysis_path.stem}]]", index)
            self.assertIn("updated:", index)

            log = (root / "wiki/_meta/log.md").read_text(encoding="utf-8")
            self.assertIn(f"[[{analysis_path.stem}]]", log)
            self.assertIn("Active semantic page updates", log)


if __name__ == "__main__":
    unittest.main()
