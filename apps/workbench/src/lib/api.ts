export type WorkbenchSummary = {
  root: string;
  raw: {
    counts: Record<string, number>;
  };
  wiki: {
    page_count: number;
    section_count: number;
    index_entry_count: number;
    log_entry_count: number;
  };
  warehouse: {
    registry_counts: Record<string, number>;
  };
  graph_projection: {
    path: string;
    file_count: number;
    available: boolean;
  };
  warnings: string[];
};

export type WikiIndexEntry = {
  stem: string;
  title?: string;
  summary: string;
};

export type WikiIndexSection = {
  name: string;
  entries: WikiIndexEntry[];
};

export type WikiIndexPayload = {
  path: string;
  sections: WikiIndexSection[];
};

export type WikiPagePayload = {
  stem: string;
  path: string;
  section: string;
  frontmatter: Record<string, unknown>;
  body: string;
  summary: string;
  related_pages: RelatedPage[];
};

export type SourceDetailPayload = {
  stem: string;
  path: string;
  frontmatter: Record<string, unknown>;
  body: string;
  summary: string;
  raw_path?: string;
  related_documents: Record<string, unknown>[];
  related_versions: Record<string, unknown>[];
  incremental_status:
    | {
        document_id?: string | null;
        source_family_id?: string | null;
        source_kind?: string | null;
        latest_export_version_id?: string | null;
        supersedes_export_version_id?: string | null;
        message_count?: number | null;
        new_message_count?: number | null;
        unchanged_message_count?: number | null;
        incremental_status_page?: string | null;
        affected_registry_paths?: string[];
        affected_wiki_paths?: string[];
      }
    | null;
  coverage: {
    document_count: number;
    version_count: number;
    entity_count: number;
    claim_count: number;
    approved_claim_count: number;
    pending_claim_count: number;
    rejected_claim_count: number;
    evidence_count: number;
    segment_count: number;
    needs_review_claim_count: number;
    low_confidence_claim_count: number;
  };
  review_queue: {
    claim_id: string;
    predicate?: string;
    review_state?: string;
    confidence?: number;
    claim_text?: string;
  }[];
  related_pages: RelatedPage[];
};

export type WarehouseRegistry = {
  key: string;
  path: string;
  truth_class: string;
  count: number;
  sample: Record<string, unknown>[];
};

export type WarehouseSummaryPayload = {
  path: string;
  registries: WarehouseRegistry[];
};

export type LogEntry = {
  date: string;
  kind: string;
  title: string;
  bullets: string[];
};

export type RecentLogPayload = {
  path: string;
  entries: LogEntry[];
};

export type RelatedPage = {
  stem: string;
  title: string;
  section: string;
  summary: string;
  score: number;
  reasons: string[];
};

export type WorkbenchFeedItem = {
  stem: string;
  title: string;
  summary: string;
  updated: string | null;
  path: string;
};

export type WorkbenchFeedPayload = {
  recent_sources: WorkbenchFeedItem[];
  recent_analyses: WorkbenchFeedItem[];
};

export type ReviewItem = {
  stem: string;
  title: string;
  section: string;
  line_count?: number;
  reason?: string;
  updated?: string | null;
  age_days?: number | null;
  graph_hint?: string;
};

export type WorkbenchReviewPayload = {
  oversized_pages: ReviewItem[];
  low_coverage_pages: ReviewItem[];
  uncertainty_candidates: ReviewItem[];
  stale_pages: ReviewItem[];
  low_confidence_claims: {
    claim_id: string;
    document_id?: string;
    source_page?: string;
    subject_id?: string;
    review_state: string;
    confidence: number | null;
    claim_text?: string;
    graph_hint?: string;
  }[];
};

export type ProvenanceSection = {
  label: string;
  count: number;
  items: Record<string, unknown>[];
};

export type QueryGraphHints = {
  available: boolean;
  summary: string;
  related_nodes: string[];
  path_hints: string[];
  warnings: string[];
  seeds: GraphInspectSeed[];
};

