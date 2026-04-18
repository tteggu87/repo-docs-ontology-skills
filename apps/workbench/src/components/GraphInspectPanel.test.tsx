import assert from "node:assert/strict";
import test from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import type { GraphInspectPayload, GraphInspectSeed } from "../lib/api";
import { GraphInspectPanel } from "./GraphInspectPanel";

const seeds: GraphInspectSeed[] = [
  {
    key: "page:graph-memory",
    type: "page",
    value: "graph-memory",
    title: "Graph Memory",
    subtitle: "wiki/concepts/graph-memory.md",
    description: "Open the selected wiki page in graph inspect.",
  },
];

test("GraphInspectPanel renders unavailable state with explicit fallback copy", () => {
  const inspect: GraphInspectPayload = {
    mode: "unavailable",
    seed: { type: "page", value: "graph-memory", label: "Graph Memory" },
    summary: "Graph projection is unavailable.",
    source_path: "warehouse/graph_projection/",
    neighborhood: { node_count: 0, edge_count: 0, nodes: [], edges: [] },
    path_hints: [],
    warnings: ["graph_projection_empty"],
  };

  const html = renderToStaticMarkup(
    GraphInspectPanel({
      seeds,
      activeSeedKey: seeds[0]?.key ?? null,
      inspect,
      loading: false,
      error: null,
      onInspect: () => undefined,
    }),
  );

  assert.match(html, /Graph projection is unavailable\./);
  assert.match(html, /No bounded neighborhood is available yet\./);
});

test("GraphInspectPanel renders graph counts and path hints when graph data is available", () => {
  const inspect: GraphInspectPayload = {
    mode: "available",
    seed: { type: "claim", value: "claim:graph-memory-supports-operators", label: "Graph memory supports operators" },
    summary: "Found a bounded neighborhood.",
    source_path: "warehouse/graph_projection/",
    neighborhood: {
      node_count: 3,
      edge_count: 2,
      nodes: [
        { id: "entity:graph-memory", label: "Graph Memory", kind: "entity", matched: true },
        { id: "claim:graph-memory-supports-operators", label: "Graph memory supports operators", kind: "claim", matched: true },
        { id: "entity:operators", label: "Operators", kind: "entity", matched: false },
      ],
      edges: [
        { source: "entity:graph-memory", target: "claim:graph-memory-supports-operators", label: "supports" },
        { source: "claim:graph-memory-supports-operators", target: "entity:operators", label: "about" },
      ],
    },
    path_hints: ["Graph Memory --supports--> Graph memory supports operators"],
    warnings: [],
  };

  const html = renderToStaticMarkup(
    GraphInspectPanel({
      seeds,
      activeSeedKey: seeds[0]?.key ?? null,
      inspect,
      loading: false,
      error: null,
      onInspect: () => undefined,
    }),
  );

  assert.match(html, /node count/i);
  assert.match(html, /edge count/i);
  assert.match(html, /Graph Memory/);
  assert.match(html, /supports/);
});
