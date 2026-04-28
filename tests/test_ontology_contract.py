from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class OntologyContractTests(unittest.TestCase):
    def test_agents_declares_ontology_read_write_and_postflight_contracts(self) -> None:
        content = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("## Ontology Read Contract", content)
        self.assertIn("## Ontology Write Contract", content)
        self.assertIn("## Ontology Postflight", content)
        self.assertIn("ontology-query", content)
        self.assertIn("python3 scripts/llm_wiki.py ontology-check --json", content)

    def test_registry_manifest_declares_canonical_warehouse_contract(self) -> None:
        content = (PROJECT_ROOT / "intelligence" / "manifests" / "ontology_registries.yaml").read_text(
            encoding="utf-8"
        )

        self.assertIn("warehouse/jsonl/documents.jsonl", content)
        self.assertIn("warehouse/jsonl/claims.jsonl", content)
        self.assertIn("warehouse/jsonl/claim_evidence.jsonl", content)
        self.assertIn("foreign-key references", content)
        self.assertIn("python3 scripts/llm_wiki.py ontology-check --json", content)

    def test_ontology_check_json_reports_canonical_registries(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/llm_wiki.py", "ontology-check", "--json"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        self.assertIn(payload["status"], {"ok", "warning"})
        registry_keys = {item["key"] for item in payload["registries"]}
        self.assertIn("documents", registry_keys)
        self.assertIn("claims", registry_keys)
        self.assertIn("claim_evidence", registry_keys)
        self.assertEqual(payload["graph_projection"]["truth_class"], "derived")
        self.assertEqual(payload["graph_projection"]["canonical"], False)

    def test_agent_contract_points_agents_to_ontology_check(self) -> None:
        content = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("python3 scripts/llm_wiki.py ontology-check --json", content)
        self.assertIn("graph projection", content)
        self.assertIn("raw/` first, then `warehouse/jsonl/`", content)


if __name__ == "__main__":
    unittest.main()
