export type StatusTone = 'fresh' | 'healthy' | 'warning' | 'danger' | 'derived';

export type Kpi = {
  label: string;
  value: string;
  hint: string;
  tone?: StatusTone;
};

export type ActivityItem = {
  title: string;
  meta: string;
  detail: string;
};

export type PageSummary = {
  id: string;
  title: string;
  type: 'analysis' | 'concept' | 'entity' | 'project' | 'source';
  summary: string;
  updatedAt: string;
  related: string[];
};

export type PageDetail = {
  id: string;
  title: string;
  kicker: string;
  summary: string;
  sections: { heading: string; body: string[] }[];
  provenance: string[];
  relatedPages: string[];
  graphSeed: string;
};

export type GraphNode = {
  id: string;
  label: string;
  family: 'Entity' | 'Claim' | 'Segment' | 'Document' | 'Evidence';
  emphasis?: boolean;
};

export type GraphEdge = {
  source: string;
  target: string;
  family: 'accepted' | 'derived' | 'evidence' | 'mentions';
};
