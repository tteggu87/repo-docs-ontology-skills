import assert from "node:assert/strict";
import test from "node:test";

import { buildGraphInspectSeeds, buildGraphInspectRequest } from "./graph-inspect";

test("buildGraphInspectSeeds exposes page, source, and claim seeds from current selections", () => {
  const seeds = buildGraphInspectSeeds({
    selectedPage: {
      stem: "graph-memory",
      path: "wiki/concepts/graph-memory.md",
      section: "concepts",
      frontmatter: {},
      body: "",
      summary: "Graph memory summary",
      related_pages: [],
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
      related_pages: [],
    },
  });

  assert.equal(seeds.length, 3);
  assert.equal(seeds[0]?.type, "page");
  assert.equal(seeds[1]?.type, "source");
  assert.equal(seeds[2]?.type, "claim");
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
