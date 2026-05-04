from __future__ import annotations

import json
import subprocess
import tempfile
import unicodedata
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.workbench_api import ACTION_COMMANDS, WorkbenchRepository, json_ready, read_jsonl, route_request
from scripts.workbench.llm_config import load_continue_helper_config


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(content + ("\n" if content else ""), encoding="utf-8")


class WorkbenchApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        for directory in [
            "raw/inbox",
            "raw/processed",
            "raw/notes",
            "raw/assets",
            "wiki/_meta",
            "wiki/sources",
            "wiki/concepts",
            "wiki/analyses",
            "warehouse/jsonl",
            "warehouse/graph_projection",
        ]:
            (self.root / directory).mkdir(parents=True, exist_ok=True)

        (self.root / "raw" / "inbox" / "sample.md").write_text("raw inbox file\n", encoding="utf-8")
        (self.root / "raw" / "processed" / "done.txt").write_text("processed file\n", encoding="utf-8")

        (self.root / "wiki" / "sources" / "source-sample.md").write_text(
            "---\n"
            'title: "Sample Source"\n'
            "type: source\n"
            "status: active\n"
            "created: 2026-04-09\n"
            "updated: 2026-04-10\n"
            'raw_path: "raw/inbox/sample.md"\n'
            "---\n\n"
            "# Sample Source\n\n"
            "A durable source page linked to [[concept-sample]] and [[analysis-sample]].\n",
            encoding="utf-8",
        )
        (self.root / "wiki" / "concepts" / "concept-sample.md").write_text(
            "---\n"
            'title: "Sample Concept"\n'
            "type: concept\n"
            "status: active\n"
            "created: 2026-04-09\n"
            "updated: 2026-04-09\n"
            "---\n\n"
            "# Sample Concept\n\n"
            "A durable concept page referencing [[source-sample]].\n",
            encoding="utf-8",
        )
        (self.root / "wiki" / "analyses" / "analysis-sample.md").write_text(
            "---\n"
            'title: "Sample Analysis"\n'
            "type: analysis\n"
            "status: active\n"
            "created: 2026-04-09\n"
            "updated: 2026-02-01\n"
            "---\n\n"
            "# Sample Analysis\n\n"
            "This analysis discusses sample durability and points back to [[source-sample]]. Open question: is the coverage strong enough?\n",
            encoding="utf-8",
        )
        (self.root / "wiki" / "_meta" / "index.md").write_text(
            "---\n"
            'title: "Index"\n'
            "type: meta\n"
            "status: active\n"
            "created: 2026-04-09\n"
            "updated: 2026-04-09\n"
            "---\n\n"
            "# Index\n\n"
            "## Sources\n\n"
            "- [[source-sample]] - raw_path: \"raw/inbox/sample.md\"\n\n"
            "## Concepts\n\n"
            "- [[concept-sample]] - A durable concept page.\n",
            encoding="utf-8",
        )
        (self.root / "wiki" / "_meta" / "log.md").write_text(
            "---\n"
            "title: Log\n"
            "type: meta\n"
            "status: active\n"
            "created: 2026-04-09\n"
            "updated: 2026-04-09\n"
            "---\n\n"
            "# Log\n\n"
            "## [2026-04-09] query | sample question\n\n"
            "- Saved a sample analysis.\n\n"
            "## [2026-04-09] refactor | sample change\n\n"
            "- Updated the sample source page.\n",
            encoding="utf-8",
        )

        write_jsonl(
            self.root / "warehouse" / "jsonl" / "documents.jsonl",
            [
                {
                    "document_id": "doc-sample",
                    "source_page": "source-sample",
                    "source_kind": "note",
                    "source_family_id": "family-sample",
                    "export_version_id": "export-sample-v1",
                    "incremental_status_page": "source-sample-incremental-status",
                    "message_count": 3,
                }
            ],
        )
        write_jsonl(
            self.root / "warehouse" / "jsonl" / "source_versions.jsonl",
            [
                {
                    "export_version_id": "export-sample-v1",
                    "document_id": "doc-sample",
                    "source_kind": "note",
                    "source_family_id": "family-sample",
                    "raw_path": "raw/inbox/sample.md",
                    "message_count": 3,
                    "ingested_at": "2026-04-09",
                }
            ],
        )
        write_jsonl(
            self.root / "warehouse" / "jsonl" / "messages.jsonl",
            [
                {
                    "message_id": "msg-1",
                    "document_id": "doc-sample",
                    "text": "hello",
                }
            ],
        )
        write_jsonl(
            self.root / "warehouse" / "jsonl" / "entities.jsonl",
            [
                {
                    "entity_id": "entity-sample",
                    "entity_type": "concept",
                    "source_document_id": "doc-sample",
                    "name": "Sample Entity",
                }
            ],
        )
        write_jsonl(
            self.root / "warehouse" / "jsonl" / "claims.jsonl",
            [
                {
                    "claim_id": "claim-sample",
                    "document_id": "doc-sample",
                    "source_document_id": "doc-sample",
                    "predicate": "covers",
                    "review_state": "needs_review",
                    "confidence": 0.62,
                    "claim_text": "Sample durability still needs explicit review.",
                }
            ],
        )
        write_jsonl(
            self.root / "warehouse" / "jsonl" / "claim_evidence.jsonl",
            [
                {
                    "claim_id": "claim-sample",
                    "source_document_id": "doc-sample",
                    "evidence_id": "evidence-sample",
                }
            ],
        )
        write_jsonl(
            self.root / "warehouse" / "jsonl" / "segments.jsonl",
            [
                {
                    "segment_id": "segment-sample",
                    "document_id": "doc-sample",
                    "text": "Sample durability discussion.",
                }
            ],
        )
        write_jsonl(self.root / "warehouse" / "jsonl" / "derived_edges.jsonl", [])

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_summary_reports_counts_and_empty_graph_warning(self) -> None:
        repo = WorkbenchRepository(self.root)
        summary = repo.summary()

        self.assertEqual(summary["raw"]["counts"]["inbox"], 1)
        self.assertEqual(summary["raw"]["counts"]["processed"], 1)
        self.assertEqual(summary["raw"]["counts"]["other"], 0)
        self.assertEqual(summary["raw"]["counts"]["total"], 2)
        self.assertEqual(summary["wiki"]["page_count"], 5)
        self.assertEqual(summary["warehouse"]["registry_counts"]["documents"], 1)
        self.assertEqual(summary["graph_projection"]["available"], False)
        self.assertIn("graph_projection_empty", summary["warnings"])

    def test_route_request_returns_wiki_page_and_source_detail(self) -> None:
        repo = WorkbenchRepository(self.root)

        status, page_payload = route_request(repo, "GET", "/api/wiki/page/source-sample")
        self.assertEqual(status, 200)
        self.assertEqual(page_payload["frontmatter"]["title"], "Sample Source")
        self.assertTrue(page_payload["related_pages"])

        status, source_payload = route_request(repo, "GET", "/api/sources/source-sample")
        self.assertEqual(status, 200)
        self.assertEqual(source_payload["raw_path"], "raw/inbox/sample.md")
        self.assertEqual(source_payload["incremental_status"]["latest_export_version_id"], "export-sample-v1")
        self.assertTrue(source_payload["related_pages"])
        self.assertEqual(source_payload["incremental_status"]["new_message_count"], 3)
        self.assertEqual(source_payload["incremental_status"]["unchanged_message_count"], 0)
        self.assertIn("warehouse/jsonl/messages.jsonl", source_payload["incremental_status"]["affected_registry_paths"])
        self.assertIn("wiki/_meta/log.md", source_payload["incremental_status"]["affected_wiki_paths"])
        self.assertEqual(source_payload["coverage"]["claim_count"], 1)
        self.assertEqual(source_payload["coverage"]["approved_claim_count"], 0)
        self.assertEqual(source_payload["coverage"]["pending_claim_count"], 1)
        self.assertEqual(source_payload["coverage"]["rejected_claim_count"], 0)
        self.assertEqual(source_payload["coverage"]["entity_count"], 1)
        self.assertEqual(source_payload["review_queue"][0]["claim_id"], "claim-sample")

    def test_json_ready_serializes_frontmatter_dates(self) -> None:
        repo = WorkbenchRepository(self.root)
        payload = repo.wiki_page("source-sample")
        normalized = json_ready(payload)

        self.assertEqual(normalized["frontmatter"]["created"], "2026-04-09")
        json.dumps(normalized)

    def test_warehouse_summary_and_recent_log_are_structured(self) -> None:
        repo = WorkbenchRepository(self.root)

        status, warehouse_payload = route_request(repo, "GET", "/api/warehouse/summary")
        self.assertEqual(status, 200)
        documents_registry = next(item for item in warehouse_payload["registries"] if item["key"] == "documents")
        self.assertEqual(documents_registry["count"], 1)
        self.assertEqual(documents_registry["truth_class"], "canonical")

        status, log_payload = route_request(repo, "GET", "/api/meta/log/recent?limit=1")
        self.assertEqual(status, 200)
        self.assertEqual(len(log_payload["entries"]), 1)
        self.assertEqual(log_payload["entries"][0]["title"], "sample change")

    def test_workbench_feed_and_related_route_are_structured(self) -> None:
        repo = WorkbenchRepository(self.root)

        status, feed_payload = route_request(repo, "GET", "/api/workbench/feed?limit=1")
        self.assertEqual(status, 200)
        self.assertEqual(feed_payload["recent_sources"][0]["stem"], "source-sample")
        self.assertEqual(feed_payload["recent_analyses"][0]["stem"], "analysis-sample")

        status, related_payload = route_request(repo, "GET", "/api/wiki/related/source-sample")
        self.assertEqual(status, 200)
        related_stems = [item["stem"] for item in related_payload["related_pages"]]
        self.assertIn("concept-sample", related_stems)
        self.assertIn("analysis-sample", related_stems)

    def test_review_summary_surfaces_operator_triage(self) -> None:
        repo = WorkbenchRepository(self.root)

        status, payload = route_request(repo, "GET", "/api/workbench/review?limit=5")
        self.assertEqual(status, 200)
        self.assertTrue(payload["low_coverage_pages"])
        self.assertTrue(payload["uncertainty_candidates"])
        self.assertTrue(payload["stale_pages"])
        self.assertTrue(payload["low_confidence_claims"])
        self.assertEqual(payload["low_coverage_pages"][0]["stem"], "concept-sample")
        stale_stems = [item["stem"] for item in payload["stale_pages"]]
        self.assertIn("analysis-sample", stale_stems)
        self.assertEqual(payload["low_confidence_claims"][0]["claim_id"], "claim-sample")
        self.assertEqual(payload["low_confidence_claims"][0]["source_page"], "source-sample")

    def test_query_preview_returns_related_pages_and_provenance(self) -> None:
        repo = WorkbenchRepository(self.root)

        status, payload = route_request(repo, "GET", "/api/query/preview?q=sample%20durability")
        self.assertEqual(status, 200)
        self.assertEqual(payload["coverage"], "supported")
        self.assertTrue(payload["related_pages"])
        self.assertTrue(payload["related_sources"])
        self.assertIn("Local query preview", payload["answer_markdown"])
        self.assertIn("## Draft answer", payload["answer_markdown"])
        registry_labels = [section["label"] for section in payload["provenance_sections"]]
        self.assertIn("Wiki pages", registry_labels)
        self.assertNotIn("thin-coverage answer draft", payload["answer_markdown"])

    def test_query_preview_thin_coverage_is_explicit(self) -> None:
        repo = WorkbenchRepository(self.root)

        status, payload = route_request(repo, "GET", "/api/query/preview?q=covers")
        self.assertEqual(status, 200)
        self.assertEqual(payload["coverage"], "thin")
        self.assertIn("thin-coverage answer draft", payload["answer_markdown"])
        self.assertIn("thin coverage", payload["warnings"][0].replace("_", " "))

    def test_query_preview_none_coverage_refuses_smart_answer(self) -> None:
        repo = WorkbenchRepository(self.root)

        status, payload = route_request(repo, "GET", "/api/query/preview?q=totallyunknownterm")
        self.assertEqual(status, 200)
        self.assertEqual(payload["coverage"], "none")
        self.assertIn("does not currently have enough direct evidence", payload["answer_markdown"])
        self.assertIn("no_direct_matches", payload["warnings"])

    def test_save_analysis_writes_only_allowed_files(self) -> None:
        repo = WorkbenchRepository(self.root)
        raw_before = (self.root / "raw" / "inbox" / "sample.md").read_text(encoding="utf-8")
        documents_before = (self.root / "warehouse" / "jsonl" / "documents.jsonl").read_text(encoding="utf-8")

        status, payload = route_request(
            repo,
            "POST",
            "/api/actions/save-analysis",
            body_text=json.dumps({"question": "sample durability"}),
        )

        self.assertEqual(status, 200)
        self.assertIn(payload["analysis_path"], payload["changed_files"])
        self.assertIn("wiki/_meta/log.md", payload["changed_files"])
        self.assertIn("wiki/_meta/index.md", payload["changed_files"])
        self.assertIn("wiki/sources/source-sample.md", payload["linked_pages"])
        self.assertIn("wiki/concepts/concept-sample.md", payload["linked_pages"])
        analysis_path = self.root / payload["analysis_path"]
        self.assertTrue(analysis_path.exists())
        analysis_text = analysis_path.read_text(encoding="utf-8")
        self.assertIn("coverage:", analysis_text)
        self.assertIn("## Query", analysis_text)
        log_text = (self.root / "wiki" / "_meta" / "log.md").read_text(encoding="utf-8")
        self.assertIn("Saved analysis page", log_text)
        index_text = (self.root / "wiki" / "_meta" / "index.md").read_text(encoding="utf-8")
        self.assertIn(payload["analysis_stem"], index_text)
        source_text = (self.root / "wiki" / "sources" / "source-sample.md").read_text(encoding="utf-8")
        concept_text = (self.root / "wiki" / "concepts" / "concept-sample.md").read_text(encoding="utf-8")
        self.assertIn(payload["analysis_stem"], source_text)
        self.assertIn(payload["analysis_stem"], concept_text)

    def test_save_analysis_is_idempotent_on_repeat(self) -> None:
        repo = WorkbenchRepository(self.root)

        status, first_payload = route_request(
            repo,
            "POST",
            "/api/actions/save-analysis",
            body_text=json.dumps({"question": "sample durability"}),
        )
        self.assertEqual(status, 200)
        first_log = (self.root / "wiki" / "_meta" / "log.md").read_text(encoding="utf-8")
        first_index = (self.root / "wiki" / "_meta" / "index.md").read_text(encoding="utf-8")
        first_analysis = (self.root / first_payload["analysis_path"]).read_text(encoding="utf-8")

        status, second_payload = route_request(
            repo,
            "POST",
            "/api/actions/save-analysis",
            body_text=json.dumps({"question": "sample durability"}),
        )
        self.assertEqual(status, 200)
        self.assertEqual(second_payload["changed_files"], [])
        self.assertEqual((self.root / "wiki" / "_meta" / "log.md").read_text(encoding="utf-8"), first_log)
        self.assertEqual((self.root / "wiki" / "_meta" / "index.md").read_text(encoding="utf-8"), first_index)
        self.assertEqual((self.root / first_payload["analysis_path"]).read_text(encoding="utf-8"), first_analysis)

    def test_review_claim_updates_canonical_registry_and_log(self) -> None:
        repo = WorkbenchRepository(self.root)
        raw_before = (self.root / "raw" / "inbox" / "sample.md").read_text(encoding="utf-8")
        documents_before = (self.root / "warehouse" / "jsonl" / "documents.jsonl").read_text(encoding="utf-8")

        status, payload = route_request(
            repo,
            "POST",
            "/api/actions/review-claim",
            body_text=json.dumps({"claim_id": "claim-sample", "review_state": "approved"}),
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["review_state"], "approved")
        self.assertEqual(payload["changed_files"], ["warehouse/jsonl/claims.jsonl", "wiki/_meta/log.md"])
        claims_rows = read_jsonl(self.root / "warehouse" / "jsonl" / "claims.jsonl")
        updated = next(row for row in claims_rows if row["claim_id"] == "claim-sample")
        self.assertEqual(updated["review_state"], "approved")
        self.assertEqual(updated["reviewed_via"], "workbench-review")
        log_text = (self.root / "wiki" / "_meta" / "log.md").read_text(encoding="utf-8")
        self.assertIn("claim review claim-sample", log_text)
        self.assertEqual((self.root / "raw" / "inbox" / "sample.md").read_text(encoding="utf-8"), raw_before)
        self.assertEqual(
            (self.root / "warehouse" / "jsonl" / "documents.jsonl").read_text(encoding="utf-8"),
            documents_before,
        )
        status, source_payload = route_request(repo, "GET", "/api/sources/source-sample")
        self.assertEqual(status, 200)
        self.assertEqual(source_payload["coverage"]["approved_claim_count"], 1)
        self.assertEqual(source_payload["coverage"]["pending_claim_count"], 0)
        self.assertEqual(source_payload["review_queue"], [])
        status, review_payload = route_request(repo, "GET", "/api/workbench/review?limit=5")
        self.assertEqual(status, 200)
        self.assertEqual(review_payload["low_confidence_claims"], [])
        status, query_payload = route_request(repo, "GET", "/api/query/preview?q=sample%20durability")
        self.assertEqual(status, 200)
        self.assertIn("approved `1`, needs_review `0`", query_payload["answer_markdown"])

    def test_review_claim_is_idempotent_when_state_already_matches(self) -> None:
        repo = WorkbenchRepository(self.root)
        route_request(
            repo,
            "POST",
            "/api/actions/review-claim",
            body_text=json.dumps({"claim_id": "claim-sample", "review_state": "approved"}),
        )
        log_before = (self.root / "wiki" / "_meta" / "log.md").read_text(encoding="utf-8")
        status, payload = route_request(
            repo,
            "POST",
            "/api/actions/review-claim",
            body_text=json.dumps({"claim_id": "claim-sample", "review_state": "approved"}),
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["changed_files"], [])
        self.assertEqual((self.root / "wiki" / "_meta" / "log.md").read_text(encoding="utf-8"), log_before)

    def test_save_analysis_requires_question(self) -> None:
        repo = WorkbenchRepository(self.root)

        status, payload = route_request(
            repo,
            "POST",
            "/api/actions/save-analysis",
            body_text=json.dumps({"question": "   "}),
        )

        self.assertEqual(status, 400)
        self.assertIn("question is required", payload["error"])

    def test_unknown_route_and_method_return_errors(self) -> None:
        repo = WorkbenchRepository(self.root)

        status, payload = route_request(repo, "GET", "/api/unknown")
        self.assertEqual(status, 404)
        self.assertIn("Unknown route", payload["error"])

        status, payload = route_request(repo, "POST", "/api/workbench/summary")
        self.assertEqual(status, 405)
        self.assertEqual(payload["error"], "Method not allowed")

    @patch("scripts.workbench_api.subprocess.run")
    def test_post_action_returns_structured_lint_summary(self, mock_run) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=ACTION_COMMANDS["lint"],
            returncode=0,
            stdout=(
                "Lint results\n"
                "Hard failures\n"
                "- Broken wikilinks: 0\n"
                "- Missing frontmatter: 1\n"
                "Advisory warnings\n"
                "- Orphan pages: 2\n"
                "- Duplicate titles: 0\n"
            ),
            stderr="",
        )

        status, payload = route_request(WorkbenchRepository(self.root), "POST", "/api/actions/lint")

        self.assertEqual(status, 200)
        self.assertEqual(payload["command"], "python3 scripts/llm_wiki.py lint")
        self.assertEqual(payload["summary"]["kind"], "lint")
        self.assertEqual(payload["summary"]["hard_failures"]["missing_frontmatter"], "1")
        self.assertEqual(payload["summary"]["advisory_warnings"]["orphan_pages"], "2")
        mock_run.assert_called_once_with(
            ACTION_COMMANDS["lint"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_unknown_action_returns_error(self) -> None:
        status, payload = route_request(WorkbenchRepository(self.root), "POST", "/api/actions/unknown")

        self.assertEqual(status, 400)
        self.assertIn("Unknown action", payload["error"])

    def test_continue_config_loader_is_root_only(self) -> None:
        parent_config = self.root.parent / "wikiconfig.json"
        original_parent = parent_config.read_text(encoding="utf-8") if parent_config.exists() else None
        parent_config.write_text('{"models":[{"provider":"openai","model":"x","apiKey":"k","apiBase":"https://example.com"}]}', encoding="utf-8")
        try:
            self.assertIsNone(load_continue_helper_config(self.root))
        finally:
            if original_parent is None:
                parent_config.unlink(missing_ok=True)
            else:
                parent_config.write_text(original_parent, encoding="utf-8")

    def test_draft_source_summary_requires_root_continue_config(self) -> None:
        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "source-sample"}),
        )

        self.assertEqual(status, 400)
        self.assertIn("wikiconfig.json", payload["error"])

    def test_draft_source_summary_respects_disabled_toggle(self) -> None:
        (self.root / "wikiconfig.json").write_text(
            json.dumps(
                {
                    "llmWiki": {
                        "enabled": False
                    }
                }
            ),
            encoding="utf-8",
        )

        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "source-sample"}),
        )

        self.assertEqual(status, 400)
        self.assertIn("llmWiki.enabled=false", payload["error"])

    def test_continue_config_rejects_non_boolean_enabled_toggle(self) -> None:
        (self.root / "wikiconfig.json").write_text(
            json.dumps(
                {
                    "llmWiki": {
                        "enabled": "yes"
                    },
                    "models": [
                        {
                            "provider": "openai",
                            "model": "cheap-model",
                            "apiKey": "super-secret",
                            "apiBase": "https://example.com/v1"
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "source-sample"}),
        )

        self.assertEqual(status, 400)
        self.assertIn("llmWiki.enabled must be a boolean", payload["error"])

    def test_draft_source_summary_rejects_malformed_continue_config(self) -> None:
        (self.root / "wikiconfig.json").write_text('{"models":"bad"}', encoding="utf-8")

        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "source-sample"}),
        )

        self.assertEqual(status, 400)
        self.assertIn("models list", payload["error"])

    def test_draft_source_summary_rejects_unsupported_provider(self) -> None:
        (self.root / "wikiconfig.json").write_text(
            json.dumps(
                {
                    "models": [
                        {
                            "provider": "anthropic",
                            "model": "claude-x",
                            "apiKey": "k",
                            "apiBase": "https://example.com",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "source-sample"}),
        )

        self.assertEqual(status, 400)
        self.assertIn("provider must be one of: openai", payload["error"])

    @patch("scripts.workbench.llm_config.request.urlopen")
    def test_draft_source_summary_returns_draft_without_secret_leakage(self, mock_urlopen) -> None:
        (self.root / "wikiconfig.json").write_text(
            json.dumps(
                {
                    "models": [
                        {
                            "title": "Cheap Helper Model",
                            "provider": "openai",
                            "model": "cheap-model",
                            "apiKey": "super-secret",
                            "apiBase": "https://example.com/v1",
                        }
                    ],
                    "unsupported": {"ignored": True},
                }
            ),
            encoding="utf-8",
        )
        mocked_response = MagicMock()
        mocked_response.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "## Draft summary\n\n- Draft only.\n"
                        }
                    }
                ]
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mocked_response

        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "source-sample", "max_chars": 2000}),
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["action"], "draft_source_summary")
        self.assertEqual(payload["changed_files"], [])
        self.assertEqual(payload["helper_model"]["config_source"], "wikiconfig.json")
        self.assertEqual(payload["helper_model"]["model_title"], "Cheap Helper Model")
        self.assertNotIn("apiKey", json.dumps(payload))
        self.assertNotIn("super-secret", json.dumps(payload))
        self.assertNotIn("apiBase", json.dumps(payload))
        self.assertIn("draft_only_output", payload["warnings"])
        self.assertIn("## Draft summary", payload["draft_markdown"])

    def test_draft_source_summary_requires_source_stem(self) -> None:
        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "   "}),
        )

        self.assertEqual(status, 400)
        self.assertIn("source_stem is required", payload["error"])

    def test_draft_source_summary_rejects_raw_path_outside_allowed_prefixes(self) -> None:
        (self.root / "wikiconfig.json").write_text(
            json.dumps(
                {
                    "models": [
                        {
                            "provider": "openai",
                            "model": "cheap-model",
                            "apiKey": "super-secret",
                            "apiBase": "https://example.com/v1",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        source_path = self.root / "wiki" / "sources" / "source-sample.md"
        source_path.write_text(
            "---\n"
            'title: "Sample Source"\n'
            "type: source\n"
            "status: active\n"
            "created: 2026-04-09\n"
            "updated: 2026-04-10\n"
            'raw_path: ".env"\n'
            "---\n\n"
            "# Sample Source\n\n"
            "A durable source page linked to [[concept-sample]] and [[analysis-sample]].\n",
            encoding="utf-8",
        )

        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "source-sample"}),
        )

        self.assertEqual(status, 400)
        self.assertIn("must stay under raw/inbox/, raw/processed/, or raw/notes/", payload["error"])

    def test_draft_source_summary_rejects_binary_source_files(self) -> None:
        (self.root / "wikiconfig.json").write_text(
            json.dumps(
                {
                    "models": [
                        {
                            "provider": "openai",
                            "model": "cheap-model",
                            "apiKey": "super-secret",
                            "apiBase": "https://example.com/v1",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        binary_path = self.root / "raw" / "inbox" / "sample.pdf"
        binary_path.write_bytes(b"%PDF-\xff\xfe\x00binary")
        source_path = self.root / "wiki" / "sources" / "source-sample.md"
        source_path.write_text(
            "---\n"
            'title: "Sample Source"\n'
            "type: source\n"
            "status: active\n"
            "created: 2026-04-09\n"
            "updated: 2026-04-10\n"
            'raw_path: "raw/inbox/sample.pdf"\n'
            "---\n\n"
            "# Sample Source\n\n"
            "A durable source page linked to [[concept-sample]] and [[analysis-sample]].\n",
            encoding="utf-8",
        )

        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "source-sample"}),
        )

        self.assertEqual(status, 400)
        self.assertIn("is not UTF-8 text", payload["error"])

    @patch("scripts.workbench.llm_config.request.urlopen")
    def test_draft_source_summary_resolves_unicode_normalized_raw_path(self, mock_urlopen) -> None:
        (self.root / "wikiconfig.json").write_text(
            json.dumps(
                {
                    "llmWiki": {"enabled": True},
                    "models": [
                        {
                            "title": "Cheap Helper Model",
                            "provider": "openai",
                            "model": "cheap-model",
                            "apiKey": "super-secret",
                            "apiBase": "https://example.com/v1",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        actual_name = "KakaoTalk_Chat_에이전트코리아_2026-04-07-00-26-26.csv"
        decomposed_name = unicodedata.normalize("NFD", actual_name)
        raw_file = self.root / "raw" / "inbox" / actual_name
        raw_file.write_text("Date,User,Message\n2026-04-07 00:00:00,tester,hello\n", encoding="utf-8")
        source_path = self.root / "wiki" / "sources" / "source-sample.md"
        source_path.write_text(
            "---\n"
            'title: "Sample Source"\n'
            "type: source\n"
            "status: active\n"
            "created: 2026-04-09\n"
            "updated: 2026-04-10\n"
            f'raw_path: "raw/inbox/{decomposed_name}"\n'
            "---\n\n"
            "# Sample Source\n\n"
            "A durable source page linked to [[concept-sample]] and [[analysis-sample]].\n",
            encoding="utf-8",
        )
        mocked_response = MagicMock()
        mocked_response.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "## Draft summary\n\n- Unicode path resolved.\n"
                        }
                    }
                ]
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mocked_response

        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "source-sample", "max_chars": 2000}),
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["raw_path"], f"raw/inbox/{decomposed_name}")
        self.assertIn("Unicode path resolved", payload["draft_markdown"])

    @patch("scripts.workbench.llm_config.request.urlopen")
    def test_draft_source_summary_resolves_broken_hangul_combining_path(self, mock_urlopen) -> None:
        (self.root / "wikiconfig.json").write_text(
            json.dumps(
                {
                    "llmWiki": {"enabled": True},
                    "models": [
                        {
                            "title": "Cheap Helper Model",
                            "provider": "openai",
                            "model": "cheap-model",
                            "apiKey": "super-secret",
                            "apiBase": "https://example.com/v1",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        actual_name = "KakaoTalk_Chat_에이전트코리아_2026-04-07-00-26-26.csv"
        broken_name = "KakaoTalk_Chat_에이전트코리ᅡ_2026-04-07-00-26-26.csv"
        raw_file = self.root / "raw" / "inbox" / actual_name
        raw_file.write_text("Date,User,Message\n2026-04-07 00:00:00,tester,hello\n", encoding="utf-8")
        source_path = self.root / "wiki" / "sources" / "source-sample.md"
        source_path.write_text(
            "---\n"
            'title: "Sample Source"\n'
            "type: source\n"
            "status: active\n"
            "created: 2026-04-09\n"
            "updated: 2026-04-10\n"
            f'raw_path: "raw/inbox/{broken_name}"\n'
            "---\n\n"
            "# Sample Source\n\n"
            "A durable source page linked to [[concept-sample]] and [[analysis-sample]].\n",
            encoding="utf-8",
        )
        mocked_response = MagicMock()
        mocked_response.read.return_value = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "## Draft summary\n\n- Broken Hangul path resolved.\n"
                        }
                    }
                ]
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mocked_response

        status, payload = route_request(
            WorkbenchRepository(self.root),
            "POST",
            "/api/actions/draft-source-summary",
            body_text=json.dumps({"source_stem": "source-sample", "max_chars": 2000}),
        )

        self.assertEqual(status, 200)
        self.assertEqual(payload["raw_path"], f"raw/inbox/{broken_name}")
        self.assertIn("Broken Hangul path resolved", payload["draft_markdown"])


if __name__ == "__main__":
    unittest.main()
