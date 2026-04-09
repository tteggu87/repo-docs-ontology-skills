# DocTology SaaS Dashboard Design Plan

> For Hermes: Use subagent-driven-development skill to implement this plan task-by-task.

Goal: Define a SaaS-grade visual and interaction design system for the DocTology workbench so the eventual product feels trustworthy, premium, and operationally useful rather than experimental or graph-toy-like.

Architecture: Keep the product visually centered on a workbench dashboard with calm enterprise SaaS patterns, a readable wiki/article surface, and a graph sidecar that feels precise and instrument-like. Design the UI system first as reusable tokens, layout rules, and state patterns so frontend implementation can stay consistent as pages are added.

Tech Stack: Tailwind CSS tokens, CSS variables, React component primitives, icon set such as Lucide, chart library for lightweight dashboard charts, WebGL-capable graph renderer behind an adapter, Figma-friendly token naming.

---

## Product design north star

DocTology should feel like:
- a serious knowledge operations product
- a private intelligence workbench
- a wiki you can trust
- a graph you can inspect when needed

DocTology should not feel like:
- a hacker-only dev tool
- a graph demo
- a Notion clone
- a chaotic note app with too many panes and too little hierarchy

Primary emotional target:
- "이건 뭔가 복잡한데도 정돈돼 있고 믿을 수 있다"

Secondary emotional target:
- "그래프도 있긴 한데, 그게 메인이 아니라 진짜 필요한 순간에만 힘을 준다"

---

## Visual direction

## Overall style

Use a modern B2B SaaS control-room style:
- dark-first or dark-optimized
- low-noise surfaces
- disciplined hierarchy
- restrained color accents
- strong spacing rhythm
- table/card/chart readability over spectacle

Blend these references conceptually:
- Linear / Vercel / Ramp / Datadog style calm SaaS density
- Wikipedia-like article clarity for reading pages
- Obsidian-like linked knowledge feel in navigation
- Polaris-like quiet graph instrument feel in graph inspect mode

Do not emulate flashy crypto dashboards or glowing 3D cyberpunk UIs.

---

## Design principles

1. Trust over novelty
- Numbers, freshness, provenance, and state should feel clear before anything feels beautiful.

2. Reading is first-class
- Every design choice must support long-form reading and scanning.

3. Graph is secondary power
- Graph gets a premium drill-down experience, not homepage dominance.

4. Density with breathing room
- The product should support many signals at once, but not feel cramped.

5. One primary action per panel
- Every card or module should have one obvious next action.

6. State is visible
- Fresh, stale, warning, failed, derived, canonical, pending, approved must be instantly legible.

---

## Information hierarchy

## Level 1: Global shell
- app name
- workspace/repo selector if later needed
- global search
- primary nav
- user/settings area

## Level 2: Screen purpose
Each top-level screen should have one sentence of purpose visible near the title.
Examples:
- Dashboard: "Monitor pipeline health, freshness, and graph value."
- Ask: "Ask questions against wiki and canonical truth."
- Pages: "Read and inspect synthesized knowledge pages."
- Graph Inspect: "Explore bounded graph neighborhoods from a seed."
- Doctor: "Diagnose drift, missing outputs, and repair steps."

## Level 3: Section blocks
Each screen should use 3-6 major section blocks max.
Do not create long scrolling patchworks of tiny cards without grouping.

---

## Layout system

## Primary app layout
Desktop-first 3-zone shell:

1. Left sidebar
- compact nav
- section filters
- recent items
- saved views

2. Main content column
- page title
- page actions
- core content surface

3. Right context rail
- provenance
- related items
- status notes
- graph preview
- quick actions

Default proportions:
- left: 240-280px
- center: fluid
- right: 320-380px

On narrower screens:
- collapse right rail into tabbed drawer
- collapse left sidebar to icons + flyout

## Grid rules for dashboard
Use a 12-column desktop grid.
Recommended rhythm:
- top KPI strip: 5 cards across
- main body: 8/4 split or 7/5 split
- lower sections: 6/6 or 4/4/4 depending on content type

