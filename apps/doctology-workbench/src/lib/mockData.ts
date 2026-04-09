import type { ActivityItem, GraphEdge, GraphNode, Kpi, PageDetail, PageSummary } from './types';

export const dashboardKpis: Kpi[] = [
  { label: 'Corpus freshness', value: '12m ago', hint: 'Last ontology refresh completed', tone: 'fresh' },
  { label: 'Canonical entities', value: '563', hint: 'Stable entities in warehouse/jsonl', tone: 'healthy' },
  { label: 'Accepted claims', value: '42', hint: 'Ready for graph-backed reasoning', tone: 'healthy' },
  { label: 'Graph projection', value: 'Stale', hint: 'Projection lags canonical truth by 1 run', tone: 'warning' },
  { label: 'Pending review', value: '7', hint: 'Candidate facts need operator approval', tone: 'derived' }
];

export const recentActivity: ActivityItem[] = [
  { title: 'Agent Korea ingest', meta: 'source family · 12m ago', detail: 'Canonical outputs refreshed and 3 wiki analyses updated.' },
  { title: 'Mem0 vs lg-ontology review', meta: 'analysis · 39m ago', detail: 'Added comparison memo and updated index/log.' },
  { title: 'Graph regression check', meta: 'operator loop · 1h ago', detail: 'Baseline beat graph on one seed query; projection flagged for review.' }
];

export const suggestedActions: ActivityItem[] = [
  { title: 'Rebuild graph projection', meta: 'high impact', detail: 'Projection is stale against current accepted claims.' },
  { title: 'Review pending claims', meta: 'operator', detail: 'Seven candidate claims are blocking stronger graph evidence.' },
  { title: 'Inspect sparse topic cluster', meta: 'quality', detail: 'One concept group has low evidence density compared with activity.' }
];

export const pages: PageSummary[] = [
  {
    id: 'mem0-fit',
    title: 'Mem0 fit for llm-wiki-obsidian',
    type: 'analysis',
    summary: 'Evaluates Mem0 as a sidecar memory layer versus canonical ontology truth.',
    updatedAt: '2026-04-09',
    related: ['lg-ontology-skill', 'mem0-graph']
  },
  {
    id: 'lg-ontology-skill',
    title: 'lg-ontology Skill',
    type: 'source',
    summary: 'Describes graph projection and graph-style inspection on top of canonical JSONL truth.',
    updatedAt: '2026-04-08',
    related: ['mem0-fit']
  },
  {
    id: 'doctology-ui',
    title: 'DocTology UI and dashboard direction',
    type: 'analysis',
    summary: 'Recommends a workbench-first, wiki-first, graph-sidecar UX strategy.',
    updatedAt: '2026-04-09',
    related: ['mem0-fit', 'lg-ontology-skill']
  }
];

export const pageDetails: Record<string, PageDetail> = {
  'doctology-ui': {
    id: 'doctology-ui',
    title: 'DocTology UI and dashboard direction',
    kicker: 'Analysis · UI Strategy',
    summary: 'The strongest product direction is a calm SaaS workbench where dashboard trust, article reading, and graph drill-down work together.',
    sections: [
      {
        heading: 'Why workbench-first wins',
        body: [
          'Users need to trust freshness, validator health, and provenance before they care about graph spectacle.',
          'The homepage should therefore show pipeline health, suggested actions, and graph value signals instead of a giant graph.'
        ]
      },
      {
        heading: 'Role of graph inspect',
        body: [
          'Graph exploration should stay bounded to seeded neighborhoods and evidence-aware path inspection.',
          'It should feel like a precision instrument, not a homepage toy.'
        ]
      }
    ],
    provenance: ['wiki/analyses/analysis-2026-04-09-doctology-ui-dashboard-direction.md', 'lg-ontology/references/comparison-workflow.md'],
    relatedPages: ['Mem0 fit for llm-wiki-obsidian', 'lg-ontology Skill'],
    graphSeed: 'doctology-ui'
  }
};

export const graphNodes: GraphNode[] = [
  { id: 'doctology-ui', label: 'DocTology UI', family: 'Document', emphasis: true },
  { id: 'workbench', label: 'Workbench-first UX', family: 'Claim' },
  { id: 'wiki-surface', label: 'Wiki reading surface', family: 'Entity' },
  { id: 'graph-sidecar', label: 'Graph inspect sidecar', family: 'Entity' },
  { id: 'provenance', label: 'Provenance bundle', family: 'Evidence' },
  { id: 'seed-neighborhood', label: 'Seeded neighborhood', family: 'Segment' }
];

export const graphEdges: GraphEdge[] = [
  { source: 'doctology-ui', target: 'workbench', family: 'accepted' },
  { source: 'doctology-ui', target: 'wiki-surface', family: 'accepted' },
  { source: 'doctology-ui', target: 'graph-sidecar', family: 'derived' },
  { source: 'workbench', target: 'provenance', family: 'evidence' },
  { source: 'graph-sidecar', target: 'seed-neighborhood', family: 'mentions' }
];
