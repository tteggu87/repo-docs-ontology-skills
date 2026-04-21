import type { GraphInspectSeed, QueryGraphHints, SourceDetailPayload, WikiPagePayload } from "./api";

type BuildGraphInspectSeedsInput = {
  selectedPage: WikiPagePayload | null;
  selectedSource: SourceDetailPayload | null;
  querySeeds?: GraphInspectSeed[];
  extraSeeds?: GraphInspectSeed[];
};

function pushSeed(seeds: GraphInspectSeed[], seed: GraphInspectSeed) {
  if (!seeds.some((item) => item.key === seed.key)) {
    seeds.push(seed);
  }
}

export function hasRenderableGraphHints(graphHints: QueryGraphHints | null | undefined): boolean {
  if (!graphHints) {
    return false;
  }
  if ((graphHints.warnings ?? []).includes("empty_query")) {
    return false;
  }
  return Boolean(graphHints.available || graphHints.related_nodes.length || graphHints.path_hints.length || graphHints.seeds.length);
}

export function buildGraphInspectSeeds({
  selectedPage,
  selectedSource,
  querySeeds = [],
  extraSeeds = [],
}: BuildGraphInspectSeedsInput): GraphInspectSeed[] {
  const seeds: GraphInspectSeed[] = [];

  if (selectedPage) {
    pushSeed(seeds, {
      key: `page:${selectedPage.stem}`,
      type: "page",
      value: selectedPage.stem,
      title: selectedPage.frontmatter.title ? String(selectedPage.frontmatter.title) : selectedPage.stem,
      subtitle: selectedPage.path,
      description: "Open the selected wiki page in graph inspect.",
    });

    for (const item of selectedPage.related_pages.slice(0, 3)) {
      pushSeed(seeds, {
        key: `page:${item.stem}`,
        type: "page",
        value: item.stem,
        title: item.title,
        subtitle: `${item.section} · related page`,
        description: "Inspect a related page neighborhood from the current page context.",
      });
    }
  }

  if (selectedSource) {
    pushSeed(seeds, {
      key: `source:${selectedSource.stem}`,
      type: "source",
      value: selectedSource.stem,
      title: selectedSource.frontmatter.title ? String(selectedSource.frontmatter.title) : selectedSource.stem,
      subtitle: selectedSource.path,
      description: "Inspect graph context around the selected source page.",
    });

    for (const item of selectedSource.related_pages.slice(0, 3)) {
      pushSeed(seeds, {
        key: `page:${item.stem}`,
        type: "page",
        value: item.stem,
        title: item.title,
        subtitle: `${item.section} · from source context`,
        description: "Drill down from the selected source into a related entity/project/concept page.",
      });
    }

    for (const item of selectedSource.review_queue) {
      const value = item.claim_id.trim();
      if (!value) continue;
      pushSeed(seeds, {
        key: `claim:${value}`,
        type: "claim",
        value,
        title: item.claim_text?.trim() || value,
        subtitle: `review: ${item.review_state ?? "unknown"}`,
        description: "Inspect the selected review-queue claim in graph space.",
      });
    }
  }

  for (const seed of querySeeds) {
    pushSeed(seeds, seed);
  }
  for (const seed of extraSeeds) {
    pushSeed(seeds, seed);
  }

  return seeds;
}

export function buildGraphInspectRequest(seed: GraphInspectSeed): string {
  const params = new URLSearchParams({ seed_type: seed.type, seed: seed.value });
  return `/api/graph/inspect?${params.toString()}`;
}