Spacing scale:
- outer page padding: 24px desktop
- section gap: 24px
- card padding: 16px or 20px
- compact dense table cells: 10-12px vertical

---

## Color system

## Base palette
- Background 1: deep graphite / blue-black
- Background 2: slightly lighter panel gray
- Border: soft slate border with low contrast
- Text primary: near-white, slightly softened
- Text secondary: muted slate
- Accent primary: cool blue or indigo
- Accent secondary: teal or emerald for success states

## Semantic colors
Canonical vs derived needs explicit distinction:
- Canonical: blue family
- Derived: violet or cyan family
- Warning: amber
- Error: red
- Success / fresh / approved: emerald
- Pending / review-needed: yellow-amber
- Informational graph hint: purple-cyan mix

## Hard rule
Never rely on color alone.
Pair every state with:
- badge text
- icon
- label
- tooltip or legend where needed

---

## Typography

Use a sober system font stack.

Type scale:
- App title / page title: 28-32px
- Section title: 18-20px
- Card title: 14-16px semi-bold
- KPI number: 24-32px
- Body: 14-15px
- Dense table/meta text: 12-13px

Reading surfaces:
- line length capped around 70-85 characters for article content
- generous line-height in page reader
- tighter line-height in cards/tables

---

## Core component system

## Shell components
- `AppShell`
- `Sidebar`
- `TopNav`
- `ContextRail`
- `CommandSearch`

## Data display
- `StatCard`
- `TrendCard`
- `StatusBadge`
- `FreshnessBadge`
- `DeltaBadge`
- `MetricStrip`
- `TableCard`
- `TimelineList`
- `WarningPanel`

## Reading components
- `ArticleHeader`
- `ArticleSummary`
- `ArticleSection`
- `ProvenancePanel`
- `EvidenceBundle`
- `RelatedPagesList`
- `EntityChip`

## Graph components
- `GraphPanel`
- `GraphToolbar`
- `GraphLegend`
- `GraphFilters`
- `NodeDetailPanel`
- `GraphStatusBanner`
- `TruncationWarning`

## Feedback and state
- `EmptyState`
- `SkeletonCard`
- `InlineError`
- `SuccessToast`
- `ConfirmDialog`

---

## Screen-by-screen design guidance

## 1. Dashboard

Purpose:
- system overview
- work prioritization
- trust and freshness

Hero strip:
- corpus freshness
- latest ingest status
- graph projection freshness
- validator status
- pending review count

Main sections:
1. Canonical Health
   - documents
   - entities
   - claims
   - evidence
   - segments
   - accepted ratio
   - derived edges

2. Recent Activity
   - updated pages
   - recent analyses
   - source family activity

3. Graph Value
   - latest baseline-vs-graph result
   - top useful seed query
   - graph regressions
   - stale projection alert

4. Suggested Next Actions
   - review pending claims
   - refresh projection
   - inspect sparse topic area
   - sync docs drift

Design notes:
- cards should look like premium operational SaaS cards, not academic widgets
- each section should answer a question quickly
- action buttons should be sparse and specific

## 2. Ask / Explore

Purpose:
- make the system usable every day

Layout:
- top search/query composer
- center answer surface
- right provenance + related page rail

Answer composition blocks:
- concise answer
- route used
- evidence chain
- related pages
- uncertainty / limitation
- graph contribution note if applicable

Design notes:
- answer should read like a human-facing assistant result, not raw system telemetry
- telemetry should exist but be visually secondary

## 3. Page Reader

Purpose:
- private Wikipedia / high-trust reading mode

Layout:
- article title + metadata
- summary block
- sectioned content
- right rail with provenance, related pages, entities, graph seed

Design notes:
- this is where Wikipedia influence should be strongest
- use generous white space in the content column even in dark mode
- ensure links and references feel solid and not overly "app-like"

## 4. Graph Inspect

Purpose:
- bounded graph drill-down

Layout:
- graph center
- top toolbar for hops / filters / search / reset
- right node detail panel
- bottom or side legend

