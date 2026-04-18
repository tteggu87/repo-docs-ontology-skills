---
title: "Source - Kuzu docs"
type: source
status: superseded
created: 2026-04-17
updated: 2026-04-18
raw_path: ""
tags:
  - source
  - kuzu
  - graph
  - docs
---

# Source - Kuzu docs

## Source Metadata

- Raw path: superseded by `[[source-kuzu-docs-corpus-scan-2026-04-18]]` for canonical raw-backed coverage
- URL: https://kuzudb.com/docs
- Related URLs:
  - https://docs.kuzudb.com/extensions/vector/
  - https://docs.kuzudb.com/extensions/full-text-search/
- Retrieved: 2026-04-17
- Source type: official docs

## Summary

Kuzu는 embedded property graph database로 설명되며, Cypher, ACID transactions, columnar storage, DuckDB/Parquet/Arrow interoperability, vector index, FTS extension을 제공한다.

## Key Facts

- embedded (in-process) graph DB
- property graph model + Cypher
- DuckDB, Arrow, Parquet와 상호운용 가능
- vector extension 제공
- full-text search extension 제공

## Important Claims

- analytical query workloads on large graphs에 최적화되었다고 설명한다.
- vector와 FTS가 extension 형태로 공식 지원된다.

## Contradictions Or Uncertainty

- 개인용 기본값으로 유용해 보이지만, 실제 graph truth owner로 둘지 support runtime으로 둘지는 제품 요구에 따라 달라진다.
- 이 페이지는 초기 요약 소스이며, canonical raw-backed coverage는 `[[source-kuzu-docs-corpus-scan-2026-04-18]]`를 우선한다.

## Affected Pages

- [[ontology-graph-truth-layer-and-recommended-stack]]
