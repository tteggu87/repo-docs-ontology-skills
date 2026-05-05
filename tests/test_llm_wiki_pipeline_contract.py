from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_PATH = ROOT / ".agents" / "skills" / "llm-wiki-bootstrap" / "scripts" / "bootstrap_llm_wiki.py"


def read_repo_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def load_bootstrap_module():
    spec = importlib.util.spec_from_file_location("bootstrap_llm_wiki", BOOTSTRAP_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClosedIngestPipelineContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bootstrap = load_bootstrap_module()

    def test_root_agents_declares_closed_ingest_without_semantic_router(self) -> None:
        text = read_repo_text("AGENTS.md")
        self.assertIn("## Closed Ingest Pipeline", text)
        self.assertIn("`scripts/llm_wiki.py ingest` is source registration only", text)
        self.assertIn("This pipeline closes the lifecycle, not semantic judgment.", text)
        self.assertIn("Accepted claims require explicit review metadata and supporting evidence.", text)
        self.assertIn("Do not use filename, keyword", text)

    def test_ingest_skill_has_closed_contract_and_report_format(self) -> None:
        text = read_repo_text(".agents/skills/llm-wiki-ontology-ingest/SKILL.md")
        self.assertIn("## Closed Pipeline Contract", text)
        self.assertIn("This pipeline closes the lifecycle, not semantic judgment.", text)
        self.assertIn("## Completion Report", text)
        self.assertIn("JSONL registries updated, skipped, not applicable, or pending", text)
        self.assertIn("do not report the result as completed ontology-backed ingest", text)

    def test_operator_skill_does_not_accept_missing_validation_as_success(self) -> None:
        text = read_repo_text(".agents/skills/ontology-pipeline-operator/SKILL.md")
        self.assertIn("validation must check the closed ingest lifecycle", text)
        self.assertIn("Do not report success when validation output is missing.", text)
        self.assertIn("source-registration-only results under", text)

    def test_bootstrap_generates_closed_ingest_contracts(self) -> None:
        ontology_agents = self.bootstrap.ontology_agents_md()
        wiki_only_agents = self.bootstrap.wiki_only_agents_md()
        ontology_readme = self.bootstrap.readme(Path("ExampleOntologyWiki"), "wiki-plus-ontology")
        wiki_only_readme = self.bootstrap.readme(Path("ExampleWiki"), "wiki-only")

        self.assertIn("## Closed Ingest Pipeline", ontology_agents)
        self.assertIn("`scripts/llm_wiki.py ingest` is source registration only", ontology_agents)
        self.assertIn("Accepted claims require explicit review metadata", ontology_agents)
        self.assertIn("## Closed Wiki Ingest Pipeline", wiki_only_agents)
        self.assertIn("source registration only", wiki_only_agents)
        self.assertIn("raw -> register -> warehouse/jsonl when applicable -> wiki projection", ontology_readme)
        self.assertIn("raw -> register -> wiki projection -> meta refresh", wiki_only_readme)

    def test_bootstrap_writes_pipeline_manifest_for_ontology_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "vault"
            self.bootstrap.scaffold(target, force=False, profile="wiki-plus-ontology")

            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            readme = (target / "README.md").read_text(encoding="utf-8")
            manifest = (target / "intelligence" / "manifests" / "pipelines.yaml").read_text(encoding="utf-8")

        self.assertIn("## Closed Ingest Pipeline", agents)
        self.assertIn("source registration only", readme)
        self.assertIn("manifest_as_runtime_executor", manifest)
        self.assertIn("yaml_as_semantic_wiki", manifest)
        self.assertNotIn("if_keyword", manifest)
        self.assertNotIn("filename_contains", manifest)

    def test_repo_pipeline_manifest_is_stage_contract_only(self) -> None:
        text = read_repo_text("intelligence/manifests/pipelines.yaml")
        self.assertIn("manifest_as_runtime_executor", text)
        self.assertIn("yaml_as_semantic_wiki", text)
        self.assertIn("semantic_judgment_owner", text)
        self.assertNotIn("if_keyword", text)
        self.assertNotIn("filename_contains", text)


if __name__ == "__main__":
    unittest.main()
