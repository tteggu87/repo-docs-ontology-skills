import type { WorkbenchSummary } from "./api";

export type GraphRendererMode = "empty" | "bounded-neighborhood";

export type GraphSurfaceState = {
  mode: GraphRendererMode;
  title: string;
  description: string;
  sourcePath: string;
  notes: string[];
};

export function buildGraphSurface(summary: WorkbenchSummary | null): GraphSurfaceState {
  const sourcePath = summary?.graph_projection.path ?? "warehouse/graph_projection/";

  if (!summary?.graph_projection.available) {
    return {
      mode: "empty",
      title: "No graph projection is available yet.",
      description:
        "This repo is still running without real projection artifacts, so the graph renderer stays in an explicit empty state instead of pretending the whole corpus is a graph UI.",
      sourcePath,
      notes: [
        "Graph remains derived, read-only, and secondary to wiki plus canonical JSONL.",
        "Any future renderer should start with bounded neighborhood drill-down, not whole-corpus spectacle.",
        "Ask flows stay outside the graph until a backend-mediated or repo-local contract is ready.",
      ],
    };
  }

  return {
    mode: "bounded-neighborhood",
    title: "Graph projection artifacts are available.",
    description:
      "The renderer contract is ready for bounded neighborhood exploration, but graph remains a drill-down surface rather than the default way to read the repo.",
    sourcePath,
    notes: [
      "Only derived graph projection artifacts may feed the renderer.",
      "The renderer should stay isolated from backend query orchestration.",
      "Neighborhood-first exploration is preferred over loading the full graph by default.",
    ],
  };
}
