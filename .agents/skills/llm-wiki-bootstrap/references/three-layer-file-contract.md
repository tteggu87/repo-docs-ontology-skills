# Three-Layer File Contract

This reference defines the preferred file-layer layout for a wiki-first, file-canonical LLM Wiki.

## Directory layout

```text
wiki/
  pages/
    concepts/
    entities/
    people/
    projects/
    timelines/
    analyses/
  sources/
    raw/
      web/
      notes/
      chats/
      pdf_text/
    manifests/
      source_manifest.jsonl
  schemas/
    page.schema.yaml
    claim.schema.yaml
    relation.schema.yaml
  policies/
    AGENTS.md
    naming_rules.md
    linking_rules.md
    extraction_policy.yaml
    routing_policy.yaml
  exports/
    claims.jsonl
    relations.jsonl
    entities.jsonl
    ingest_runs.jsonl
  state/
    wiki_index.sqlite
    analytics.duckdb
```

## Surface semantics

- `pages/` = maintained human-facing synthesis
- `sources/raw/` = evidence-bearing source artifacts
- `sources/manifests/` = machine-readable source registry
- `schemas/` = structural contracts
- `policies/` = human-readable rules
- `exports/` = machine-readable, rebuildable artifacts
- `state/` = non-canonical operational and analytical databases

## Guardrails

1. files remain the canonical write surface
2. raw source should not be destructively overwritten
3. state databases must remain rebuildable
4. exports should be explicit and role-specific, not generic dumps

