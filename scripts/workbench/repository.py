#!/usr/bin/env python3
"""Repository-facing read and bounded-write operations for the workbench."""

from __future__ import annotations

import datetime as dt
import difflib
import json
import subprocess
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from workbench.common import (
        ACTION_COMMANDS,
        JSONL_REGISTRIES,
        REVIEW_STATE_ACTIVE,
        REVIEW_STATE_PENDING,
        REVIEW_STATE_REJECTED,
        append_bullet_to_section,
        count_non_placeholder_files,
        days_since_iso,
        default_incremental_registry_paths,
        default_incremental_wiki_paths,
        ensure_allowed_write_paths,
        extract_summary,
        flatten_row_text,
        parse_frontmatter,
        parse_index_sections,
        parse_log_entries,
        read_jsonl,
        read_text,
        safe_iso_date,
        slugify,
        strip_markdown,
        summarize_action_output,
        tokenize_query,
        update_frontmatter_date,
        wikilinks,
        write_jsonl,
    )
except ModuleNotFoundError:
    from scripts.workbench.common import (
        ACTION_COMMANDS,
        JSONL_REGISTRIES,
        REVIEW_STATE_ACTIVE,
        REVIEW_STATE_PENDING,
        REVIEW_STATE_REJECTED,
        append_bullet_to_section,
        count_non_placeholder_files,
        days_since_iso,
        default_incremental_registry_paths,
        default_incremental_wiki_paths,
        ensure_allowed_write_paths,
        extract_summary,
        flatten_row_text,
        parse_frontmatter,
        parse_index_sections,
        parse_log_entries,
        read_jsonl,
        read_text,
        safe_iso_date,
        slugify,
        strip_markdown,
        summarize_action_output,
        tokenize_query,
        update_frontmatter_date,
        wikilinks,
        write_jsonl,
    )
    from scripts.workbench.llm_config import (
        helper_model_public_summary,
        load_continue_helper_config,
        run_helper_chat_completion,
    )
else:
    from workbench.llm_config import (
        helper_model_public_summary,
        load_continue_helper_config,
        run_helper_chat_completion,
    )

