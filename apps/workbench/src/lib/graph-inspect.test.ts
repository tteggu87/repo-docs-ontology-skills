import assert from "node:assert/strict";
import test from "node:test";

import { buildGraphInspectSeeds, buildGraphInspectRequest, hasRenderableGraphHints } from "./graph-inspect";
import type { GraphInspectSeed, QueryGraphHints } from "./api";

test("buildGraphInspectSeeds exposes page, source, and claim seeds from current selections", () => {
  const seeds = buildGraphInspectSeeds({
    selectedPage: {
      stem: "graph-memory",
      path: "wiki/concepts/graph-memory.md",
      section: "concepts",
      frontmatter: {},
      body: "",
      summary: "Graph memory summary",
      related_pages: [{ stem: "operators", title: "Operators", summary: "Operator page", section: "entities", score: 3, reasons: [] }],
    },
    selectedSource: {
      stem: "source-alpha",
      path: "wiki/sources/source-alpha.md",
      frontmatter: {},
      body: "",
      summary: "Source summary",
      raw_path: "raw/inbox/source-alpha.md",
      related_documents: [],
      related_versions: [],
      incremental_status: null,
      coverage: {
        document_count: 1,
        version_count: 1,
        entity_count: 1,
        claim_count: 1,
        approved_claim_count: 0,
        pending_claim_count: 1,
        rejected_claim_count: 0,
        evidence_count: 1,
        segment_count: 1,
        needs_review_claim_count: 1,
        low_confidence_claim_count: 0,
      },
      review_queue: [
        {
          claim_id: "claim:graph-memory-supports-operators",
          review_state: "pending",
          claim_text: "Graph memory supports operators",
        },
      ],
      related_pages: [{ stem: "project-alpha", title: "Project Alpha", summary: "Project page", section: "projects", score: 4, reasons: [] }],
    },
  });

  const keys = seeds.map((seed) => seed.key);
  assert.ok(seeds.length >= 3);
  assert.match(keys.join(","), /page:graph-memory/);
  assert.match(keys.join(","), /source:source-alpha/);
  assert.match(keys.join(","), /claim:claim:graph-memory-supports-operators/);
});

test("buildGraphInspectRequest builds a stable query string for graph inspect calls", () => {
  const request = buildGraphInspectRequest({
    key: "page:graph-memory",
    type: "page",
    value: "graph-memory",
    title: "Graph Memory",
    subtitle: "wiki/concepts/graph-memory.md",
    description: "Open the selected wiki page in graph inspect.",
  });

  assert.equal(request, "/api/graph/inspect?seed_type=page&seed=graph-memory");
});


test("buildGraphInspectSeeds includes related page drilldowns for source and page contexts", () => {
  const seeds = buildGraphInspectSeeds({
    selectedPage: {
      stem: "graph-memory",
      path: "wiki/concepts/graph-memory.md",
      section: "concepts",
      frontmatter: {},
      body: "",
      summary: "Graph memory summary",
      related_pages: [{ stem: "operators", title: "Operators", summary: "Operator page", section: "entities", score: 3, reasons: [] }],
    },
    selectedSource: {
      stem: "source-alpha",
      path: "wiki/sources/source-alpha.md",
      frontmatter: {},
      body: "",
      summary: "Source summary",
      raw_path: "raw/inbox/source-alpha.md",
      related_documents: [],
      related_versions: [],
      incremental_status: null,
      coverage: {
        document_count: 1,
        version_count: 1,
        entity_count: 1,
        claim_count: 1,
        approved_claim_count: 0,
        pending_claim_count: 1,
        rejected_claim_count: 0,
        evidence_count: 1,
        segment_count: 1,
        needs_review_claim_count: 1,
        low_confidence_claim_count: 0,
      },
      review_queue: [],
      related_pages: [{ stem: "project-alpha", title: "Project Alpha", summary: "Project page", section: "projects", score: 4, reasons: [] }],
    },
  });

  const keys = seeds.map((seed) => seed.key);
  assert.match(keys.join(","), /page:operators/);
  assert.match(keys.join(","), /page:project-alpha/);
});

test("buildGraphInspectSeeds keeps query-preview claim seeds available for graph drilldown", () => {
  const querySeeds: GraphInspectSeed[] = [
    {
      key: "claim:claim:graph-memory-supports-operators",
      type: "claim",
      value: "claim:graph-memory-supports-operators",
      title: "Graph memory supports operators",
      subtitle: "claim seed",
      description: "From query preview graph hints",
    },
  ];

  const seeds = buildGraphInspectSeeds({
    selectedPage: null,
    selectedSource: null,
    querySeeds,
  });

  assert.deepEqual(seeds, querySeeds);
});

