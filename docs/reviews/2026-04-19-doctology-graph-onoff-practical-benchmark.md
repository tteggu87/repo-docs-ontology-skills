---
title: "DocTology graph on/off practical benchmark"
status: draft
created: 2026-04-19
updated: 2026-04-19
owner: "Hermes"
type: review
tags:
  - doctology
  - graph
  - benchmark
  - query-preview
---

# DocTology graph on/off practical benchmark

## Summary

- Query count: **10**
- with graph avg latency: **337.06ms**
- without graph avg latency: **39.43ms**
- avg latency delta: **+297.63ms**
- with graph graph signal count: **7**
- without graph graph signal count: **0**

### `neo4j kuzu ladybug graph truth layer`

- with graph avg: **330.91ms**
- without graph avg: **38.69ms**
- with graph signal: `- Graph signal: Source - Playground portfolio scan 2026-04-17 --mentions--> RAG`
- without graph signal: `none`
- top graph paths (with):
  - Source - Playground portfolio scan 2026-04-17 --mentions--> RAG
  - Source - Playground portfolio scan 2026-04-17 --mentions--> AutoRAG
  - Source - Playground portfolio scan 2026-04-17 --mentions--> GraphRAG

### `ontology validation provenance human review`

- with graph avg: **337.69ms**
- without graph avg: **40.41ms**
- with graph signal: `none`
- without graph signal: `none`
- top graph paths (with):

### `opencrab ontology grammar promotion lifecycle`

- with graph avg: **349.52ms**
- without graph avg: **39.43ms**
- with graph signal: `- Graph signal: OpenCrab ontology engine value collection 2026-04-19 --mentions--> BM25`
- without graph signal: `none`
- top graph paths (with):
  - OpenCrab ontology engine value collection 2026-04-19 --mentions--> BM25
  - OpenCrab ontology engine value collection 2026-04-19 --mentions--> AlexAI-MCP
  - OpenCrab ontology engine value collection 2026-04-19 --mentions--> GraphRAG

### `little world little crab doctology comparison`

- with graph avg: **337.09ms**
- without graph avg: **39.14ms**
- with graph signal: `- Graph signal: Source - my_project portfolio scan 2026-04-17 --mentions--> MCP`
- without graph signal: `none`
- top graph paths (with):
  - Source - my_project portfolio scan 2026-04-17 --mentions--> MCP
  - Source - Chroma docs --mentions--> little-crab-storage-decision-duckdb-vs-sqlite-vs-neo4j
  - Source - my_project portfolio scan 2026-04-17 --mentions--> little-world-vs-little-crab-vs-doctology-comparison

### `playground portfolio ontology graphrag fit`

- with graph avg: **340.17ms**
- without graph avg: **39.11ms**
- with graph signal: `- Graph signal: External best practices for ontology engines 2026-04-19 --documents--> - SHACL Use Cases and Requirements`
- without graph signal: `none`
- top graph paths (with):
  - External best practices for ontology engines 2026-04-19 --documents--> - SHACL Use Cases and Requirements
  - External best practices for ontology engines 2026-04-19 --documents--> - collected: 2026-04-19 - scope: papers, standards, blogs, open-source-adjacent materials, Reddit signals

### `canonical truth vs graph projection`

- with graph avg: **332.58ms**
- without graph avg: **38.99ms**
- with graph signal: `none`
- without graph signal: `none`
- top graph paths (with):

### `graph inspect sidecar ROI`

- with graph avg: **331.76ms**
- without graph avg: **40.17ms**
- with graph signal: `none`
- without graph signal: `none`
- top graph paths (with):

### `kuzu docs vector fts extension`

- with graph avg: **334.46ms**
- without graph avg: **40.04ms**
- with graph signal: `- Graph signal: Source - Chroma docs --mentions--> Chroma`
- without graph signal: `none`
- top graph paths (with):
  - Source - Chroma docs --mentions--> Chroma
  - Source - Chroma docs --mentions--> Chroma Docs
  - Snapshot: Chroma presents itself as open-source data infrastructure for AI, with support for document storage, embeddings, dense/sparse/hybrid vector search, full-text and regex search, metadata filtering, and multimodal retrieval. --about_subject--> Chroma

### `ladybug derived runtime vs truth owner`

- with graph avg: **333.13ms**
- without graph avg: **38.8ms**
- with graph signal: `- Graph signal: (dbtype duckdb)`, showing interoperability between a graph runtime and DuckDB files. --about_subject--> DuckDB`
- without graph signal: `none`
- top graph paths (with):
  - (dbtype duckdb)`, showing interoperability between a graph runtime and DuckDB files. --about_subject--> DuckDB

### `why ontology engine over plain RAG`

- with graph avg: **343.32ms**
- without graph avg: **39.52ms**
- with graph signal: `- Graph signal: External best practices for ontology engines 2026-04-19 --documents--> - SHACL Use Cases and Requirements`
- without graph signal: `none`
- top graph paths (with):
  - External best practices for ontology engines 2026-04-19 --documents--> - SHACL Use Cases and Requirements
  - External best practices for ontology engines 2026-04-19 --documents--> - collected: 2026-04-19 - scope: papers, standards, blogs, open-source-adjacent materials, Reddit signals

