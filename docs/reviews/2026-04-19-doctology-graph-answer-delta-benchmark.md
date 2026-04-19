---
title: "DocTology graph answer-delta benchmark"
status: draft
created: 2026-04-19
updated: 2026-04-19
owner: "Hermes"
type: review
tags:
  - doctology
  - graph
  - benchmark
  - answer-delta
---

# DocTology graph answer-delta benchmark

## Goal

그래프 on/off가 query preview의 **실제 답변 문면**을 바꾸는지 확인한다.

## Summary

- Query count: **5**
- Answers changed: **5/5**
- with graph graph-signal count: **5**
- without graph graph-signal count: **0**
- with graph avg latency: **342.53ms**
- without graph avg latency: **39.82ms**
- avg latency delta: **+302.7ms**

### `little world little crab doctology comparison`

- Answer changed: **True**
- with graph avg: **335.31ms**
- without graph avg: **39.56ms**
- Graph signal (with): `- Graph signal: Source - my_project portfolio scan 2026-04-17 --mentions--> MCP`
- Graph signal (without): `none`
- Top graph paths (with):
  - Source - my_project portfolio scan 2026-04-17 --mentions--> MCP
  - Source - Chroma docs --mentions--> little-crab-storage-decision-duckdb-vs-sqlite-vs-neo4j
  - Source - my_project portfolio scan 2026-04-17 --mentions--> little-world-vs-little-crab-vs-doctology-comparison

#### Answer diff excerpt

```diff
--- with_graph
+++ without_graph
@@ -12,3 +12,2 @@
 - Claim review states in scope: approved `0`, needs_review `5`, rejected claims hidden.
-- Graph signal: Source - my_project portfolio scan 2026-04-17 --mentions--> MCP
 
@@ -35,22 +34 @@
 - segments: 5
-
-## Graph hints
-
-- Graph hints are available for this query preview.
```

### `opencrab ontology grammar promotion lifecycle`

- Answer changed: **True**
- with graph avg: **349.17ms**
- without graph avg: **38.81ms**
- Graph signal (with): `- Graph signal: OpenCrab ontology engine value collection 2026-04-19 --mentions--> BM25`
- Graph signal (without): `none`
- Top graph paths (with):
  - OpenCrab ontology engine value collection 2026-04-19 --mentions--> BM25
  - OpenCrab ontology engine value collection 2026-04-19 --mentions--> AlexAI-MCP
  - OpenCrab ontology engine value collection 2026-04-19 --mentions--> GraphRAG

#### Answer diff excerpt

```diff
--- with_graph
+++ without_graph
@@ -12,3 +12,2 @@
 - Claim review states in scope: approved `0`, needs_review `5`, rejected claims hidden.
-- Graph signal: OpenCrab ontology engine value collection 2026-04-19 --mentions--> BM25
 
@@ -35,22 +34 @@
 - segments: 5
-
-## Graph hints
-
-- Graph hints are available for this query preview.
```

### `opencrab ontology engine value collection`

- Answer changed: **True**
- with graph avg: **344.4ms**
- without graph avg: **40.16ms**
- Graph signal (with): `- Graph signal: OpenCrab ontology engine value collection 2026-04-19 --mentions--> BM25`
- Graph signal (without): `none`
- Top graph paths (with):
  - OpenCrab ontology engine value collection 2026-04-19 --mentions--> BM25
  - OpenCrab ontology engine value collection 2026-04-19 --mentions--> AlexAI-MCP
  - OpenCrab ontology engine value collection 2026-04-19 --mentions--> GraphRAG

#### Answer diff excerpt

```diff
--- with_graph
+++ without_graph
@@ -12,3 +12,2 @@
 - Claim review states in scope: approved `0`, needs_review `5`, rejected claims hidden.
-- Graph signal: OpenCrab ontology engine value collection 2026-04-19 --mentions--> BM25
 
@@ -35,22 +34 @@
 - segments: 5
-
-## Graph hints
-
-- Graph hints are available for this query preview.
```

### `why ontology engine over plain RAG`

- Answer changed: **True**
- with graph avg: **343.8ms**
- without graph avg: **40.95ms**
- Graph signal (with): `- Graph signal: External best practices for ontology engines 2026-04-19 --documents--> - SHACL Use Cases and Requirements`
- Graph signal (without): `none`
- Top graph paths (with):
  - External best practices for ontology engines 2026-04-19 --documents--> - SHACL Use Cases and Requirements
  - External best practices for ontology engines 2026-04-19 --documents--> - collected: 2026-04-19 - scope: papers, standards, blogs, open-source-adjacent materials, Reddit signals

#### Answer diff excerpt

```diff
--- with_graph
+++ without_graph
@@ -12,3 +12,2 @@
 - Claim review states in scope: approved `0`, needs_review `5`, rejected claims hidden.
-- Graph signal: External best practices for ontology engines 2026-04-19 --documents--> - SHACL Use Cases and Requirements
 
@@ -35,19 +34 @@
 - segments: 5
-
-## Graph hints
-
-- Graph hints are available for this query preview.
```

### `ontology engine best practices shacl provenance`

- Answer changed: **True**
- with graph avg: **339.95ms**
- without graph avg: **39.64ms**
- Graph signal (with): `- Graph signal: External best practices for ontology engines 2026-04-19 --documents--> - SHACL Use Cases and Requirements`
- Graph signal (without): `none`
- Top graph paths (with):
  - External best practices for ontology engines 2026-04-19 --documents--> - SHACL Use Cases and Requirements
  - External best practices for ontology engines 2026-04-19 --documents--> - collected: 2026-04-19 - scope: papers, standards, blogs, open-source-adjacent materials, Reddit signals

#### Answer diff excerpt

```diff
--- with_graph
+++ without_graph
@@ -12,3 +12,2 @@
 - Claim review states in scope: approved `0`, needs_review `5`, rejected claims hidden.
-- Graph signal: External best practices for ontology engines 2026-04-19 --documents--> - SHACL Use Cases and Requirements
 
@@ -35,19 +34 @@
 - segments: 5
-
-## Graph hints
-
-- Graph hints are available for this query preview.
```