test("buildGraphInspectSeeds keeps manually requested seeds while payloads are still loading", () => {
  const extraSeeds: GraphInspectSeed[] = [
    {
      key: "page:future-page",
      type: "page",
      value: "future-page",
      title: "Future Page",
      subtitle: "pending page seed",
      description: "Requested before the page payload finished loading.",
    },
  ];

  const seeds = buildGraphInspectSeeds({
    selectedPage: null,
    selectedSource: null,
    querySeeds: [],
    extraSeeds,
  });

  assert.deepEqual(seeds, extraSeeds);
});

test("buildGraphInspectSeeds replaces pending overrides with loaded page metadata when available", () => {
  const extraSeeds: GraphInspectSeed[] = [
    {
      key: "page:graph-memory",
      type: "page",
      value: "graph-memory",
      title: "pending placeholder",
      subtitle: "pending page seed",
      description: "Requested before the page payload finished loading.",
    },
  ];

  const seeds = buildGraphInspectSeeds({
    selectedPage: {
      stem: "graph-memory",
      path: "wiki/concepts/graph-memory.md",
      section: "concepts",
      frontmatter: { title: "Graph Memory" },
      body: "",
      summary: "Graph memory summary",
      related_pages: [],
    },
    selectedSource: null,
    querySeeds: [],
    extraSeeds,
  });

  assert.equal(seeds[0]?.title, "Graph Memory");
  assert.equal(seeds[0]?.subtitle, "wiki/concepts/graph-memory.md");
});

test("buildGraphInspectSeeds exposes every review-queue claim for source drilldown", () => {
  const seeds = buildGraphInspectSeeds({
    selectedPage: null,
    selectedSource: {
      stem: "source-alpha",
      path: "wiki/sources/source-alpha.md",
      frontmatter: {},
      body: "",
      summary: "Source summary",
      raw_path: "raw/inbox/source-alpha.md",
      related_documents: [],
      related_versions: [],
      incremental_status: null,
      coverage: {
        document_count: 1,
        version_count: 1,
        entity_count: 5,
        claim_count: 5,
        approved_claim_count: 0,
        pending_claim_count: 5,
        rejected_claim_count: 0,
        evidence_count: 5,
        segment_count: 5,
        needs_review_claim_count: 5,
        low_confidence_claim_count: 0,
      },
      review_queue: Array.from({ length: 5 }, (_, index) => ({
        claim_id: `claim:test-${index + 1}`,
        review_state: "pending",
        claim_text: `Claim ${index + 1}`,
      })),
      related_pages: [],
    },
  });

  const keys = seeds.map((seed) => seed.key);
  assert.match(keys.join(","), /claim:claim:test-5/);
});

test("hasRenderableGraphHints hides empty-query sentinels and infra-only warnings, and shows real graph content", () => {
  const emptyQueryHints: QueryGraphHints = {
    available: false,
    summary: "Graph hints require a non-empty query.",
    related_nodes: [],
    path_hints: [],
    warnings: ["empty_query"],
    seeds: [],
  };
  const unavailableHints: QueryGraphHints = {
    available: false,
    summary: "Graph projection is unavailable for this query preview.",
    related_nodes: [],
    path_hints: [],
    warnings: ["graph_projection_empty"],
    seeds: [],
  };
  const availableHints: QueryGraphHints = {
    available: true,
    summary: "Graph hints are available for this query preview.",
    related_nodes: ["Graph Memory"],
    path_hints: [],
    warnings: [],
    seeds: [],
  };
  const seedOnlyHints: QueryGraphHints = {
    available: false,
    summary: "Graph inspect is configured, but no bounded neighborhood matched the current preview seeds.",
    related_nodes: [],
    path_hints: [],
    warnings: [],
    seeds: [
      {
        key: "page:future-page",
        type: "page",
        value: "future-page",
        title: "Future Page",
        subtitle: "pending page seed",
        description: "seed only",
      },
    ],
  };

  assert.equal(hasRenderableGraphHints(emptyQueryHints), false);
  assert.equal(hasRenderableGraphHints(unavailableHints), false);
  assert.equal(hasRenderableGraphHints(availableHints), true);
  assert.equal(hasRenderableGraphHints(seedOnlyHints), true);
});