@dataclass
class WorkbenchRepository:
    root: Path
    _graph_nodes_cache: list[dict[str, Any]] | None = field(default=None, init=False, repr=False)
    _graph_edges_cache: list[dict[str, Any]] | None = field(default=None, init=False, repr=False)
    _graph_nodes_signature: tuple[int, int] | None = field(default=None, init=False, repr=False)
    _graph_edges_signature: tuple[int, int] | None = field(default=None, init=False, repr=False)

    @property
    def raw_dir(self) -> Path:
        return self.root / "raw"

    @property
    def wiki_dir(self) -> Path:
        return self.root / "wiki"

    @property
    def meta_dir(self) -> Path:
        return self.wiki_dir / "_meta"

    @property
    def sources_dir(self) -> Path:
        return self.wiki_dir / "sources"

    @property
    def warehouse_jsonl_dir(self) -> Path:
        return self.root / "warehouse" / "jsonl"

    @property
    def graph_dir(self) -> Path:
        return self.root / "warehouse" / "graph_projection"

    def iter_markdown_pages(self) -> list[Path]:
        if not self.wiki_dir.exists():
            return []
        return sorted(path for path in self.wiki_dir.rglob("*.md") if path.is_file())

    def page_lookup(self) -> dict[str, Path]:
        return {path.stem: path for path in self.iter_markdown_pages()}

    def load_helper_model_config(self) -> dict[str, Any]:
        config = load_continue_helper_config(self.root)
        if config is None:
            raise ValueError("wikiconfig.json was not found at the repo root")
        if not config.get("enabled", True):
            raise ValueError("helper model is disabled in wikiconfig.json (llmWiki.enabled=false)")
        return config

    def normalized_filename_keys(self, value: str) -> set[str]:
        nfc = unicodedata.normalize("NFC", value)
        nfd = unicodedata.normalize("NFD", value)
        stripped = "".join(char for char in nfd if unicodedata.category(char) != "Mn")
        return {nfc, nfd, stripped}

    def resolve_allowed_raw_source_path(self, raw_path_value: str, source_stem: str) -> Path:
        normalized_raw_path = raw_path_value.strip()
        if not normalized_raw_path:
            raise ValueError(f"Source page `{source_stem}` does not declare raw_path")
        allowed_prefixes = ("raw/inbox/", "raw/processed/", "raw/notes/")
        if not normalized_raw_path.startswith(allowed_prefixes):
            raise ValueError(
                f"raw_path for `{source_stem}` must stay under raw/inbox/, raw/processed/, or raw/notes/"
            )

        raw_path = (self.root / normalized_raw_path).resolve()
        resolved_root = self.root.resolve()
        if resolved_root not in raw_path.parents and raw_path != resolved_root:
            raise ValueError(f"raw_path for `{source_stem}` points outside the repo")
        if not raw_path.exists():
            parent = raw_path.parent
            target_name_keys = self.normalized_filename_keys(raw_path.name)
            if parent.exists():
                fuzzy_candidates: list[tuple[float, Path]] = []
                for candidate in parent.iterdir():
                    if not candidate.is_file():
                        continue
                    candidate_name_keys = self.normalized_filename_keys(candidate.name)
                    if target_name_keys.intersection(candidate_name_keys):
                        return candidate.resolve()
                    if candidate.suffix == raw_path.suffix:
                        similarity = max(
                            difflib.SequenceMatcher(None, left, right).ratio()
                            for left in target_name_keys
                            for right in candidate_name_keys
                        )
                        if similarity >= 0.95:
                            fuzzy_candidates.append((similarity, candidate.resolve()))
                if len(fuzzy_candidates) == 1:
                    return fuzzy_candidates[0][1]
            raise ValueError(f"Raw source file not found: {normalized_raw_path}")
        return raw_path

    def page_record(self, path: Path) -> dict[str, Any]:
        text = read_text(path)
        frontmatter, body = parse_frontmatter(text)
        rel = path.relative_to(self.root)
        section = path.relative_to(self.wiki_dir).parts[0]
        title = str(frontmatter.get("title") or path.stem.replace("-", " ").title())
        updated = safe_iso_date(frontmatter.get("updated")) or safe_iso_date(frontmatter.get("created"))
        links = sorted(set(wikilinks(text)))
        return {
            "stem": path.stem,
            "path": str(rel),
            "section": section,
            "title": title,
            "summary": extract_summary(text),
            "frontmatter": frontmatter,
            "body": body,
            "links": links,
            "updated": updated,
        }

    def all_page_records(self) -> list[dict[str, Any]]:
        return [self.page_record(path) for path in self.iter_markdown_pages()]

    def related_pages_for_stem(self, stem: str, limit: int = 6) -> list[dict[str, Any]]:
        records = self.all_page_records()
        lookup = {record["stem"]: record for record in records}
        if stem not in lookup:
            raise FileNotFoundError(f"Page not found: {stem}")

        target = lookup[stem]
        direct_links = set(target["links"])
        related: dict[str, dict[str, Any]] = {}
        for candidate in records:
            if candidate["stem"] == stem:
                continue
            score = 0
            reasons: list[str] = []
            candidate_links = set(candidate["links"])
            shared_links = sorted(direct_links.intersection(candidate_links))
            if stem in candidate_links:
                score += 3
                reasons.append("links_back")
            if candidate["stem"] in direct_links:
                score += 3
                reasons.append("linked_from_target")
            if shared_links:
                score += min(2, len(shared_links))
                reasons.append("shared_links")
            if candidate["section"] == target["section"]:
                score += 1
                reasons.append("same_section")
            if score <= 0:
                continue
            related[candidate["stem"]] = {
                "stem": candidate["stem"],
                "title": candidate["title"],
                "section": candidate["section"],
                "summary": candidate["summary"],
                "score": score,
                "reasons": reasons,
            }

        return sorted(
            related.values(),
            key=lambda item: (-int(item["score"]), str(item["title"]).lower()),
        )[:limit]

    def workbench_feed(self, limit: int = 5) -> dict[str, Any]:
        records = self.all_page_records()
        sources = [record for record in records if record["section"] == "sources"]
        analyses = [record for record in records if record["section"] == "analyses"]

        def top(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
            ranked = sorted(
                items,
                key=lambda item: (item["updated"], item["title"].lower()),
                reverse=True,
            )[:limit]
            return [
                {
                    "stem": item["stem"],
                    "title": item["title"],
                    "summary": item["summary"],
                    "updated": item["updated"] or None,
                    "path": item["path"],
                }
                for item in ranked
            ]

        return {
            "recent_sources": top(sources),
            "recent_analyses": top(analyses),
        }

    @staticmethod
    def _claim_semantics_summary(claims: list[dict[str, Any]]) -> dict[str, Any]:
        support_status_counts = Counter(str(row.get("support_status") or "unknown") for row in claims)
        truth_basis_counts = Counter(str(row.get("truth_basis") or "unknown") for row in claims)
        lifecycle_state_counts = Counter(str(row.get("lifecycle_state") or "unknown") for row in claims)
        temporal_scope_counts = Counter(str(row.get("temporal_scope") or "unknown") for row in claims)
        dominant_scope = temporal_scope_counts.most_common(1)[0][0] if temporal_scope_counts else None
        return {
            "claim_count": len(claims),
            "support_status_counts": dict(sorted(support_status_counts.items())),
            "truth_basis_counts": dict(sorted(truth_basis_counts.items())),
            "lifecycle_state_counts": dict(sorted(lifecycle_state_counts.items())),
            "temporal_scope_counts": dict(sorted(temporal_scope_counts.items())),
            "dominant_scope": dominant_scope,
        }

    @staticmethod
    def _save_readiness_from_claim_semantics(coverage: str, claim_semantics: dict[str, Any]) -> tuple[str, str]:
        if coverage == "none":
            return (
                "blocked",
                "Refine the query before saving because the workspace does not yet have direct enough evidence.",
            )
        support_counts = claim_semantics.get("support_status_counts") or {}
        claim_count = int(claim_semantics.get("claim_count") or 0)
        disputed_count = int(support_counts.get("disputed", 0))
        provisional_count = int(support_counts.get("provisional", 0))
        supported_count = int(support_counts.get("supported", 0))
        rejected_count = int(support_counts.get("rejected", 0))
        if disputed_count > 0:
            return (
                "review_required",
                "Claim support status includes disputed evidence. Resolve the disputed claim set before saving.",
            )
        if provisional_count > 0:
            return (
                "review_required",
                "Claim support status is still provisional. Review the in-scope evidence before saving.",
            )
        if coverage == "supported" and claim_count > 0 and supported_count > 0 and rejected_count == 0:
            return (
                "ready",
                "Evidence is broad enough to save after a final human review.",
            )
        return (
            "review_required",
            "Inspect the evidence and related pages before saving this thin-coverage draft.",
        )

    @staticmethod
    def _derived_claim_state(review_state: str, contradiction_candidate: bool) -> tuple[str, str]:
        normalized_state = review_state.strip().lower()
        if normalized_state == REVIEW_STATE_REJECTED:
            return "rejected", "rejected"
        if contradiction_candidate:
            return "disputed", "contested"
        if normalized_state == REVIEW_STATE_ACTIVE:
            return "supported", "active"
        return "provisional", "draft"

    def review_summary(self, limit: int = 5) -> dict[str, Any]:
        records = self.all_page_records()
        documents_by_id = {
            row.get("document_id"): row
            for row in read_jsonl(self.warehouse_jsonl_dir / "documents.jsonl")
        }
        entity_rows = read_jsonl(self.warehouse_jsonl_dir / "entities.jsonl")
        oversized: list[dict[str, Any]] = []
        low_coverage: list[dict[str, Any]] = []
        uncertainty: list[dict[str, Any]] = []
        stale: list[dict[str, Any]] = []
        low_confidence_claims: list[dict[str, Any]] = []
        contradiction_candidates: list[dict[str, Any]] = []
        merge_candidates: list[dict[str, Any]] = []
        for claim in read_jsonl(self.warehouse_jsonl_dir / "claims.jsonl"):
            confidence = claim.get("confidence")
            review_state = str(claim.get("review_state") or "unknown")
            needs_review = review_state == REVIEW_STATE_PENDING
            confidence_value = float(confidence) if isinstance(confidence, (int, float)) else None
            if not needs_review:
                continue
            low_confidence_claims.append(
                {
                    "claim_id": claim.get("claim_id"),
                    "document_id": claim.get("document_id") or claim.get("source_document_id"),
                    "source_page": documents_by_id.get(
                        claim.get("document_id") or claim.get("source_document_id"),
                        {},
                    ).get("source_page"),
                    "subject_id": claim.get("subject_id"),
                    "review_state": review_state,
                    "confidence": confidence_value,
                    "support_status": claim.get("support_status"),
                    "truth_basis": claim.get("truth_basis"),
                    "lifecycle_state": claim.get("lifecycle_state"),
                    "temporal_scope": claim.get("temporal_scope"),
                    "evidence_count": claim.get("evidence_count"),
                    "claim_text": claim.get("claim_text"),
                }
            )
            if claim.get("contradiction_candidate"):
                contradiction_candidates.append(
                    {
                        "claim_id": claim.get("claim_id"),
                        "document_id": claim.get("document_id") or claim.get("source_document_id"),
                        "source_page": documents_by_id.get(
                            claim.get("document_id") or claim.get("source_document_id"),
                            {},
                        ).get("source_page"),
                        "subject_id": claim.get("subject_id"),
                        "confidence": confidence_value,
                        "support_status": claim.get("support_status"),
                        "truth_basis": claim.get("truth_basis"),
                        "lifecycle_state": claim.get("lifecycle_state"),
                        "temporal_scope": claim.get("temporal_scope"),
                        "claim_text": claim.get("claim_text"),
                    }
                )

        for entity in entity_rows:
            aliases = entity.get("aliases") or []
            if entity.get("merge_candidate") or len(aliases) > 1:
                merge_candidates.append(
                    {
                        "entity_id": entity.get("entity_id"),
                        "label": entity.get("label") or entity.get("canonical_name"),
                        "alias_count": len(aliases),
                        "aliases": aliases,
                        "source_pages": entity.get("source_pages") or [],
                    }
                )

        for record in records:
            line_count = len(record["body"].splitlines())
            if record["section"] != "_meta" and line_count > 200:
                oversized.append(
                    {
                        "stem": record["stem"],
                        "title": record["title"],
                        "section": record["section"],
                        "line_count": line_count,
                    }
                )

            sources_value = record["frontmatter"].get("sources")
            source_count = len(sources_value) if isinstance(sources_value, list) else 0
            if record["section"] in {"concepts", "entities", "people", "projects", "timelines"} and source_count == 0:
                low_coverage.append(
                    {
                        "stem": record["stem"],
                        "title": record["title"],
                        "section": record["section"],
                        "reason": "missing_sources_frontmatter",
                    }
                )

            body_lower = record["body"].lower()
            if record["section"] != "_meta" and any(
                token in body_lower for token in ["uncertain", "contradiction", "disputed", "pending", "open question"]
            ):
                uncertainty.append(
                    {
                        "stem": record["stem"],
                        "title": record["title"],
                        "section": record["section"],
                    }
                )

            age_days = days_since_iso(record["updated"])
            if record["section"] != "_meta" and (age_days is None or age_days >= 30):
                stale.append(
                    {
                        "stem": record["stem"],
                        "title": record["title"],
                        "section": record["section"],
                        "updated": record["updated"] or None,
                        "age_days": age_days,
                    }
                )

        oversized.sort(key=lambda item: (-int(item["line_count"]), str(item["title"]).lower()))
        low_coverage.sort(key=lambda item: (str(item["section"]), str(item["title"]).lower()))
        uncertainty.sort(key=lambda item: (str(item["section"]), str(item["title"]).lower()))
        stale.sort(
            key=lambda item: (
                item["age_days"] is not None,
                int(item["age_days"] or -1),
            ),
            reverse=True,
        )
        low_confidence_claims.sort(
            key=lambda item: (
                item["review_state"] == "approved",
                float(item["confidence"] if item["confidence"] is not None else 1.0),
            )
        )
        contradiction_candidates.sort(
            key=lambda item: (
                float(item["confidence"] if item["confidence"] is not None else 1.0),
                str(item.get("claim_text") or "").lower(),
            )
        )
        merge_candidates.sort(key=lambda item: (-int(item["alias_count"]), str(item["label"]).lower()))

        low_coverage = low_coverage[:limit]
        uncertainty = uncertainty[:limit]
        stale = stale[:limit]
        low_confidence_claims = low_confidence_claims[:limit]
        contradiction_candidates = contradiction_candidates[:limit]
        merge_candidates = merge_candidates[:limit]

        for item in low_coverage:
            item["graph_hint"] = self._graph_hint_text("page", str(item["stem"]))
        for item in uncertainty:
            item["graph_hint"] = self._graph_hint_text("page", str(item["stem"]))
        for item in stale:
            item["graph_hint"] = self._graph_hint_text("page", str(item["stem"]))
        for item in low_confidence_claims:
            claim_id = str(item.get("claim_id") or "")
            item["graph_hint"] = self._graph_hint_text("claim", claim_id) or (
                self._graph_hint_text("source", str(item.get("source_page") or "")) if item.get("source_page") else None
            )
        for item in contradiction_candidates:
            claim_id = str(item.get("claim_id") or "")
            item["graph_hint"] = self._graph_hint_text("claim", claim_id) or (
                self._graph_hint_text("source", str(item.get("source_page") or "")) if item.get("source_page") else None
            )
        for item in merge_candidates:
            source_pages = item.get("source_pages") or []
            item["graph_hint"] = self._graph_hint_text("source", str(source_pages[0])) if source_pages else None

        return {
            "oversized_pages": oversized[:limit],
            "low_coverage_pages": low_coverage,
            "uncertainty_candidates": uncertainty,
            "stale_pages": stale,
            "low_confidence_claims": low_confidence_claims,
            "contradiction_candidates": contradiction_candidates,
            "merge_candidates": merge_candidates,
        }

    def query_preview(self, question: str, limit: int = 5) -> dict[str, Any]:
        tokens = tokenize_query(question)
        if not tokens:
            return {
                "mode": "repo_local_search",
                "question": question,
                "tokens": [],
                "coverage": "none",
                "answer_markdown": (
                    "# Ask workspace\n\n"
                    "Enter a more specific question to search the wiki and canonical registries.\n"
                ),
                "related_pages": [],
                "related_sources": [],
                "provenance_sections": [],
                "warnings": ["empty_query"],
                "graph_hints": {
                    "available": False,
                    "summary": "Graph hints require a non-empty query.",
                    "related_nodes": [],
                    "path_hints": [],
                    "warnings": ["empty_query"],
                    "seeds": [],
                },
                "contract": {
                    "route": "repo_local_search",
                    "truth_layers": [
                        {"name": "wiki_pages", "used": False, "count": 0},
                        {"name": "source_pages", "used": False, "count": 0},
                        {"name": "canonical_jsonl", "used": False, "count": 0},
                        {"name": "graph_projection", "used": False, "count": 0},
                    ],
                    "fallback_reason": "empty_query",
                    "save_readiness": "blocked",
                    "save_reason": "Ask a more specific question before saving an analysis.",
                    "uncertainty": {
                        "claim_hit_count": 0,
                        "support_status_counts": {},
                        "truth_basis_counts": {},
                        "lifecycle_state_counts": {},
                    },
                    "temporal_scope": {
                        "dominant_scope": None,
                        "counts": {},
                    },
                },
            }

        page_results: list[dict[str, Any]] = []
        source_results: list[dict[str, Any]] = []
        for record in self.all_page_records():
            searchable_title = record["title"].lower()
            searchable_summary = record["summary"].lower()
            searchable_body = strip_markdown(record["body"]).lower()
            score = 0
            matched_terms: list[str] = []
            for token in tokens:
                token_score = 0
                if token in searchable_title:
                    token_score += 4
                if token in searchable_summary:
                    token_score += 3
                if token in searchable_body:
                    token_score += 1
                if token_score:
                    matched_terms.append(token)
                    score += token_score
            if score <= 0:
                continue
            result = {
                "stem": record["stem"],
                "title": record["title"],
                "section": record["section"],
                "summary": record["summary"],
                "score": score,
                "matched_terms": sorted(set(matched_terms)),
            }
            if record["section"] == "sources":
                source_results.append(result)
            else:
                page_results.append(result)

        page_results.sort(key=lambda item: (-int(item["score"]), str(item["title"]).lower()))
        source_results.sort(key=lambda item: (-int(item["score"]), str(item["title"]).lower()))
        top_pages = page_results[:limit]
        top_sources = source_results[:limit]

        registry_hits: dict[str, list[dict[str, Any]]] = {}
        for name in ["entities", "claims", "segments"]:
            hits: list[dict[str, Any]] = []
            for row in read_jsonl(self.warehouse_jsonl_dir / f"{name}.jsonl"):
                if name == "claims" and str(row.get("review_state") or "unknown") == REVIEW_STATE_REJECTED:
                    continue
                haystack = flatten_row_text(row).lower()
                matched_terms = [token for token in tokens if token in haystack]
                if not matched_terms:
                    continue
                hit_id = (
                    row.get("entity_id")
                    or row.get("claim_id")
                    or row.get("segment_id")
                    or row.get("message_id")
                    or "row"
                )
                preview = flatten_row_text(row)[:240]
                hits.append(
                    {
                        "id": hit_id,
                        "review_state": row.get("review_state") if name == "claims" else None,
                        "support_status": row.get("support_status") if name == "claims" else None,
                        "truth_basis": row.get("truth_basis") if name == "claims" else None,
                        "lifecycle_state": row.get("lifecycle_state") if name == "claims" else None,
                        "temporal_scope": row.get("temporal_scope") if name == "claims" else None,
                        "evidence_count": row.get("evidence_count") if name == "claims" else None,
                        "matched_terms": sorted(set(matched_terms)),
                        "preview": preview,
                    }
                )
            registry_hits[name] = hits[:limit]

        total_registry_hits = sum(len(items) for items in registry_hits.values())
        if top_pages and (top_sources or total_registry_hits):
            coverage = "supported"
        elif top_pages or top_sources or total_registry_hits:
            coverage = "thin"
        else:
            coverage = "none"

        warnings: list[str] = []
        if coverage == "thin":
            warnings.append("thin_coverage")
        if coverage == "none":
            warnings.append("no_direct_matches")

        provenance_sections = [
            {
                "label": "Wiki pages",
                "count": len(top_pages),
                "items": top_pages,
            },
            {
                "label": "Source pages",
                "count": len(top_sources),
                "items": top_sources,
            },
            {
                "label": "Canonical registries",
                "count": total_registry_hits,
                "items": [
                    {
                        "registry": name,
                        "count": len(items),
                        "hits": items,
                    }
                    for name, items in registry_hits.items()
                    if items
                ],
            },
        ]

        graph_seed_candidates: list[tuple[str, str]] = []
        graph_seed_candidates.extend(("page", item["stem"]) for item in top_pages[:2])
        graph_seed_candidates.extend(("source", item["stem"]) for item in top_sources[:2])
        claim_seed = next((str(item["id"]) for item in registry_hits.get("claims", []) if item.get("id")), None)
        if claim_seed:
            graph_seed_candidates.append(("claim", claim_seed))
        graph_hints = self._graph_hints_for_seeds(graph_seed_candidates)
        claim_hits = registry_hits.get("claims", [])
        claim_semantics = self._claim_semantics_summary(claim_hits)
        fallback_reason = None
        if coverage == "thin":
            fallback_reason = "thin_coverage"
        elif coverage == "none":
            fallback_reason = "no_direct_matches"
        save_readiness, save_reason = self._save_readiness_from_claim_semantics(coverage, claim_semantics)
        contract = {
            "route": "repo_local_search",
            "truth_layers": [
                {"name": "wiki_pages", "used": bool(top_pages), "count": len(top_pages)},
                {"name": "source_pages", "used": bool(top_sources), "count": len(top_sources)},
                {"name": "canonical_jsonl", "used": total_registry_hits > 0, "count": total_registry_hits},
                {
                    "name": "graph_projection",
                    "used": self._should_render_graph_hints(graph_hints),
                    "count": len(graph_hints.get("seeds") or []),
                },
            ],
            "fallback_reason": fallback_reason,
            "save_readiness": save_readiness,
            "save_reason": save_reason,
            "uncertainty": {
                "claim_hit_count": claim_semantics["claim_count"],
                "support_status_counts": claim_semantics["support_status_counts"],
                "truth_basis_counts": claim_semantics["truth_basis_counts"],
                "lifecycle_state_counts": claim_semantics["lifecycle_state_counts"],
            },
            "temporal_scope": {
                "dominant_scope": claim_semantics["dominant_scope"],
                "counts": claim_semantics["temporal_scope_counts"],
            },
        }
        graph_signal = next((hint for hint in graph_hints.get("path_hints") or [] if str(hint).strip()), None)

        answer_lines = [
            "# Local query preview",
            "",
            f"- Question: `{question}`",
            f"- Coverage: `{coverage}`",
            "",
        ]
        if top_pages or top_sources or total_registry_hits:
            answer_lines.extend(["## Draft answer", ""])
            if top_pages:
                lead_titles = ", ".join(f"`{item['title']}`" for item in top_pages[:2])
                answer_lines.append(f"- The current workspace most strongly points to {lead_titles}.")
                lead_summaries = [item["summary"] for item in top_pages[:2] if item.get("summary")]
                if lead_summaries:
                    answer_lines.append(f"- Summary signal: {' '.join(lead_summaries)}")
            if top_sources:
                answer_lines.append(
                    f"- Source grounding currently comes from {len(top_sources)} source page(s), led by `"
                    + top_sources[0]["title"]
                    + "`."
                )
            if total_registry_hits:
                answer_lines.append(
                    f"- Canonical registries add {total_registry_hits} matching hit(s) across entities, claims, or segments."
                )
                if claim_hits:
                    approved_count = sum(
                        1 for item in claim_hits if str(item.get("review_state") or "unknown") == REVIEW_STATE_ACTIVE
                    )
                    pending_count = sum(
                        1 for item in claim_hits if str(item.get("review_state") or "unknown") == REVIEW_STATE_PENDING
                    )
                    answer_lines.append(
                        f"- Claim review states in scope: approved `{approved_count}`, needs_review `{pending_count}`, rejected claims hidden."
                    )
                    support_counts = claim_semantics["support_status_counts"]
                    if support_counts:
                        answer_lines.append(
                            "- Claim support standing in scope: "
                            + ", ".join(f"{name} `{count}`" for name, count in support_counts.items())
                            + "."
                        )
                    truth_basis_counts = claim_semantics["truth_basis_counts"]
                    if truth_basis_counts:
                        answer_lines.append(
                            "- Truth basis in scope: "
                            + ", ".join(f"{name} `{count}`" for name, count in truth_basis_counts.items())
                            + "."
                        )
                    dominant_scope = claim_semantics.get("dominant_scope")
                    if dominant_scope:
                        answer_lines.append(f"- Dominant temporal scope: `{dominant_scope}`.")
            if graph_signal:
                answer_lines.append(f"- Graph signal: {graph_signal}")
            if coverage == "thin":
                answer_lines.append(
                    "- This is a thin-coverage answer draft. Treat it as a routing hint and inspect the linked pages before relying on it."
                )
            answer_lines.append("")
        if coverage == "none":
            answer_lines.extend(
                [
                    "## Draft answer",
                    "",
                    "- The workspace does not currently have enough direct evidence for a trustworthy answer draft.",
                    "- Refine the query with stable names, dates, or explicit source/page titles before saving an analysis.",
                    "",
                ]
            )
        if warnings:
            answer_lines.extend(["## Warnings", ""] + [f"- {warning.replace('_', ' ')}" for warning in warnings] + [""])
        if top_pages:
            answer_lines.extend(["## Suggested wiki pages", ""])
            answer_lines.extend([f"- [[{item['stem']}]] — {item['summary']}" for item in top_pages])
            answer_lines.append("")
        if top_sources:
            answer_lines.extend(["## Source grounding", ""])
            answer_lines.extend([f"- [[{item['stem']}]] — {item['summary']}" for item in top_sources])
            answer_lines.append("")
        if total_registry_hits:
            answer_lines.extend(["## Canonical registry hits", ""])
            for name, hits in registry_hits.items():
                if hits:
                    answer_lines.append(f"- {name}: {len(hits)}")
            answer_lines.append("")
        if self._should_render_graph_hints(graph_hints):
            answer_lines.extend(["## Graph hints", "", f"- {graph_hints['summary']}"])
            if graph_hints["related_nodes"]:
                answer_lines.append("- Related nodes: " + ", ".join(f"`{item}`" for item in graph_hints["related_nodes"]))
            if graph_hints["path_hints"]:
                answer_lines.extend(["", "### Path hints", ""] + [f"- {hint}" for hint in graph_hints["path_hints"]])
            if graph_hints["seeds"]:
                answer_lines.extend(["", "### Graph seeds", ""])
                for item in graph_hints["seeds"]:
                    answer_lines.append(
                        f"- `{item.get('type', 'seed')}` `{item.get('value', '')}` — {item.get('title', item.get('key', 'graph seed'))}"
                    )
            answer_lines.append("")
        if not top_pages and not top_sources and not total_registry_hits:
            answer_lines.extend(
                [
                    "## Next best action",
                    "",
                    "- Browse nearby source pages first, then refine the question with stable names, dates, or concepts.",
                    "",
                ]
            )

        return {
            "mode": "repo_local_search",
            "question": question,
            "tokens": tokens,
            "coverage": coverage,
            "answer_markdown": "\n".join(answer_lines).strip() + "\n",
            "related_pages": top_pages,
            "related_sources": top_sources,
            "provenance_sections": provenance_sections,
            "warnings": warnings,
            "graph_hints": graph_hints,
            "contract": contract,
        }

    def rebuild_index(self) -> bool:
        try:
            import llm_wiki  # type: ignore[import-not-found]
        except ModuleNotFoundError:  # pragma: no cover - exercised in package import contexts
            from scripts import llm_wiki  # type: ignore[no-redef]

        index_path = self.meta_dir / "index.md"
        before = read_text(index_path) if index_path.exists() else None
        previous_root = llm_wiki.ROOT
        previous_wiki_dir = llm_wiki.WIKI_DIR
        previous_meta_dir = llm_wiki.META_DIR
        previous_raw_dir = llm_wiki.RAW_DIR
        try:
            llm_wiki.ROOT = self.root
            llm_wiki.WIKI_DIR = self.wiki_dir
            llm_wiki.META_DIR = self.meta_dir
            llm_wiki.RAW_DIR = self.raw_dir
            llm_wiki.rebuild_index()
        finally:
            llm_wiki.ROOT = previous_root
            llm_wiki.WIKI_DIR = previous_wiki_dir
            llm_wiki.META_DIR = previous_meta_dir
            llm_wiki.RAW_DIR = previous_raw_dir
        after = read_text(index_path) if index_path.exists() else None
        return before != after

    def append_log_entry(self, kind: str, title: str, bullets: list[str]) -> bool:
        log_path = self.meta_dir / "log.md"
        if log_path.exists():
            content = read_text(log_path)
        else:
            content = (
                "---\n"
                "title: Log\n"
                "type: meta\n"
                "status: active\n"
                f"created: {dt.date.today().isoformat()}\n"
                f"updated: {dt.date.today().isoformat()}\n"
                "---\n\n"
                "# Log\n"
            )
        today = dt.date.today().isoformat()
        entry_block = (
            f"\n## [{today}] {kind} | {title}\n\n"
            + "\n".join(f"- {bullet}" for bullet in bullets)
            + "\n"
        )
        if entry_block in content:
            return False
        content = update_frontmatter_date(content, "updated", today)
        if not content.endswith("\n"):
            content += "\n"
        content += entry_block
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(content, encoding="utf-8")
        return True

    def link_analysis_from_related_pages(
        self,
        analysis_stem: str,
        analysis_title: str,
        preview: dict[str, Any],
    ) -> list[str]:
        today = dt.date.today().isoformat()
        link_targets: dict[str, dict[str, Any]] = {}
        for item in preview.get("related_sources", []) + preview.get("related_pages", []):
            stem = str(item.get("stem") or "")
            section = str(item.get("section") or "")
            score = int(item.get("score") or 0)
            if not stem or section not in {"sources", "concepts", "entities", "people", "projects", "timelines"}:
                continue
            if score < 5:
                continue
            link_targets[stem] = item

        linked_paths: list[str] = []
        for stem in list(link_targets.keys())[:5]:
            lookup = self.page_lookup()
            path = lookup.get(stem)
            if path is None:
                continue
            existing = read_text(path)
            bullet = f"- [[{analysis_stem}]] — {analysis_title} ({today})"
            updated = append_bullet_to_section(existing, "Related analyses", bullet)
            if updated == (existing if existing.endswith("\n") else existing + "\n"):
                continue
            updated = update_frontmatter_date(updated, "updated", today)
            path.write_text(updated, encoding="utf-8")
            linked_paths.append(str(path.relative_to(self.root)))
        return linked_paths

    def save_query_analysis(self, question: str, limit: int = 5) -> dict[str, Any]:
        preview = self.query_preview(question, limit=limit)
        today = dt.date.today().isoformat()
        stem = f"analysis-{today}-{slugify(question)[:64]}"
        path = self.wiki_dir / "analyses" / f"{stem}.md"
        safe_title = question.replace('"', "'").strip() or "Untitled analysis"
        created = today
        if path.exists():
            existing_frontmatter, _ = parse_frontmatter(read_text(path))
            created = safe_iso_date(existing_frontmatter.get("created")) or today

        related_source_links = [f'"[[{item["stem"]}]]"' for item in preview["related_sources"][:5]]
        related_page_links = [f"[[{item['stem']}]]" for item in preview["related_pages"][:5]]
        lines = [
            "---",
            f'title: "{safe_title}"',
            "type: analysis",
            "status: active",
            f"created: {created}",
            f"updated: {today}",
            "tags:",
            "  - workbench-query",
            f"coverage: {preview['coverage']}",
        ]
        if related_source_links:
            lines.append("sources:")
            lines.extend([f"  - {item}" for item in related_source_links])
        else:
            lines.append("sources: []")
        lines.extend(
            [
                "---",
                "",
                f"# {safe_title}",
                "",
                "## Query",
                "",
                f"- Asked from the local sidecar workbench on {today}",
                f"- Coverage: `{preview['coverage']}`",
                "",
                "## Preview",
                "",
                preview["answer_markdown"].strip(),
                "",
            ]
        )
        if related_page_links:
            lines.extend(["## Related pages", ""] + [f"- {item}" for item in related_page_links] + [""])
        provenance_items = preview["provenance_sections"]
        if provenance_items:
            lines.extend(["## Provenance sections", ""])
            for section in provenance_items:
                lines.append(f"- {section['label']}: {section['count']}")
            lines.append("")

        contract = preview.get("contract") or {}
        truth_layers = contract.get("truth_layers") or []
        if contract:
            lines.extend(
                [
                    "## Query contract",
                    "",
                    f"- Route: `{contract.get('route', 'unknown')}`",
                    f"- Save readiness: `{contract.get('save_readiness', 'unknown')}`",
                    f"- Save reason: {contract.get('save_reason', 'No save reason recorded.')}",
                ]
            )
            fallback_reason = contract.get("fallback_reason")
            if fallback_reason:
                lines.append(f"- Fallback reason: `{fallback_reason}`")
            if truth_layers:
                lines.extend(["- Truth layers touched:"])
                for layer in truth_layers:
                    lines.append(
                        f"  - `{layer.get('name', 'layer')}` used=`{layer.get('used', False)}` count=`{layer.get('count', 0)}`"
                    )
            lines.append("")

        graph_hints = preview.get("graph_hints") or {}
        if self._should_render_graph_hints(graph_hints):
            lines.extend(["## Graph context", "", f"- Graph hints: {graph_hints.get('summary', 'No graph hint summary.')}" ])
            graph_seeds = graph_hints.get("seeds") or []
            if graph_seeds:
                lines.extend(["", "### Graph seeds", ""])
                for item in graph_seeds:
                    lines.append(
                        f"- `{item.get('type', 'seed')}` `{item.get('value', '')}` — {item.get('title', item.get('key', 'graph seed'))}"
                    )
            lines.append("")

        next_text = "\n".join(lines).strip() + "\n"
        existing_text = read_text(path) if path.exists() else None
        changed_files: list[str] = []
        path.parent.mkdir(parents=True, exist_ok=True)
        if existing_text is None:
            path.write_text(next_text, encoding="utf-8")
            changed_files.append(str(path.relative_to(self.root)))

        log_changed = self.append_log_entry(
            "query",
            safe_title,
            [
                f"Saved analysis page [[{stem}]] from the local Ask workspace.",
                f"Coverage: `{preview['coverage']}`.",
            ],
        )
        linked_paths = self.link_analysis_from_related_pages(stem, safe_title, preview)
        index_changed = self.rebuild_index()
        meta_paths: list[str] = []
        if log_changed:
            meta_paths.append(str((self.meta_dir / 'log.md').relative_to(self.root)))
        if index_changed:
            meta_paths.append(str((self.meta_dir / 'index.md').relative_to(self.root)))
        changed_files = changed_files + meta_paths + linked_paths
        changed_files = list(dict.fromkeys(changed_files))
        ensure_allowed_write_paths(changed_files)
        return {
            "action": "save_analysis",
            "question": safe_title,
            "analysis_stem": stem,
            "analysis_path": str(path.relative_to(self.root)),
            "changed_files": changed_files,
            "linked_pages": linked_paths,
            "preview": preview,
        }

    def draft_source_summary(self, source_stem: str, max_chars: int = 12000) -> dict[str, Any]:
        normalized_stem = source_stem.strip()
        if not normalized_stem:
            raise ValueError("source_stem is required")

        config = self.load_helper_model_config()
        source_payload = self.source_detail(normalized_stem)
        raw_path_value = source_payload.get("raw_path")
        if not isinstance(raw_path_value, str) or not raw_path_value.strip():
            raise ValueError(f"Source page `{normalized_stem}` does not declare raw_path")

        raw_path = self.resolve_allowed_raw_source_path(raw_path_value, normalized_stem)

        try:
            raw_text = read_text(raw_path)
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"Raw source file `{raw_path_value}` is not UTF-8 text. Use a companion note in raw/notes/ first."
            ) from exc
        bounded_raw_text = raw_text[:max(1000, min(max_chars, 40000))]
        prompt = "\n".join(
            [
                "Create a draft-only markdown source summary for this repository.",
                "Do not claim certainty beyond the provided source and source page.",
                "Do not invent facts.",
                "Use these sections exactly:",
                "## Draft summary",
                "## Key facts",
                "## Important claims",
                "## Uncertainties",
                "## Open questions",
                "",
                f"Source page title: {source_payload['frontmatter'].get('title') or normalized_stem}",
                f"Source page stem: {normalized_stem}",
                f"Raw path: {raw_path_value}",
                "",
                "Existing source page body:",
                source_payload["body"].strip() or "(empty)",
                "",
                "Raw source excerpt:",
                bounded_raw_text,
            ]
        )
        draft_markdown = run_helper_chat_completion(
            config,
            system_prompt=(
                "You are a backend-only helper model for an Obsidian-first LLM wiki. "
                "Return markdown only. The output is a draft and must preserve uncertainty."
            ),
            user_prompt=prompt,
        )
        return {
            "action": "draft_source_summary",
            "source_stem": normalized_stem,
            "source_path": source_payload["path"],
            "raw_path": raw_path_value,
            "draft_markdown": draft_markdown,
            "helper_model": helper_model_public_summary(config),
            "changed_files": [],
            "warnings": ["draft_only_output", "no_direct_write"],
        }

    def review_claim(self, claim_id: str, review_state: str) -> dict[str, Any]:
        normalized_state = review_state.strip().lower()
        if normalized_state not in {REVIEW_STATE_ACTIVE, REVIEW_STATE_REJECTED}:
            raise ValueError("review_state must be approved or rejected")

        claims_path = self.warehouse_jsonl_dir / "claims.jsonl"
        claims = read_jsonl(claims_path)
        updated_claim: dict[str, Any] | None = None
        today = dt.date.today().isoformat()
        claim_was_same = False
        for row in claims:
            if row.get("claim_id") != claim_id:
                continue
            support_status, lifecycle_state = self._derived_claim_state(
                normalized_state,
                bool(row.get("contradiction_candidate")),
            )
            if row.get("review_state") == normalized_state:
                row["support_status"] = support_status
                row["lifecycle_state"] = lifecycle_state
                row["state_updated_at"] = today
                updated_claim = row
                claim_was_same = True
                break
            row["review_state"] = normalized_state
            row["reviewed_at"] = today
            row["reviewed_via"] = "workbench-review"
            row["support_status"] = support_status
            row["lifecycle_state"] = lifecycle_state
            row["state_updated_at"] = today
            updated_claim = row
            break

        if updated_claim is None:
            raise FileNotFoundError(f"Claim not found: {claim_id}")

        changed_files: list[str] = []
        if not claim_was_same:
            write_jsonl(claims_path, claims)
            title = f"claim review {claim_id}"
            self.append_log_entry(
                "review",
                title,
                [
                    f"Set `{claim_id}` review_state to `{normalized_state}` via the workbench.",
                    f"Subject: `{updated_claim.get('subject_id') or 'unknown'}`.",
                ],
            )
            changed_files = [
                str(claims_path.relative_to(self.root)),
                str((self.meta_dir / "log.md").relative_to(self.root)),
            ]
        ensure_allowed_write_paths(changed_files)
        return {
            "action": "review_claim",
            "claim_id": claim_id,
            "review_state": normalized_state,
            "changed_files": changed_files,
            "claim": updated_claim,
        }

    def raw_counts(self) -> dict[str, int]:
        counts = {
            "inbox": 0,
            "processed": 0,
            "notes": 0,
            "assets": 0,
            "other": 0,
        }
        for key in counts:
            if key == "other":
                continue
            directory = self.raw_dir / key
            if directory.exists():
                counts[key] = sum(1 for path in directory.rglob("*") if path.is_file())
        categorized_files = sum(counts[key] for key in ("inbox", "processed", "notes", "assets"))
        all_raw_files = sum(1 for path in self.raw_dir.rglob("*") if path.is_file())
        counts["other"] = max(0, all_raw_files - categorized_files)
        counts["total"] = all_raw_files
        return counts

    def warehouse_registry_counts(self) -> dict[str, int]:
        return {
            name: len(read_jsonl(self.warehouse_jsonl_dir / f"{name}.jsonl"))
            for name in JSONL_REGISTRIES
        }

    def _graph_projection_paths(self) -> tuple[Path, Path]:
        return self.graph_dir / "nodes.jsonl", self.graph_dir / "edges.jsonl"

    def _graph_projection_signature(self, path: Path) -> tuple[int, int] | None:
        if not path.exists():
            return None
        stat = path.stat()
        return (stat.st_mtime_ns, stat.st_size)

    def _graph_projection_available(self) -> bool:
        nodes_path, edges_path = self._graph_projection_paths()
        return nodes_path.exists() and edges_path.exists()

    def _graph_nodes(self) -> list[dict[str, Any]]:
        nodes_path, _ = self._graph_projection_paths()
        signature = self._graph_projection_signature(nodes_path)
        if self._graph_nodes_cache is None or self._graph_nodes_signature != signature:
            self._graph_nodes_cache = read_jsonl(nodes_path)
            self._graph_nodes_signature = signature
        return self._graph_nodes_cache

    def _graph_edges(self) -> list[dict[str, Any]]:
        _, edges_path = self._graph_projection_paths()
        signature = self._graph_projection_signature(edges_path)
        if self._graph_edges_cache is None or self._graph_edges_signature != signature:
            self._graph_edges_cache = read_jsonl(edges_path)
            self._graph_edges_signature = signature
        return self._graph_edges_cache

    def _graph_string(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return " ".join(self._graph_string(item) for item in value)
        if isinstance(value, dict):
            return " ".join(self._graph_string(item) for item in value.values())
        return str(value)

    def _graph_node_label(self, node: dict[str, Any]) -> str:
        return str(node.get("label") or node.get("title") or node.get("name") or node.get("id") or "unnamed-node")

    def _graph_edge_label(self, edge: dict[str, Any]) -> str:
        return str(edge.get("label") or edge.get("predicate") or edge.get("kind") or "related_to")

    def _graph_node_kind(self, node: dict[str, Any]) -> str:
        return str(node.get("kind") or node.get("type") or "node")

    def _is_graph_noise_label(self, label: str) -> bool:
        normalized = label.strip().lower()
        if not normalized:
            return True
        if normalized in {"http", "https", "url", "all", "blog", "reddit", "from", "title", "excerpt", "readme", "snapshot"}:
            return True
        if normalized.startswith("url: http") or normalized.startswith("http://") or normalized.startswith("https://"):
            return True
        if normalized.startswith("fetched:") or " fetched:" in normalized or " title:" in normalized or "http status:" in normalized or "excerpt:" in normalized:
            return True
        if normalized.startswith("- ") and ("http" in normalized or "retrieval note:" in normalized):
            return True
        return False

    def _graph_hint_candidate(self, source_label: str, edge_label: str, target_label: str) -> str | None:
        if self._is_graph_noise_label(source_label) or self._is_graph_noise_label(target_label):
            return None
        hint = f"{source_label} --{edge_label}--> {target_label}"
        if "http://" in hint.lower() or "https://" in hint.lower():
            return None
        return hint

    def _graph_label_quality_score(self, label: str) -> int:
        normalized = label.strip().lower()
        if self._is_graph_noise_label(label):
            return -100
        score = 0
        word_count = len(normalized.split())
        score += max(0, 16 - min(word_count, 16))
        score += max(0, 96 - min(len(normalized), 96)) // 6
        if label[:1].isupper():
            score += 2
        if normalized in {"readme", "blog", "reddit", "snapshot", "excerpt"}:
            score -= 8
        if normalized.startswith("- ") or normalized.startswith("this folder contains") or normalized.startswith("these files are treated"):
            score -= 12
        if "`" in label:
            score -= 4
        return score

    def _graph_hint_score(self, source_label: str, edge_label: str, target_label: str) -> int:
        score = self._graph_label_quality_score(source_label) + self._graph_label_quality_score(target_label)
        normalized_edge = edge_label.strip().lower()
        if normalized_edge in {"supports", "documents", "mentions", "related_to"}:
            score += 6
        elif normalized_edge.startswith("about"):
            score += 2
        hint_length = len(f"{source_label} --{edge_label}--> {target_label}")
        if hint_length > 180:
            score -= 10
        return score

    def _graph_seed_payload(self, seed_type: str, seed: str) -> tuple[str, list[str]]:
        normalized_type = seed_type.strip().lower()
        normalized_seed = seed.strip()
        if normalized_type not in {"page", "source", "claim"}:
            raise ValueError("seed_type must be one of: page, source, claim")
        if not normalized_seed:
            raise ValueError("seed is required")

        if normalized_type == "page":
            record = self.wiki_page(normalized_seed)
            label = str(record["frontmatter"].get("title") or record["stem"])
            tokens = tokenize_query(" ".join([label, record["stem"], record.get("summary") or ""]))
            return label, tokens

        if normalized_type == "source":
            record = self.source_detail(normalized_seed)
            label = str(record["frontmatter"].get("title") or record["stem"])
            tokens = tokenize_query(" ".join([label, record["stem"], record.get("summary") or ""]))
            return label, tokens

        claims = read_jsonl(self.warehouse_jsonl_dir / "claims.jsonl")
        claim = next((row for row in claims if str(row.get("claim_id") or "") == normalized_seed), None)
        label = str((claim or {}).get("claim_text") or normalized_seed)
        token_source = " ".join(
            [
                label,
                str((claim or {}).get("subject_id") or ""),
                str((claim or {}).get("object_id") or ""),
                str((claim or {}).get("predicate") or ""),
            ]
        )
        return label, tokenize_query(token_source)

    def graph_inspect(self, seed_type: str, seed: str, *, max_nodes: int = 8, max_edges: int = 12) -> dict[str, Any]:
        seed_label, tokens = self._graph_seed_payload(seed_type, seed)
        payload: dict[str, Any] = {
            "seed": {"type": seed_type, "value": seed, "label": seed_label},
            "source_path": "warehouse/graph_projection/",
            "neighborhood": {"node_count": 0, "edge_count": 0, "nodes": [], "edges": []},
            "path_hints": [],
            "warnings": [],
        }

        if not self._graph_projection_available():
            payload.update(
                {
                    "mode": "unavailable",
                    "summary": "Graph projection is unavailable because `warehouse/graph_projection/` does not contain bounded graph artifacts yet.",
                    "warnings": ["graph_projection_empty"],
                }
            )
            return payload

        nodes = self._graph_nodes()
        edges = self._graph_edges()
        searchable_tokens = [token.lower() for token in tokens if token]
        matched_nodes = [node for node in nodes if any(token in self._graph_string(node).lower() for token in searchable_tokens)]

        if not matched_nodes:
            payload.update(
                {
                    "mode": "empty",
                    "summary": f"No bounded neighborhood matched the current {seed_type} seed.",
                }
            )
            return payload

        matched_ids = [str(node.get("id") or "") for node in matched_nodes if node.get("id")][: max(1, max_nodes // 2)]
        selected_ids = list(dict.fromkeys(matched_ids))
        for edge in edges:
            source = str(edge.get("source") or edge.get("from") or "")
            target = str(edge.get("target") or edge.get("to") or "")
            if source in selected_ids or target in selected_ids:
                if source and source not in selected_ids and len(selected_ids) < max_nodes:
                    selected_ids.append(source)
                if target and target not in selected_ids and len(selected_ids) < max_nodes:
                    selected_ids.append(target)

        node_lookup = {str(node.get("id") or ""): node for node in nodes if node.get("id")}
        selected_nodes = []
        for node_id in selected_ids[:max_nodes]:
            node = node_lookup.get(node_id)
            if not node:
                continue
            selected_nodes.append(
                {
                    "id": node_id,
                    "label": self._graph_node_label(node),
                    "kind": self._graph_node_kind(node),
                    "matched": node_id in matched_ids,
                }
            )

        selected_id_set = {node["id"] for node in selected_nodes}
        selected_edges = []
        path_hints = []
        for edge in edges:
            source = str(edge.get("source") or edge.get("from") or "")
            target = str(edge.get("target") or edge.get("to") or "")
            if source in selected_id_set and target in selected_id_set:
                label = self._graph_edge_label(edge)
                selected_edges.append({"source": source, "target": target, "label": label})
                source_label = next((node["label"] for node in selected_nodes if node["id"] == source), source)
                target_label = next((node["label"] for node in selected_nodes if node["id"] == target), target)
                path_hints.append(f"{source_label} --{label}--> {target_label}")
            if len(selected_edges) >= max_edges:
                break

        payload.update(
            {
                "mode": "available",
                "summary": f"Found a bounded neighborhood for the current {seed_type} seed.",
                "neighborhood": {
                    "node_count": len(selected_nodes),
                    "edge_count": len(selected_edges),
                    "nodes": selected_nodes,
                    "edges": selected_edges,
                },
                "path_hints": path_hints[:5],
            }
        )
        return payload

    def _build_graph_seed(self, seed_type: str, seed: str) -> dict[str, str] | None:
        try:
            label, _ = self._graph_seed_payload(seed_type, seed)
        except (ValueError, FileNotFoundError):
            return None
        return {
            "key": f"{seed_type}:{seed}",
            "type": seed_type,
            "value": seed,
            "title": label,
            "subtitle": f"{seed_type} seed",
            "description": f"Bounded graph hint for {seed_type} context.",
        }

    def _graph_hints_for_seeds(self, seeds: list[tuple[str, str]]) -> dict[str, Any]:
        if not self._graph_projection_available():
            return {
                "available": False,
                "summary": "Graph projection is unavailable for this query preview.",
                "related_nodes": [],
                "path_hints": [],
                "warnings": ["graph_projection_empty"],
                "seeds": [],
            }

        related_nodes: list[str] = []
        path_hints: list[str] = []
        path_hint_scores: dict[str, int] = {}
        warnings: list[str] = []
        seed_payloads: list[dict[str, str]] = []
        any_available = False

        try:
            for seed_type, seed in seeds:
                if not seed:
                    continue
                seed_payload = self._build_graph_seed(seed_type, seed)
                if seed_payload and not any(item["key"] == seed_payload["key"] for item in seed_payloads):
                    seed_payloads.append(seed_payload)
                try:
                    inspect = self.graph_inspect(seed_type, seed)
                except (ValueError, FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
                    return {
                        "available": False,
                        "summary": "Graph projection is unavailable for this query preview.",
                        "related_nodes": [],
                        "path_hints": [],
                        "warnings": ["graph_projection_invalid"],
                        "seeds": [],
                    }
                if inspect.get("mode") == "available":
                    any_available = True
                    node_labels = {
                        str(node.get("id") or ""): str(node.get("label") or "").strip()
                        for node in inspect.get("neighborhood", {}).get("nodes", [])
                    }
                    for label in node_labels.values():
                        if label and not self._is_graph_noise_label(label) and label not in related_nodes:
                            related_nodes.append(label)
                    for edge in inspect.get("neighborhood", {}).get("edges", []):
                        source = str(edge.get("source") or "")
                        target = str(edge.get("target") or "")
                        edge_label = str(edge.get("label") or "related_to")
                        source_label = node_labels.get(source, source)
                        target_label = node_labels.get(target, target)
                        candidate = self._graph_hint_candidate(
                            source_label,
                            edge_label,
                            target_label,
                        )
                        if candidate and candidate not in path_hints:
                            path_hints.append(candidate)
                            path_hint_scores[candidate] = self._graph_hint_score(source_label, edge_label, target_label)
                for warning in inspect.get("warnings", []):
                    if warning not in warnings:
                        warnings.append(warning)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return {
                "available": False,
                "summary": "Graph projection is unavailable for this query preview.",
                "related_nodes": [],
                "path_hints": [],
                "warnings": ["graph_projection_invalid"],
                "seeds": [],
            }

        if any_available:
            summary = "Graph hints are available for this query preview."
        elif seed_payloads:
            summary = "Graph inspect is configured, but no bounded neighborhood matched the current preview seeds."
        else:
            summary = "No graph seeds were available for this query preview."

        return {
            "available": any_available,
            "summary": summary,
            "related_nodes": sorted(related_nodes, key=self._graph_label_quality_score, reverse=True)[:6],
            "path_hints": sorted(path_hints, key=lambda hint: path_hint_scores.get(hint, -1000), reverse=True)[:5],
            "warnings": warnings,
            "seeds": seed_payloads[:6],
        }

    def _graph_hint_text(self, seed_type: str, seed: str) -> str | None:
        try:
            inspect = self.graph_inspect(seed_type, seed)
        except (ValueError, FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        if inspect.get("mode") == "available" and inspect.get("path_hints"):
            return str(inspect["path_hints"][0])
        if inspect.get("mode") == "available":
            count = inspect.get("neighborhood", {}).get("node_count", 0)
            return f"bounded neighborhood nodes: {count}"
        return None

    def _should_render_graph_hints(self, graph_hints: dict[str, Any] | None) -> bool:
        if not graph_hints:
            return False
        warnings = list(graph_hints.get("warnings") or [])
        if "empty_query" in warnings:
            return False
        return bool(
            graph_hints.get("available")
            or graph_hints.get("related_nodes")
            or graph_hints.get("path_hints")
            or graph_hints.get("seeds")
        )

    def summary(self) -> dict[str, Any]:
        index_path = self.meta_dir / "index.md"
        log_path = self.meta_dir / "log.md"
        index_sections = parse_index_sections(read_text(index_path)) if index_path.exists() else []
        log_entries = parse_log_entries(read_text(log_path)) if log_path.exists() else []
        graph_file_count = count_non_placeholder_files(self.graph_dir)

        warnings: list[str] = []
        if not index_path.exists():
            warnings.append("missing_index")
        if not log_path.exists():
            warnings.append("missing_log")
        if graph_file_count == 0:
            warnings.append("graph_projection_empty")

        return {
            "root": str(self.root),
            "raw": {
                "counts": self.raw_counts(),
            },
            "wiki": {
                "page_count": len(self.iter_markdown_pages()),
                "section_count": len(index_sections),
                "index_entry_count": sum(len(section["entries"]) for section in index_sections),
                "log_entry_count": len(log_entries),
            },
            "warehouse": {
                "registry_counts": self.warehouse_registry_counts(),
            },
            "graph_projection": {
                "path": "warehouse/graph_projection/",
                "file_count": graph_file_count,
                "available": graph_file_count > 0,
            },
            "warnings": warnings,
        }

    def wiki_index(self) -> dict[str, Any]:
        index_path = self.meta_dir / "index.md"
        sections = parse_index_sections(read_text(index_path)) if index_path.exists() else []
        records_by_stem = {record["stem"]: record for record in self.all_page_records()}
        enriched_sections: list[dict[str, Any]] = []
        for section in sections:
            enriched_entries: list[dict[str, Any]] = []
            for entry in section["entries"]:
                record = records_by_stem.get(entry["stem"], {})
                enriched_entries.append(
                    {
                        "stem": entry["stem"],
                        "title": record.get("title") or entry["stem"].replace("-", " ").title(),
                        "summary": entry.get("summary") or record.get("summary") or "",
                    }
                )
            enriched_sections.append({"name": section["name"], "entries": enriched_entries})
        return {
            "path": "wiki/_meta/index.md",
            "sections": enriched_sections,
        }

    def wiki_page(self, stem: str) -> dict[str, Any]:
        lookup = self.page_lookup()
        if stem not in lookup:
            raise FileNotFoundError(f"Page not found: {stem}")

        path = lookup[stem]
        text = read_text(path)
        frontmatter, body = parse_frontmatter(text)
        return {
            "stem": stem,
            "path": str(path.relative_to(self.root)),
            "section": path.relative_to(self.wiki_dir).parts[0],
            "frontmatter": frontmatter,
            "body": body,
            "summary": extract_summary(text),
            "related_pages": self.related_pages_for_stem(stem),
        }

    def source_detail(self, stem: str) -> dict[str, Any]:
        path = self.sources_dir / f"{stem}.md"
        if not path.exists():
            raise FileNotFoundError(f"Source page not found: {stem}")

        text = read_text(path)
        frontmatter, body = parse_frontmatter(text)
        documents = read_jsonl(self.warehouse_jsonl_dir / "documents.jsonl")
        source_versions = read_jsonl(self.warehouse_jsonl_dir / "source_versions.jsonl")
        entities = read_jsonl(self.warehouse_jsonl_dir / "entities.jsonl")
        claims = read_jsonl(self.warehouse_jsonl_dir / "claims.jsonl")
        claim_evidence = read_jsonl(self.warehouse_jsonl_dir / "claim_evidence.jsonl")
        segments = read_jsonl(self.warehouse_jsonl_dir / "segments.jsonl")
        derived_edges = read_jsonl(self.warehouse_jsonl_dir / "derived_edges.jsonl")

        related_documents = [
            row
            for row in documents
            if row.get("source_page") == stem or row.get("incremental_status_page") == stem
        ]
        related_document_ids = {row.get("document_id") for row in related_documents}
        related_versions = [
            row
            for row in source_versions
            if row.get("document_id") in related_document_ids
            or row.get("raw_path") == frontmatter.get("raw_path")
        ]
        related_versions.sort(
            key=lambda row: (
                row.get("ingested_at") or "",
                row.get("export_version_id") or "",
            ),
            reverse=True,
        )

        latest_document = related_documents[0] if related_documents else None
        latest_version = related_versions[0] if related_versions else None
        family_version_count = len(
            [
                row
                for row in source_versions
                if row.get("source_family_id")
                == (
                    latest_version.get("source_family_id")
                    if latest_version
                    else latest_document.get("source_family_id")
                    if latest_document
                    else None
                )
            ]
        )
        related_entities = [
            row
            for row in entities
            if row.get("source_document_id") in related_document_ids
            or any(doc_id in related_document_ids for doc_id in (row.get("source_document_ids") or []))
        ]
        related_claims = [
            row
            for row in claims
            if row.get("document_id") in related_document_ids or row.get("source_document_id") in related_document_ids
        ]
        approved_claims = [
            row for row in related_claims if str(row.get("review_state") or "unknown") == REVIEW_STATE_ACTIVE
        ]
        pending_claims = [
            row for row in related_claims if str(row.get("review_state") or "unknown") == REVIEW_STATE_PENDING
        ]
        rejected_claims = [
            row for row in related_claims if str(row.get("review_state") or "unknown") == REVIEW_STATE_REJECTED
        ]
        related_claim_ids = {row.get("claim_id") for row in related_claims}
        related_evidence = [
            row
            for row in claim_evidence
            if row.get("claim_id") in related_claim_ids or row.get("source_document_id") in related_document_ids
        ]
        related_segments = [
            row
            for row in segments
            if row.get("document_id") in related_document_ids
        ]
        related_derived_edges = [
            row
            for row in derived_edges
            if row.get("source_claim_id") in related_claim_ids
            or row.get("source") in related_document_ids
            or row.get("target") in related_document_ids
        ]
        needs_review_claims = pending_claims
        low_confidence_claims = [
            row
            for row in pending_claims
            if isinstance(row.get("confidence"), (int, float)) and float(row["confidence"]) < 0.9
        ]

        incremental_status = None
        if latest_document or latest_version:
            supersedes_export_version_id = (
                latest_version.get("supersedes_export_version_id")
                if latest_version
                else latest_document.get("supersedes_export_version_id")
                if latest_document
                else None
            )
            new_message_count = latest_version.get("new_message_count") if latest_version else None
            unchanged_message_count = latest_version.get("unchanged_message_count") if latest_version else None
            if new_message_count is None and unchanged_message_count is None and family_version_count <= 1:
                new_message_count = latest_version.get("message_count") if latest_version else latest_document.get("message_count") if latest_document else None
                unchanged_message_count = 0 if new_message_count is not None else None
            incremental_status_page = latest_document.get("incremental_status_page") if latest_document else None
            affected_registry_paths = (
                (latest_version.get("affected_registry_paths") or [])
                if latest_version
                else []
            )
            affected_wiki_paths = (
                (latest_version.get("affected_wiki_paths") or [])
                if latest_version
                else []
            )
            if not affected_registry_paths:
                affected_registry_paths = default_incremental_registry_paths()
            if not affected_wiki_paths:
                affected_wiki_paths = default_incremental_wiki_paths(stem, incremental_status_page)
            incremental_status = {
                "document_id": latest_document.get("document_id") if latest_document else None,
                "source_family_id": latest_version.get("source_family_id") if latest_version else latest_document.get("source_family_id") if latest_document else None,
                "source_kind": latest_version.get("source_kind") if latest_version else latest_document.get("source_kind") if latest_document else None,
                "latest_export_version_id": latest_version.get("export_version_id") if latest_version else latest_document.get("export_version_id") if latest_document else None,
                "supersedes_export_version_id": supersedes_export_version_id,
                "message_count": latest_version.get("message_count") if latest_version else latest_document.get("message_count") if latest_document else None,
                "new_message_count": new_message_count,
                "unchanged_message_count": unchanged_message_count,
                "incremental_status_page": incremental_status_page,
                "affected_registry_paths": affected_registry_paths,
                "affected_wiki_paths": affected_wiki_paths,
            }
        coverage = {
            "document_count": len(related_documents),
            "version_count": len(related_versions),
            "entity_count": len(related_entities),
            "claim_count": len(related_claims),
            "approved_claim_count": len(approved_claims),
            "pending_claim_count": len(pending_claims),
            "rejected_claim_count": len(rejected_claims),
            "evidence_count": len(related_evidence),
            "segment_count": len(related_segments),
            "derived_edge_count": len(related_derived_edges),
            "needs_review_claim_count": len(needs_review_claims),
            "low_confidence_claim_count": len(low_confidence_claims),
        }
        relation_type_counts = Counter(str(row.get("relation_type") or row.get("label") or "unknown") for row in related_derived_edges)
        knowledge_state_summary = self._claim_semantics_summary(related_claims)
        knowledge_state_summary["relation_type_counts"] = dict(sorted(relation_type_counts.items()))
        review_queue = [
            {
                "claim_id": row.get("claim_id"),
                "predicate": row.get("predicate"),
                "review_state": row.get("review_state"),
                "confidence": row.get("confidence"),
                "support_status": row.get("support_status"),
                "truth_basis": row.get("truth_basis"),
                "lifecycle_state": row.get("lifecycle_state"),
                "temporal_scope": row.get("temporal_scope"),
                "claim_text": row.get("claim_text"),
            }
            for row in sorted(
                pending_claims,
                key=lambda item: (
                    float(item.get("confidence") if isinstance(item.get("confidence"), (int, float)) else 1.0),
                    str(item.get("predicate") or ""),
                ),
            )[:5]
        ]

        return {
            "stem": stem,
            "path": str(path.relative_to(self.root)),
            "frontmatter": frontmatter,
            "body": body,
            "summary": extract_summary(text),
            "raw_path": frontmatter.get("raw_path"),
            "related_documents": related_documents,
            "related_versions": related_versions[:5],
            "incremental_status": incremental_status,
            "coverage": coverage,
            "knowledge_state_summary": knowledge_state_summary,
            "review_queue": review_queue,
            "related_pages": self.related_pages_for_stem(stem),
        }

    def warehouse_summary(self) -> dict[str, Any]:
        registries: list[dict[str, Any]] = []
        for name in JSONL_REGISTRIES:
            path = self.warehouse_jsonl_dir / f"{name}.jsonl"
            rows = read_jsonl(path)
            truth_class = "derived" if name == "derived_edges" else "canonical"
            registries.append(
                {
                    "key": name,
                    "path": str(path.relative_to(self.root)),
                    "truth_class": truth_class,
                    "count": len(rows),
                    "sample": rows[:2],
                }
            )

        return {
            "path": "warehouse/jsonl/",
            "registries": registries,
        }

    def recent_log(self, limit: int = 20) -> dict[str, Any]:
        log_path = self.meta_dir / "log.md"
        entries = parse_log_entries(read_text(log_path)) if log_path.exists() else []
        return {
            "path": "wiki/_meta/log.md",
            "entries": list(reversed(entries[-limit:])),
        }

    def run_action(self, action: str) -> dict[str, Any]:
        if action not in ACTION_COMMANDS:
            raise ValueError(f"Unknown action: {action}")

        process = subprocess.run(
            ACTION_COMMANDS[action],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        stdout_lines = [line for line in process.stdout.splitlines() if line.strip()]
        stderr_lines = [line for line in process.stderr.splitlines() if line.strip()]
        return {
            "action": action,
            "command": " ".join(ACTION_COMMANDS[action]),
            "exit_code": process.returncode,
            "stdout_lines": stdout_lines,
            "stderr_lines": stderr_lines,
            "summary": summarize_action_output(action, stdout_lines),
        }
