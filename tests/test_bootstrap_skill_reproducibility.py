from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP = ROOT / ".agents/skills/llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py"
SKILL_ROOT = ROOT / ".agents/skills"
EXPECTED_SKILLS = {
    "repo-docs-intelligence-bootstrap",
    "llm-wiki-bootstrap",
    "lightweight-ontology-core",
    "lg-ontology",
    "llm-wiki-ontology-ingest",
    "ontology-pipeline-operator",
}


class BootstrapSkillReproducibilityTests(unittest.TestCase):
    def run_cmd(
        self,
        args: list[str],
        *,
        cwd: Path,
        home: Path | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if home is not None:
            env["HOME"] = str(home)
        env.pop("LLM_WIKI_BOOTSTRAP_SCRIPT", None)
        result = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if check:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def scaffold(self, tmp: Path, home: Path, name: str, *profile_args: str) -> tuple[Path, subprocess.CompletedProcess[str]]:
        target = tmp / name
        result = self.run_cmd(
            [sys.executable, str(BOOTSTRAP), str(target), *profile_args],
            cwd=ROOT,
            home=home,
        )
        return target, result

    def test_bootstrap_script_is_repo_local_not_home_launcher(self) -> None:
        content = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertNotIn("LLM_WIKI_BOOTSTRAP_SCRIPT", content)
        self.assertNotIn(".codex/skills", content)
        self.assertNotIn(".agents/skills", content)
        self.assertIn("llm-first-ontology", content)

    def test_full_doctology_skillset_is_repo_local(self) -> None:
        for skill in sorted(EXPECTED_SKILLS):
            skill_dir = SKILL_ROOT / skill
            self.assertTrue(skill_dir.is_dir(), skill)
            self.assertTrue((skill_dir / "SKILL.md").is_file(), skill)

        expected_support = [
            "repo-docs-intelligence-bootstrap/scripts/validate_repo_docs_intelligence.py",
            "lightweight-ontology-core/scripts/validate_ontology_graph.py",
            "lightweight-ontology-core/references/claim-lifecycle.md",
            "lg-ontology/scripts/export_graph_projection.py",
            "lg-ontology/references/graph-projection-model.md",
            "llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py",
            "llm-wiki-ontology-ingest/SKILL.md",
            "ontology-pipeline-operator/references/operating-model.md",
        ]
        for relative in expected_support:
            self.assertTrue((SKILL_ROOT / relative).is_file(), relative)

    def test_default_llm_first_ontology_profile_with_empty_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as home_dir:
            tmp = Path(tmp_dir)
            home = Path(home_dir)
            target, result = self.scaffold(tmp, home, "default")

            self.assertIn("profile=llm-first-ontology", result.stdout)
            required = [
                "AGENTS.md",
                "README.md",
                ".gitignore",
                "wikiconfig.example.json",
                "wikiconfig.json",
                "docs/LLM_FIRST_ONTOLOGY_BOOTSTRAP_PROFILE.md",
                "intelligence/contract_index.yaml",
                "intelligence/policies/semantic_boundary.yaml",
                "intelligence/policies/proposal_lifecycle.yaml",
                "intelligence/manifests/semantic_workflows.yaml",
                "intelligence/manifests/meta_surfaces.yaml",
                "intelligence/manifests/page_policy.yaml",
                "intelligence/manifests/registries.yaml",
                "intelligence/manifests/relation_types.yaml",
                "warehouse/jsonl/documents.jsonl",
                "warehouse/jsonl/content_units.jsonl",
                "warehouse/jsonl/source_versions.jsonl",
                "warehouse/jsonl/compile_proposals.jsonl",
                "warehouse/jsonl/review_events.jsonl",
                "scripts/llm_query.py",
                "scripts/llm_compile_source.py",
                "scripts/query_analysis.py",
                "scripts/proposal_review.py",
                "scripts/validate_intelligence.py",
                "scripts/validate_profiles.py",
                "scripts/validate_registries.py",
                "scripts/validate_workbench_manifest.py",
                "scripts/validate_repo_docs_intelligence.py",
            ]
            for relative in required:
                self.assertTrue((target / relative).exists(), relative)

            config = json.loads((target / "wikiconfig.json").read_text(encoding="utf-8"))
            self.assertFalse(config["llmWiki"]["enabled"])

            self.run_cmd(["git", "init", "-q"], cwd=target, home=home)
            ignore = self.run_cmd(["git", "check-ignore", "-v", "wikiconfig.json"], cwd=target, home=home)
            self.assertIn("wikiconfig.json", ignore.stdout)

            for validator in [
                "scripts/validate_intelligence.py",
                "scripts/validate_profiles.py",
                "scripts/validate_registries.py",
                "scripts/validate_workbench_manifest.py",
                "scripts/validate_repo_docs_intelligence.py",
            ]:
                self.run_cmd([sys.executable, validator], cwd=target)

            query = self.run_cmd([sys.executable, "scripts/llm_query.py", "smoke question"], cwd=target)
            self.assertEqual(json.loads(query.stdout)["status"], "agent_handoff")

            selection = self.run_cmd(
                [sys.executable, "scripts/llm_query.py", "smoke question", "--emit-selection-prompt"],
                cwd=target,
            )
            self.assertEqual(json.loads(selection.stdout)["status"], "selection_prompt")

            source_page = target / "wiki/sources/source-smoke.md"
            source_page.parent.mkdir(parents=True, exist_ok=True)
            source_page.write_text("# Smoke Source\n\nTest source.\n", encoding="utf-8")
            compile_result = self.run_cmd(
                [sys.executable, "scripts/llm_compile_source.py", "--source-page", "wiki/sources/source-smoke.md"],
                cwd=target,
            )
            self.assertEqual(json.loads(compile_result.stdout)["status"], "agent_handoff")

    def test_wiki_only_profile_is_plain_wiki_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as home_dir:
            target, result = self.scaffold(Path(tmp_dir), Path(home_dir), "wiki-only", "--profile", "wiki-only")
            self.assertIn("profile=wiki-only", result.stdout)
            for relative in [
                "AGENTS.md",
                "README.md",
                ".gitignore",
                "raw/inbox",
                "wiki/_meta/index.md",
                "wiki/_meta/log.md",
                "scripts/llm_wiki.py",
                "templates/source_page_template.md",
            ]:
                self.assertTrue((target / relative).exists(), relative)
            self.assertFalse((target / "intelligence/contract_index.yaml").exists())
            self.assertFalse((target / "warehouse/jsonl").exists())
            self.assertFalse((target / "scripts/llm_query.py").exists())

    def test_wiki_plus_ontology_profile_is_legacy_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir, tempfile.TemporaryDirectory() as home_dir:
            target, result = self.scaffold(
                Path(tmp_dir),
                Path(home_dir),
                "wiki-plus",
                "--profile",
                "wiki-plus-ontology",
            )
            self.assertIn("profile=wiki-plus-ontology", result.stdout)
            self.assertIn("deprecated", result.stderr.lower())
            for relative in [
                "intelligence/glossary.yaml",
                "intelligence/manifests/actions.yaml",
                "intelligence/manifests/datasets.yaml",
                "scripts/reindex_sqlite_operational.py",
                "scripts/refresh_duckdb_analytics.py",
                "scripts/verify_three_layer_drift.py",
                "templates/llm-wiki-three-layer/sqlite_operational.schema.sql",
                "templates/llm-wiki-three-layer/duckdb_analytical.schema.sql",
                "warehouse/jsonl/messages.jsonl",
                "warehouse/jsonl/documents.jsonl",
                "warehouse/jsonl/entities.jsonl",
                "warehouse/jsonl/claims.jsonl",
                "warehouse/jsonl/claim_evidence.jsonl",
                "warehouse/jsonl/segments.jsonl",
                "warehouse/jsonl/derived_edges.jsonl",
            ]:
                self.assertTrue((target / relative).exists(), relative)
            self.assertFalse((target / "scripts/llm_query.py").exists())

    def test_vendored_skill_tree_excludes_generated_artifacts(self) -> None:
        forbidden_names = {"__pycache__", "results.tsv", ".codex", ".omx"}
        forbidden_suffixes = {".pyc", ".pyo"}
        result = subprocess.run(
            ["git", "ls-files", str(SKILL_ROOT.relative_to(ROOT))],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for raw_path in result.stdout.splitlines():
            path = Path(raw_path)
            self.assertTrue(raw_path.startswith(".agents/skills/"), raw_path)
            self.assertFalse(any(part in forbidden_names for part in path.parts), raw_path)
            self.assertNotIn(path.suffix, forbidden_suffixes, raw_path)


if __name__ == "__main__":
    unittest.main()