Design notes:
- visually calmer than many graph tools
- use subtle constellation/instrument aesthetics, not cartoon bubbles
- selected node should become an anchor/beacon
- non-selected labels should fade aggressively

## 5. Doctor

Purpose:
- repair, debug, operational trust

Layout:
- health summary strip
- issue groups by severity
- recommended commands
- latest validator outputs
- freshness drift matrix

Design notes:
- should feel like a serious ops screen, not a dump of logs
- make each issue actionable with one next step

---

## Graph interaction rules

1. No graph until a seed exists.
2. Default to 1-hop.
3. 2-hop requires explicit expansion.
4. Hard node cap and edge cap.
5. If cap exceeded, show truncation banner and refinement controls.
6. Offer list/table fallback for oversized result sets.
7. Labels shown only for:
- selected node
- hovered node
- high-priority nodes
- search hit nodes

8. Edge family filtering required.
9. Node family filtering required.
10. Path highlight mode preferred over blanket expansion.

---

## Motion and interaction

Use motion sparingly.

Good motion:
- panel fade/slide
- selected node emphasis
- smooth zoom/pan
- card hover lift
- status transition

Avoid:
- floating animated backgrounds
- noisy pulsing graph nodes everywhere
- heavy parallax
- dashboard-wide animation loops

Animation should communicate state change, not decorate emptiness.

---

## Design tokens to define before UI implementation

Create a token file later in code with:
- background colors
- surface colors
- border colors
- semantic state colors
- spacing scale
- radius scale
- shadow scale
- typography scale
- z-index layers
- graph color map by node and edge family

Recommended naming style:
- `bg.app`
- `bg.panel`
- `text.primary`
- `text.secondary`
- `state.canonical`
- `state.derived`
- `state.warning`
- `graph.node.entity`
- `graph.edge.evidence`

---

## SaaS polish checklist

The product should feel premium when these are true:
- every page has a clear top purpose
- no card feels unlabeled or contextless
- loading states are designed, not accidental
- empty states explain what to do next
- badges are consistent everywhere
- buttons follow one hierarchy system
- filters always show active state clearly
- data density is high but legible
- graph and page views feel like the same product

---

## Anti-patterns to avoid

1. Graph-home anti-pattern
- landing on a huge graph with no seed and no task context

2. Admin-panel clutter
- too many tiny widgets and no narrative hierarchy

3. File-browser leakage
- exposing raw file structure as the main mental model

4. State ambiguity
- users cannot tell canonical vs derived vs pending vs approved

5. UI split-brain
- dashboard feels enterprise, page view feels wiki, graph view feels hackathon toy

6. Renderer lock-in by accident
- graph interaction logic tied too tightly to one visualization library

---

## Phased design rollout

### Phase A: Design foundations
- token system
- layout rules
- component hierarchy
- state language
- graph legend language

### Phase B: High-fidelity dashboard + page designs
- dashboard first
- page reader second
- ask screen third

### Phase C: Graph inspect design
- only after graph role is visually bounded
- define graph toolbar, node detail, truncation states, path mode

### Phase D: Doctor and operational trust surfaces
- issue groups
- repair CTA patterns
- freshness matrices

---

## File plan for design implementation

Create later:
- `apps/doctology-workbench/src/design/tokens.ts`
- `apps/doctology-workbench/src/design/theme.css`
- `apps/doctology-workbench/src/design/graphTheme.ts`
- `apps/doctology-workbench/src/components/...`
- optional `docs/UI_ARCHITECTURE.md`
- optional `docs/UI_COPY_GUIDE.md`

---

## Immediate recommendation

Before coding more screens, do these in order:
1. finalize token vocabulary
2. finalize dashboard information hierarchy
3. finalize page reader layout
4. finalize graph inspect constraints
5. only then implement components

This will keep the product coherent.

---

## Bottom line

DocTology should use a calm SaaS dashboard language, not a flashy graph language. The wow factor should come from clarity, confidence, and depth: a dashboard that proves the system is alive, pages that read like a private Wikipedia, and a graph inspector that feels like a precise instrument instead of a toy.