export type QueryContractLayer = {
  name: "wiki_pages" | "source_pages" | "canonical_jsonl" | "graph_projection";
  used: boolean;
  count: number;
};

export type QueryContract = {
  route: "repo_local_search";
  truth_layers: QueryContractLayer[];
  fallback_reason: string | null;
  save_readiness: "ready" | "review_required" | "blocked";
  save_reason: string;
};

export type QueryPreviewPayload = {
  mode: "repo_local_search";
  question: string;
  tokens: string[];
  coverage: "none" | "thin" | "supported";
  answer_markdown: string;
  related_pages: RelatedPage[];
  related_sources: RelatedPage[];
  provenance_sections: ProvenanceSection[];
  warnings: string[];
  graph_hints: QueryGraphHints;
  contract: QueryContract;
};

export type GraphInspectSeed = {
  key: string;
  type: "page" | "source" | "claim";
  value: string;
  title: string;
  subtitle: string;
  description: string;
};

export type GraphInspectNode = {
  id: string;
  label: string;
  kind: string;
  matched: boolean;
};

export type GraphInspectEdge = {
  source: string;
  target: string;
  label: string;
};

export type GraphInspectPayload = {
  mode: "unavailable" | "empty" | "available";
  seed: {
    type: "page" | "source" | "claim";
    value: string;
    label: string;
  };
  summary: string;
  source_path: string;
  neighborhood: {
    node_count: number;
    edge_count: number;
    nodes: GraphInspectNode[];
    edges: GraphInspectEdge[];
  };
  path_hints: string[];
  warnings: string[];
};

export type SaveAnalysisPayload = {
  action: "save_analysis";
  question: string;
  analysis_stem: string;
  analysis_path: string;
  changed_files: string[];
  linked_pages: string[];
  preview: QueryPreviewPayload;
};

export type ReviewClaimPayload = {
  action: "review_claim";
  claim_id: string;
  review_state: "approved" | "rejected";
  changed_files: string[];
  claim: Record<string, unknown>;
};

export type DraftSourceSummaryPayload = {
  action: "draft_source_summary";
  source_stem: string;
  source_path: string;
  raw_path: string;
  draft_markdown: string;
  helper_model: {
    config_source?: string;
    model_title?: string;
    provider?: string;
  };
  changed_files: string[];
  warnings: string[];
};

export type WorkbenchActionKey = "status" | "reindex" | "lint" | "doctor";

export type StatusActionSummary = {
  kind: "status";
  metrics: Record<string, string>;
};

export type LintActionSummary = {
  kind: "lint";
  hard_failures: Record<string, string>;
  advisory_warnings: Record<string, string>;
};

export type DoctorActionSummary = {
  kind: "doctor";
  raw_counts: Record<string, number>;
  wiki_health: Record<string, number>;
  source_page_health: {
    missing_raw_path_count: number;
    missing_raw_path_pages: string[];
    duplicate_raw_path_owners: Array<{
      raw_path: string;
      owners: string[];
    }>;
  };
  warehouse_counts: Record<string, number>;
  graph_projection: {
    available: boolean;
    node_count: number;
    edge_count: number;
    warnings: string[];
  };
  docs_readiness: Record<string, boolean>;
  working_tree: {
    clean: boolean;
    counts: Record<string, number>;
  };
  operator_readiness: {
    production_ingest_entrypoint_exists: boolean;
    benchmark_ingest_entrypoint_exists: boolean;
    shadow_reconcile_preview_exists: boolean;
    canonical_truth_nonempty: boolean;
    recommended_next_steps: string[];
  };
};

export type GenericActionSummary = {
  kind: string;
  messages: string[];
};

export type WorkbenchActionSummary = StatusActionSummary | LintActionSummary | DoctorActionSummary | GenericActionSummary;

export type WorkbenchActionPayload = {
  action: WorkbenchActionKey;
  command: string;
  exit_code: number;
  stdout_lines: string[];
  stderr_lines: string[];
  summary: WorkbenchActionSummary;
};

