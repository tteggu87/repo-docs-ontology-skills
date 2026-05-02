import tempfile
import unittest
from pathlib import Path
import shutil
from unittest.mock import patch

from scripts.generic_ingest import ingest_source
from scripts.ingest.adapters.common import file_document_id
from scripts.ingest.resolver import resolve_family
from scripts.packs.loader import profile_by_family
from scripts.citation import make_citation
from scripts.workbench.repository import WorkbenchRepository
from scripts.workbench.server import route_request
from scripts.intelligence_contracts import load_proposal_policy
from scripts.llm_compile_source import compile_source
from scripts.llm_query import _page_inventory, _parse_selected_stems, build_query_bundle, llm_query
from scripts.proposal_review import apply_reviewed_content, list_proposals, set_proposal_status
from scripts.wiki_graph_navigation import write_navigation_pages

ROOT = Path(__file__).resolve().parent.parent


def build_temp_repo(td: str | Path) -> Path:
    repo = Path(td)
    shutil.copytree(ROOT / "intelligence" / "packs", repo / "intelligence" / "packs")
    shutil.copytree(ROOT / "intelligence" / "manifests", repo / "intelligence" / "manifests")
    shutil.copytree(ROOT / "intelligence" / "policies", repo / "intelligence" / "policies")
    shutil.copy2(ROOT / "intelligence" / "contract_index.yaml", repo / "intelligence" / "contract_index.yaml")
    (repo / "warehouse" / "jsonl").mkdir(parents=True, exist_ok=True)
    (repo / "wiki" / "_meta").mkdir(parents=True, exist_ok=True)
    (repo / "wiki" / "_meta" / "orientation.md").write_text("---\ntitle: Orientation\ntype: meta\n---\n# Orientation\n", encoding="utf-8")
    (repo / "wiki" / "_meta" / "index.md").write_text("---\ntitle: Index\ntype: meta\ncreated: 2026-01-01\n---\n# Index\n", encoding="utf-8")
    (repo / "wiki" / "_meta" / "log.md").write_text("---\ntitle: Log\ntype: meta\ncreated: 2026-01-01\n---\n# Log\n", encoding="utf-8")
    return repo


