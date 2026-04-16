export type AskSurfaceState = {
  mode: "deferred";
  title: string;
  description: string;
  notes: string[];
};

export function buildAskSurface(): AskSurfaceState {
  return {
    mode: "deferred",
    title: "Ask is deferred until a repo-safe contract exists.",
    description:
      "The extracted browser-side Gemini flow is intentionally not copied here. A future Ask surface must either stay repo-local and non-generative or move behind an explicit backend-mediated contract.",
    notes: [
      "No browser-side model secrets.",
      "No fake chat box that mutates or hallucinates over canonical truth.",
      "For now, use Pages, Sources, and Warehouse as the trusted reading path.",
    ],
  };
}
