import type { GraphInspectSeed, SourceDetailPayload, WikiPagePayload } from "./api";

type BuildGraphInspectSeedsInput = {
  selectedPage: WikiPagePayload | null;
  selectedSource: SourceDetailPayload | null;
};

export function buildGraphInspectSeeds({
  selectedPage,
  selectedSource,
}: BuildGraphInspectSeedsInput): GraphInspectSeed[] {
  const seeds: GraphInspectSeed[] = [];

  if (selectedPage) {
    seeds.push({
      key: `page:${selectedPage.stem}`,
      type: "page",
      value: selectedPage.stem,
      title: selectedPage.frontmatter.title ? String(selectedPage.frontmatter.title) : selectedPage.stem,
      subtitle: selectedPage.path,
      description: "Open the selected wiki page in graph inspect.",
    });
  }

  if (selectedSource) {
    seeds.push({
      key: `source:${selectedSource.stem}`,
      type: "source",
      value: selectedSource.stem,
      title: selectedSource.frontmatter.title ? String(selectedSource.frontmatter.title) : selectedSource.stem,
      subtitle: selectedSource.path,
      description: "Inspect graph context around the selected source page.",
    });

    for (const item of selectedSource.review_queue.slice(0, 3)) {
      const value = item.claim_id.trim();
      if (!value) continue;
      seeds.push({
        key: `claim:${value}`,
        type: "claim",
        value,
        title: item.claim_text?.trim() || value,
        subtitle: `review: ${item.review_state ?? "unknown"}`,
        description: "Inspect the selected review-queue claim in graph space.",
      });
    }
  }

  return seeds;
}

export function buildGraphInspectRequest(seed: GraphInspectSeed): string {
  const params = new URLSearchParams({ seed_type: seed.type, seed: seed.value });
  return `/api/graph/inspect?${params.toString()}`;
}