class TestGenericIngest(unittest.TestCase):
    def test_resolver_email_not_ambiguous(self):
        fam = resolve_family(ROOT, Path("raw/inbox/email/week18.md"))
        self.assertEqual(fam, "email-md-txt")

    def test_profile_mapping_is_generated_from_packs(self):
        mapping = profile_by_family(ROOT)
        self.assertEqual(mapping["email-md-txt"], "email-analysis")
        self.assertEqual(mapping["education-md-txt"], "education-analysis")
        self.assertEqual(mapping["report-md-txt"], "report-consistency-analysis")

    def test_profile_mismatch_errors(self):
        with tempfile.TemporaryDirectory() as td:
            repo = build_temp_repo(td)
            (repo / "raw/inbox/reports").mkdir(parents=True, exist_ok=True)
            src = repo / "raw/inbox/reports/r.md"
            src.write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                ingest_source(repo, src.as_posix(), profile_id="email-analysis")

    def test_education_raw_path_stable_doc_id(self):
        with tempfile.TemporaryDirectory() as td:
            repo = build_temp_repo(td)
            src = repo / "raw/inbox/education/test-stable.md"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text("# h\n\nbody", encoding="utf-8")
            out = ingest_source(repo, src.as_posix(), profile_id="education-analysis")
            self.assertEqual(out["source_family_id"], "education-md-txt")
            self.assertTrue(out["affected_wiki_paths"])
            expected = file_document_id("raw/inbox/education/test-stable.md")
            rows = (repo / "warehouse/jsonl/documents.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertTrue(any(expected in line for line in rows))
            self.assertTrue(list((repo / "wiki/sources").glob("source-*.md")))

    def test_citation_helper_uses_temp_repo(self):
        with tempfile.TemporaryDirectory() as td:
            repo = build_temp_repo(td)
            src = repo / "raw/inbox/education/attention.md"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text("# Self Attention\n\nAttention connects tokens to context.\n\n# Training\n\nOptimization uses gradients.", encoding="utf-8")
            ingest_source(repo, src.as_posix(), profile_id="education-analysis")
            units = (repo / "warehouse/jsonl/content_units.jsonl").read_text(encoding="utf-8")
            unit_id = units.split('"unit_id": "')[1].split('"', 1)[0]
            citation = make_citation(repo, unit_id)
            self.assertTrue(citation["ok"])
            self.assertIn("[[source-", citation["citation"])
            self.assertIn("lines", citation["citation"])

    def test_workbench_ingest_preview_routes_use_temp_repo(self):
        with tempfile.TemporaryDirectory() as td:
            repo = build_temp_repo(td)
            src = repo / "raw/inbox/education/preview.md"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text("# Preview\n\nA preview body.", encoding="utf-8")
            workbench = WorkbenchRepository(repo)
            status, inbox = route_request(workbench, "GET", "/api/ingest/inbox")
            self.assertEqual(status, 200)
            self.assertEqual(inbox["items"][0]["detected_profile_id"], "education-analysis")
            status, preview = route_request(workbench, "GET", "/api/ingest/preview?path=raw/inbox/education/preview.md")
            self.assertEqual(status, 200)
            self.assertEqual(preview["expected_unit_count"], 1)

    def test_strict_llm_workflows_fail_without_config_unless_prompt_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            repo = build_temp_repo(td)
            src = repo / "raw/inbox/education/llm.md"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text("# LLM Reasoning\n\nOntology links should guide reasoning.", encoding="utf-8")
            summary = ingest_source(repo, src.as_posix(), profile_id="education-analysis")
            source_page = [path for path in summary["affected_wiki_paths"] if path.startswith("wiki/sources/")][0]
            with self.assertRaises(RuntimeError):
                compile_source(repo, source_page)
            compiled = compile_source(repo, source_page, emit_bundle=True)
            self.assertEqual(compiled["status"], "prompt_bundle")
            self.assertIn("llm_system_prompt", compiled)
            self.assertIn("meta_surfaces", compiled["bundle"])
            self.assertIn("wiki_moc", compiled["bundle"]["meta_surfaces"])
            with self.assertRaises(RuntimeError):
                llm_query(repo, "How should ontology links guide reasoning?")
            queried = llm_query(repo, "How should ontology links guide reasoning?", emit_selection_prompt=True)
            self.assertEqual(queried["status"], "selection_prompt")
            self.assertIn("llm_selection_system_prompt", queried)
            self.assertIn("meta_surfaces", queried["llm_selection_user_prompt"])

    def test_llm_compile_saves_proposal_without_touching_active_pages(self):
        with tempfile.TemporaryDirectory() as td:
            repo = build_temp_repo(td)
            src = repo / "raw/inbox/education/compile.md"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text("# Compile\n\nLLM should propose wiki changes for human review.", encoding="utf-8")
            summary = ingest_source(repo, src.as_posix(), profile_id="education-analysis")
            source_page = [path for path in summary["affected_wiki_paths"] if path.startswith("wiki/sources/")][0]

            with (
                patch("scripts.llm_compile_source.load_continue_helper_config", return_value={"enabled": True, "provider": "test"}),
                patch("scripts.llm_compile_source.helper_model_public_summary", return_value={"provider": "test"}),
                patch(
                    "scripts.llm_compile_source.run_helper_chat_completion",
                    return_value='{"pages_to_update":[],"new_page_candidates":[],"citation_links":[],"uncertainties":[]}',
                ),
            ):
                result = compile_source(repo, source_page)

            self.assertEqual(result["status"], "ok")
            self.assertIn("proposal_path", result)
            proposal_path = repo / result["proposal_path"]
            self.assertTrue(proposal_path.exists())
            proposal_text = proposal_path.read_text(encoding="utf-8")
            proposal_policy = load_proposal_policy(repo)
            self.assertIn("# Compile Proposal", proposal_text)
            self.assertIn("## Human Review Checklist", proposal_text)
            self.assertIn(f"status: {proposal_policy['initial_status']}", proposal_text)
            self.assertIn(f"analysis_method: {proposal_policy['analysis_method']}", proposal_text)
            self.assertIn(f"trust_level: {proposal_policy['trust_level']}", proposal_text)
            self.assertFalse((repo / "wiki/concepts/compile.md").exists())

    def test_proposal_review_applies_only_accepted_human_content(self):
        with tempfile.TemporaryDirectory() as td:
            repo = build_temp_repo(td)
            (repo / "wiki/analyses").mkdir(parents=True, exist_ok=True)
            proposal = repo / "wiki/analyses/analysis-compile-proposal-source.md"
            proposal.write_text(
                "---\n"
                "title: Compile Proposal\n"
                "type: analysis\n"
                "status: draft\n"
                "analysis_method: llm_compile_proposal\n"
                "trust_level: human_review_required\n"
                "---\n\n"
                "# Compile Proposal\n\nLLM output pending review.\n",
                encoding="utf-8",
            )
            reviewed = repo / "wiki/analyses/reviewed-concept.md"
            reviewed.write_text(
                "---\ntitle: Reviewed Concept\ntype: concept\nstatus: active\n---\n\n# Reviewed Concept\n\nHuman-approved content.\n",
                encoding="utf-8",
            )

            listed = list_proposals(repo)
            self.assertEqual(len(listed["proposals"]), 1)
            with self.assertRaises(ValueError):
                apply_reviewed_content(repo, proposal.relative_to(repo).as_posix(), "wiki/concepts/reviewed-concept.md", reviewed.relative_to(repo).as_posix())

            accepted = set_proposal_status(repo, proposal.relative_to(repo).as_posix(), "accepted")
            self.assertEqual(accepted["new_status"], "accepted")
            applied = apply_reviewed_content(repo, proposal.relative_to(repo).as_posix(), "wiki/concepts/reviewed-concept.md", reviewed.relative_to(repo).as_posix())
            self.assertEqual(applied["target_path"], "wiki/concepts/reviewed-concept.md")
            self.assertIn("Human-approved content", (repo / "wiki/concepts/reviewed-concept.md").read_text(encoding="utf-8"))
            self.assertIn("status: applied", proposal.read_text(encoding="utf-8"))

    def test_llm_page_selection_has_no_regex_fallback(self):
        with self.assertRaises(Exception):
            _parse_selected_stems("concept-a source-b")

    def test_llm_query_excludes_draft_compile_proposals_from_reasoning_surface(self):
        with tempfile.TemporaryDirectory() as td:
            repo = build_temp_repo(td)
            (repo / "wiki/analyses").mkdir(parents=True, exist_ok=True)
            (repo / "wiki/concepts").mkdir(parents=True, exist_ok=True)
            (repo / "wiki/analyses/analysis-proposal.md").write_text(
                "---\n"
                "title: Compile Proposal\n"
                "type: analysis\n"
                "status: draft\n"
                "analysis_method: llm_compile_proposal\n"
                "---\n"
                "# Compile Proposal\n\nUnreviewed LLM output should not answer questions.",
                encoding="utf-8",
            )
            (repo / "wiki/concepts/concept-reviewed.md").write_text(
                "---\n"
                "title: Reviewed Concept\n"
                "type: concept\n"
                "status: active\n"
                "---\n"
                "# Reviewed Concept\n\nReviewed wiki content.",
                encoding="utf-8",
            )

            inventory_stems = {page["stem"] for page in _page_inventory(repo)}
            self.assertIn("concept-reviewed", inventory_stems)
            self.assertNotIn("analysis-proposal", inventory_stems)
            reviewed_inventory = [page for page in _page_inventory(repo) if page["stem"] == "concept-reviewed"][0]
            self.assertNotIn("preview", reviewed_inventory)
            self.assertNotIn("Reviewed wiki content", str(reviewed_inventory))
            bundle = build_query_bundle(repo, "What is reviewed?", ["analysis-proposal", "concept-reviewed"])
            self.assertIn("meta_surfaces", bundle)
            selected_stems = {page["stem"] for page in bundle["selected_pages"]}
            self.assertEqual(selected_stems, {"concept-reviewed"})

    def test_wiki_graph_navigation_writes_meta_pages(self):
        with tempfile.TemporaryDirectory() as td:
            repo = build_temp_repo(td)
            (repo / "wiki/concepts").mkdir(parents=True, exist_ok=True)
            (repo / "wiki/sources").mkdir(parents=True, exist_ok=True)
            (repo / "wiki/concepts/concept-a.md").write_text(
                "---\ntitle: Concept A\ntype: concept\nupdated: 2026-04-10\n---\n# Concept A\n\nLinks to [[source-a]].",
                encoding="utf-8",
            )
            (repo / "wiki/sources/source-a.md").write_text(
                "---\ntitle: Source A\ntype: source\nupdated: 2026-04-10\n---\n# Source A\n\nUncertain evidence.",
                encoding="utf-8",
            )
            result = write_navigation_pages(repo)
            self.assertEqual(result["status"], "ok")
            self.assertTrue((repo / "wiki/_meta/moc.md").exists())
            self.assertTrue((repo / "wiki/_meta/link-map.md").exists())
            self.assertTrue((repo / "wiki/_meta/source-coverage.md").exists())
            self.assertIn("[[source-a]]", (repo / "wiki/_meta/link-map.md").read_text(encoding="utf-8"))
            self.assertIn("[[source-a]]", (repo / "wiki/_meta/contradiction-review.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
