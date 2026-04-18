---
title: "Source - Kuzu docs corpus scan 2026-04-18"
type: source
status: active
created: 2026-04-18
updated: 2026-04-18
raw_path: "raw/processed/2026-04-18-external-research-backfill/by-source/kuzu-docs.md"
tags:
  - source
  - kuzu
  - docs
  - corpus
---

# Source - Kuzu docs corpus scan 2026-04-18

## Source Metadata

- Raw path: `raw/processed/2026-04-18-external-research-backfill/by-source/kuzu-docs.md`
- Docs root: https://kuzudb.github.io/docs/
- Sitemap index: https://kuzudb.github.io/docs/sitemap-index.xml
- Coverage date: 2026-04-18
- Retrieval method:
  - direct site fetch
  - sitemap parsing
  - `insane-search` style fallback with Jina where useful

## Coverage Summary

- Total docs URLs found in sitemap: **148**

Top-level category counts:

- `cypher`: 64
- `extensions`: 26
- `client-apis`: 15
- `developer-guide`: 9
- `import`: 8
- `visualization`: 7
- `get-started`: 5
- `tutorials`: 5
- `export`: 4
- `home`: 1
- `concurrency`: 1
- `installation`: 1
- `migrate`: 1
- `system-requirements`: 1

## Key Themes From The Docs

### 1) Kuzu is presented as an embeddable property graph database

The docs consistently frame Kuzu as:

- embedded / in-process
- property graph
- Cypher-based
- developer-friendly through many language APIs

### 2) Kuzu has broad Cypher and query-language surface area

The `cypher/` section is by far the largest category in the docs corpus.
This indicates Kuzu positions itself not as a toy runtime but as a serious query engine.

### 3) Extensions are a major part of the product story

The docs give first-class space to:

- vector
- full-text search
- attach integrations
- cloud/object storage
- algorithms
- LLM-related extension

### 4) Interoperability is central

The docs include attach/migration paths for:

- DuckDB
- SQLite
- Postgres
- Neo4j
- Delta / Iceberg / Unity

## Important Pages For Our Decisions

- Home: https://kuzudb.github.io/docs/
- Vector extension: https://kuzudb.github.io/docs/extensions/vector/
- Full-text search: https://kuzudb.github.io/docs/extensions/full-text-search/
- DuckDB attach: https://kuzudb.github.io/docs/extensions/attach/duckdb/
- SQLite attach: https://kuzudb.github.io/docs/extensions/attach/sqlite/
- Neo4j extension: https://kuzudb.github.io/docs/extensions/neo4j/
- Python client API: https://kuzudb.github.io/docs/client-apis/python/
- Concurrency: https://kuzudb.github.io/docs/concurrency/

## Important Claims

- Kuzu’s official docs treat vector search and FTS as supported extensions.
- Kuzu’s docs give strong weight to interoperability with other data engines, especially DuckDB and SQLite.
- The docs corpus is broad enough to support a serious embedded graph runtime story, not just a small library wrapper.

## Contradictions Or Uncertainty

- The docs alone do not prove Kuzu should be the truth owner in a product. They do strongly support the case that Kuzu is a good embedded graph runtime.

## Affected Pages

- [[kuzu-docs-blog-deep-research-2026-04-18]]
- [[neo4j-vs-kuzu-vs-ladybug-for-graph-truth-layer]]
- [[ontology-graph-truth-layer-and-recommended-stack]]