async function fetchJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal });
  if (!response.ok) {
    throw new Error(`${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchWorkbenchSummary(signal?: AbortSignal): Promise<WorkbenchSummary> {
  return fetchJson<WorkbenchSummary>("/api/workbench/summary", signal);
}

export async function fetchWorkbenchFeed(limit = 5, signal?: AbortSignal): Promise<WorkbenchFeedPayload> {
  return fetchJson<WorkbenchFeedPayload>(`/api/workbench/feed?limit=${limit}`, signal);
}

export async function fetchWorkbenchReview(limit = 5, signal?: AbortSignal): Promise<WorkbenchReviewPayload> {
  return fetchJson<WorkbenchReviewPayload>(`/api/workbench/review?limit=${limit}`, signal);
}

export async function fetchWikiIndex(signal?: AbortSignal): Promise<WikiIndexPayload> {
  return fetchJson<WikiIndexPayload>("/api/wiki/index", signal);
}

export async function fetchWikiPage(stem: string, signal?: AbortSignal): Promise<WikiPagePayload> {
  return fetchJson<WikiPagePayload>(`/api/wiki/page/${encodeURIComponent(stem)}`, signal);
}

export async function fetchSourceDetail(stem: string, signal?: AbortSignal): Promise<SourceDetailPayload> {
  return fetchJson<SourceDetailPayload>(`/api/sources/${encodeURIComponent(stem)}`, signal);
}

export async function fetchWarehouseSummary(signal?: AbortSignal): Promise<WarehouseSummaryPayload> {
  return fetchJson<WarehouseSummaryPayload>("/api/warehouse/summary", signal);
}

export async function fetchRecentLog(limit = 4, signal?: AbortSignal): Promise<RecentLogPayload> {
  return fetchJson<RecentLogPayload>(`/api/meta/log/recent?limit=${limit}`, signal);
}

export async function fetchQueryPreview(
  question: string,
  limit = 5,
  signal?: AbortSignal,
): Promise<QueryPreviewPayload> {
  const params = new URLSearchParams({ q: question, limit: String(limit) });
  return fetchJson<QueryPreviewPayload>(`/api/query/preview?${params.toString()}`, signal);
}


export async function fetchGraphInspect(
  seedType: GraphInspectSeed["type"],
  seed: string,
  signal?: AbortSignal,
): Promise<GraphInspectPayload> {
  const params = new URLSearchParams({ seed_type: seedType, seed });
  return fetchJson<GraphInspectPayload>(`/api/graph/inspect?${params.toString()}`, signal);
}

export async function saveAnalysis(question: string, limit = 5): Promise<SaveAnalysisPayload> {
  const response = await fetch("/api/actions/save-analysis", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, limit }),
  });
  if (!response.ok) {
    throw new Error(`/api/actions/save-analysis failed with ${response.status}`);
  }
  return response.json() as Promise<SaveAnalysisPayload>;
}

export async function reviewClaim(
  claimId: string,
  reviewState: "approved" | "rejected",
): Promise<ReviewClaimPayload> {
  const response = await fetch("/api/actions/review-claim", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ claim_id: claimId, review_state: reviewState }),
  });
  if (!response.ok) {
    throw new Error(`/api/actions/review-claim failed with ${response.status}`);
  }
  return response.json() as Promise<ReviewClaimPayload>;
}

export async function draftSourceSummary(
  sourceStem: string,
  maxChars = 12000,
): Promise<DraftSourceSummaryPayload> {
  const response = await fetch("/api/actions/draft-source-summary", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ source_stem: sourceStem, max_chars: maxChars }),
  });
  if (!response.ok) {
    throw new Error(`/api/actions/draft-source-summary failed with ${response.status}`);
  }
  return response.json() as Promise<DraftSourceSummaryPayload>;
}

export async function runWorkbenchAction(action: WorkbenchActionKey): Promise<WorkbenchActionPayload> {
  const response = await fetch(`/api/actions/${action}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`/api/actions/${action} failed with ${response.status}`);
  }
  return response.json() as Promise<WorkbenchActionPayload>;
}
