from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "scripts" / "helper_llm.py"
FULL_INGEST_PATH = ROOT / "scripts" / "llm_full_ingest.py"
BOOTSTRAP_PATH = ROOT / ".agents" / "skills" / "llm-wiki-bootstrap" / "scripts" / "bootstrap_llm_wiki.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class HelperLLMRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.helper = load_module(HELPER_PATH, "helper_llm_under_test")
        cls.full_ingest = load_module(FULL_INGEST_PATH, "llm_full_ingest_under_test")
        cls.bootstrap = load_module(BOOTSTRAP_PATH, "bootstrap_llm_wiki_for_full_ingest_test")

    def test_check_config_fails_when_wikiconfig_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = self.helper.main(["--root", str(root), "--check-config"])

        self.assertEqual(code, 1)

    def test_optional_placeholder_providers_do_not_break_chat_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")
            (root / "wikiconfig.json").write_text(
                json.dumps(
                    {
                        "models": [
                            {
                                "provider": "openai",
                                "model": "test-chat-model",
                                "apiKey": "real-looking-key",
                                "apiBase": "https://example.test/v1",
                            }
                        ],
                        "embeddingsProvider": {
                            "provider": "openai",
                            "model": "YOUR_EMBED_MODEL",
                            "apiKey": "YOUR_API_KEY",
                            "apiBase": "YOUR_API_BASE",
                        },
                        "rerankerProvider": {
                            "provider": "openai",
                            "model": "BAAI/bge-reranker-v2-m3",
                            "apiKey": "YOUR_API_KEY",
                            "apiBase": "YOUR_RERANKER_API_ENDPOINT_IF_ANY",
                        },
                    }
                ),
                encoding="utf-8",
            )

            config = self.helper.load_helper_config(root)

        self.assertTrue(config.enabled)
        self.assertIsNotNone(config.chat_model)
        self.assertIsNone(config.embeddings_provider)
        self.assertIsNone(config.reranker_provider)
        self.assertGreaterEqual(len(config.warnings), 2)

    def test_endpoint_join_does_not_duplicate_suffix(self) -> None:
        endpoint = self.helper.endpoint

        self.assertEqual(endpoint("https://example.test/v1", "chat/completions"), "https://example.test/v1/chat/completions")
        self.assertEqual(
            endpoint("https://example.test/v1/chat/completions", "chat/completions"),
            "https://example.test/v1/chat/completions",
        )

    def test_replace_section_preserves_backslashes_in_body(self) -> None:
        markdown = "## Summary\n\nTBD.\n\n## Key Facts\n\n- TBD\n"
        body = r"Path C:\\temp\\1 and regex \\1 should stay literal."

        updated = self.full_ingest.replace_section(markdown, "Summary", body)

        self.assertIn(body, updated)
        self.assertIn("## Key Facts", updated)

    def test_build_source_page_content_updates_frontmatter_and_sections(self) -> None:
        source_page = """---
title: "Example"
type: source
status: inbox
created: 2026-05-01
updated: 2026-05-01
raw_path: "raw/inbox/example.md"
---

# Example

## Summary

TBD.

## Key Facts

- TBD

## Important Claims

- TBD

## Contradictions Or Uncertainty

- TBD

## Open Questions

- TBD

## Affected Pages

- TBD
"""
        draft = {
            "summary": "A source-backed summary.",
            "key_facts": ["Fact one."],
            "important_claims": [{"claim_text": "Claim one.", "status": "proposed"}],
            "uncertainties": ["Unclear point."],
            "open_questions": ["Question one?"],
            "affected_pages": [{"page": "[[example]]", "action": "source_page_only", "reason": "weak signal"}],
        }

        updated = self.full_ingest.build_source_page_content(source_page, draft)

        self.assertIn("status: pending-wiki-projection", updated)
        self.assertIn(f"updated: {self.full_ingest.today()}", updated)
        self.assertIn("A source-backed summary.", updated)
        self.assertNotIn("TBD", updated)

    def test_apply_validation_rejects_non_proposed_claims(self) -> None:
        validation = self.full_ingest.validate_draft(
            {"summary": "ok", "important_claims": [{"claim_text": "bad", "status": "accepted"}]},
            "no TBD here",
        )

        with self.assertRaises(RuntimeError):
            self.full_ingest.assert_apply_safe(validation)

    def test_apply_validation_rejects_accepted_proposed_jsonl_records(self) -> None:
        validation = self.full_ingest.validate_draft(
            {
                "summary": "ok",
                "important_claims": [],
                "proposed_entities": [{"name": "bad", "status": "accepted"}],
            },
            "no TBD here",
        )

        with self.assertRaises(RuntimeError):
            self.full_ingest.assert_apply_safe(validation)

    def test_apply_validation_rejects_forbidden_affected_page_actions(self) -> None:
        validation = self.full_ingest.validate_draft(
            {
                "summary": "ok",
                "important_claims": [],
                "affected_page_updates": [
                    {"path": "wiki/concepts/bad.md", "action": "delete"}
                ],
            },
            "no TBD here",
        )

        with self.assertRaises(RuntimeError):
            self.full_ingest.assert_apply_safe(validation)

    def test_affected_page_update_contract_allows_only_create_or_append(self) -> None:
        with self.assertRaises(RuntimeError):
            self.full_ingest.validate_affected_update_action(
                {"path": "wiki/concepts/bad.md", "action": "update"}
            )
        with self.assertRaises(RuntimeError):
            self.full_ingest.validate_affected_update_action(
                {"path": "wiki/concepts/bad.md", "action": "create_or_append"}
            )

    def test_reserved_apply_modes_fail_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Test\n", encoding="utf-8")
            source = root / "raw" / "inbox" / "example.md"
            source.parent.mkdir(parents=True)
            source.write_text("hello", encoding="utf-8")

            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = self.full_ingest.main([str(source), "--root", str(root), "--mode", "apply_wiki"])

        self.assertEqual(code, 2)

    def test_apply_closes_full_growth_report_index_log_loop(self) -> None:
        original_load_config = self.full_ingest.load_helper_config
        original_chat_completion = self.full_ingest.chat_completion
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "vault"
                self.bootstrap.scaffold(root, force=False, profile="wiki-plus-ontology")
                source = root / "raw" / "inbox" / "example.md"
                source.write_text("# Example\n\n라텔은 벌꿀오소리다.\n", encoding="utf-8")

                fake_model = self.helper.ModelConfig(
                    provider="openai",
                    model="fake-model",
                    api_key="fake-key",
                    api_base="https://example.test/v1",
                )
                fake_config = self.helper.HelperLLMConfig(
                    source_path="wikiconfig.json",
                    enabled=True,
                    chat_model=fake_model,
                    embeddings_provider=None,
                    reranker_provider=None,
                    warnings=(),
                )

                def fake_load_config(_root: Path, _explicit_config: str | None = None):
                    return fake_config

                def fake_chat_completion(*_args, **_kwargs):
                    return json.dumps(
                        {
                            "summary": "라텔 관련 source-backed 요약입니다.",
                            "key_facts": ["라텔은 벌꿀오소리로 언급된다."],
                            "important_claims": [
                                {
                                    "claim_text": "라텔은 벌꿀오소리다.",
                                    "status": "proposed",
                                    "extractor_confidence": "medium",
                                    "evidence_excerpt": "라텔은 벌꿀오소리다.",
                                }
                            ],
                            "uncertainties": ["source 맥락이 짧다."],
                            "open_questions": ["라텔이 왜 중요한가?"],
                            "affected_pages": [
                                {
                                    "page": "wiki/concepts/라텔.md",
                                    "action": "create_candidate",
                                    "reason": "source의 중심 대상",
                                    "confidence": "medium",
                                }
                            ],
                            "affected_page_updates": [
                                {
                                    "path": "wiki/concepts/라텔.md",
                                    "title": "라텔",
                                    "type": "concept",
                                    "action": "create",
                                    "reason": "source의 중심 대상",
                                    "summary_append": "라텔은 이 source에서 벌꿀오소리로 설명된다.",
                                    "key_points": ["벌꿀오소리 언급이 source-backed claim으로 남는다."],
                                    "evidence_timeline": [
                                        {
                                            "date": "unknown",
                                            "text": "라텔이 벌꿀오소리로 언급됨.",
                                            "evidence_excerpt": "라텔은 벌꿀오소리다.",
                                        }
                                    ],
                                    "open_questions": ["라텔의 선호 생물과 연결되는가?"],
                                }
                            ],
                            "proposed_entities": [
                                {
                                    "name": "라텔",
                                    "type": "animal_or_character",
                                    "status": "proposed",
                                    "review_state": "needs_review",
                                    "evidence_excerpt": "라텔은 벌꿀오소리다.",
                                }
                            ],
                            "proposed_claims": [
                                {
                                    "claim_text": "라텔은 벌꿀오소리다.",
                                    "status": "proposed",
                                    "review_state": "needs_review",
                                    "confidence": "medium",
                                    "evidence_excerpt": "라텔은 벌꿀오소리다.",
                                }
                            ],
                            "proposed_evidence": [
                                {
                                    "evidence_text": "라텔은 벌꿀오소리다.",
                                    "status": "proposed",
                                    "review_state": "needs_review",
                                    "evidence_excerpt": "라텔은 벌꿀오소리다.",
                                }
                            ],
                            "completion_notes": ["full apply"],
                        },
                        ensure_ascii=False,
                    )

                self.full_ingest.load_helper_config = fake_load_config
                self.full_ingest.chat_completion = fake_chat_completion

                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    code = self.full_ingest.main(
                        [
                            "raw/inbox/example.md",
                            "--root",
                            str(root),
                            "--apply",
                            "--title",
                            "라텔 예시",
                        ]
                    )

                self.assertEqual(code, 0)
                source_pages = list((root / "wiki" / "sources").glob("source-*-라텔-예시.md"))
                self.assertEqual(len(source_pages), 1)
                source_text = source_pages[0].read_text(encoding="utf-8")
                self.assertIn("status: growth-applied", source_text)
                self.assertIn("라텔 관련 source-backed 요약입니다.", source_text)
                self.assertNotIn("TBD", source_text)

                concept_page = root / "wiki" / "concepts" / "라텔.md"
                self.assertTrue(concept_page.exists())
                concept_text = concept_page.read_text(encoding="utf-8")
                self.assertIn("라텔은 이 source에서 벌꿀오소리로 설명된다.", concept_text)
                self.assertIn(f"[[{source_pages[0].stem}]]", concept_text)

                proposed_claims = root / "warehouse" / "jsonl" / "proposed_claims.jsonl"
                self.assertTrue(proposed_claims.exists())
                proposed_text = proposed_claims.read_text(encoding="utf-8")
                self.assertIn('"status": "proposed"', proposed_text)
                self.assertIn('"review_state": "needs_review"', proposed_text)
                self.assertNotIn('"accepted"', proposed_text)

                reports = list((root / "wiki" / "_meta" / "ingest_reports").glob("ingest-*.md"))
                self.assertEqual(len(reports), 1)
                report_text = reports[0].read_text(encoding="utf-8")
                self.assertIn("## Applied Affected Pages", report_text)
                self.assertIn("Review the automatic growth with `git diff`", report_text)
                index_text = (root / "wiki" / "_meta" / "index.md").read_text(encoding="utf-8")
                self.assertIn(f"[[{reports[0].stem}]]", index_text)
                log_text = (root / "wiki" / "_meta" / "log.md").read_text(encoding="utf-8")
                self.assertIn("Full ingest apply", log_text)
        finally:
            self.full_ingest.load_helper_config = original_load_config
            self.full_ingest.chat_completion = original_chat_completion


if __name__ == "__main__":
    unittest.main()
