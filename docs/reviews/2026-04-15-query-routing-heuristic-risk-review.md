# Query routing heuristic risk review

## Question
The user is specifically worried about heuristic logic entering query-time runtime behavior in an LLM Wiki / ontology system.
The key question is not whether the new route-receipt patch is useful in general, but whether the current heuristic router is actually better than simply letting the LLM choose the route.

## Short verdict
In its current form, the heuristic inside `scripts/query_route.py` is not strong enough to justify being treated as a primary query-time decision-maker.

It is acceptable only as:
- a lightweight receipt helper
- an optional preflight hint
- a deterministic blocker for impossible routes

It is not yet clearly better than letting the LLM decide the route.
If treated as authoritative routing, it can create new downsides.

## Grounding from current implementation
Current helper logic in `llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py` generates a `query_route.py` script that:
- loads `routes.yaml`
- loads `query-routing.yaml`
- but uses hardcoded keyword buckets in `detect_route(...)`
- applies only a narrow policy gate in `apply_policy(...)`
- writes a durable receipt row to `warehouse/jsonl/query_receipts.jsonl`

Important current facts:
- repo-local `typical_signals` in YAML do not drive routing
- most policy text is not executed, only partially consulted
- the helper does not inspect wiki/index/log/canonical density before choosing most routes
- the helper writes a confident-looking receipt even though the actual semantic decision is shallow

## Why the user’s concern is valid
The user’s anti-heuristic concern is especially valid in this repo family because:
- the whole point of LLM Wiki is to let the model read, synthesize, and reason over durable artifacts
- premature hard routing can narrow that reasoning before the model has actually read enough context
- brittle keyword rules are exactly the kind of hand-built shortcut that often ages badly and silently misroutes

So yes: if the current helper were turned into the main routing brain, that would be a design regression relative to the intended LLM Wiki philosophy.

## Is it better than letting the LLM decide?

### As a primary router
No, not currently.

Reasons:
1. The LLM can use richer semantics than the hardcoded keyword list.
   - It can understand indirect phrasing, mixed intent, Korean nuance, and repo-local context.
   - The helper currently cannot.

2. The heuristic router is mostly lexical, not contextual.
   - It does not read `wiki/_meta/index.md`
   - it does not inspect actual page coverage
   - it does not inspect whether the wiki already answers the question well
   - it does not weigh ambiguity across layers

3. The current YAML contract is only partially real.
   - The docs make it look like `routes.yaml` and `query-routing.yaml` are active routing contracts
   - but runtime behavior is still mostly inside `detect_route(...)`
   - so the system can look more principled than it actually is

4. It can create false confidence.
   - A receipt row with `route_key`, `confidence`, and `fallback_reason` looks authoritative
   - but the underlying decision is still a simple keyword match

### As a receipt writer / audit helper
Yes, conditionally.

It is useful if interpreted as:
- “record what route we think we are taking”
- “leave a reproducible trace”
- “enforce simple impossible-route guards”

That is meaningfully helpful.
But that value comes from the receipt and guardrail function, not from the heuristic classifier itself being especially intelligent.

## What new downsides can appear if kept as-is

### 1. Semantic misrouting
Queries with mixed or indirect intent can be routed too early by keywords.
Examples:
- a question that mentions `claim` but really needs a wiki synthesis first
- a question that mentions `path` metaphorically, not graph-wise
- a Korean query whose meaning is clear to an LLM but not to the bucket list

### 2. Drift between docs and runtime
Because YAML contract and runtime logic are not actually the same thing yet, future maintainers may update the manifest and assume routing changed when it did not.

### 3. Hidden rigidity
Once a helper exists, people often start depending on it socially.
Even if the docs say “optional”, agents may start treating it as a default pre-step.
That would make a weak heuristic feel like a hard runtime boundary.

### 4. Anti-pattern for LLM Wiki philosophy
Karpathy-style LLM Wiki works best when:
- the model reads durable compiled knowledge
- then decides what else to verify

A lexical pre-router can become an anti-pattern if it decides too much before that reading happens.

## What would make it defensible
The current patch becomes much more defensible if the helper is explicitly repositioned as one of these:

### Option A. Receipt-only recorder
Best option.

Design:
- the LLM/agent chooses the route
- `query_route.py` only records:
  - chosen route
  - rationale
  - fallback if any
  - affected layers
- script validates route keys against manifests and appends receipt

This removes the heuristic from semantic decision-making entirely.

### Option B. Proposal mode + record mode
Second-best option.

Design:
- `query_route.py --propose` may return a weak heuristic suggestion
- `query_route.py --record --route <...>` writes the authoritative receipt
- docs clearly say proposal mode is advisory only

This keeps the helper useful without letting the heuristic pretend to be the runtime brain.

### Option C. Deterministic blocker only
Also good.

Design:
- no heuristic semantic classifier
- only deterministic checks such as:
  - graph route impossible because graph artifacts missing
  - canonical route weak because canonical files missing
- actual semantic route choice stays with the LLM

This is much more consistent with the user’s anti-heuristic stance.

## Best recommendation for this repo
For DocTology specifically, the best design is:

1. Keep route manifests and receipts
2. Remove or demote heuristic route selection
3. Let the LLM choose the route after reading index / local contracts / current repo context
4. Use the script only to:
   - validate route names
   - apply deterministic impossible-route guards
   - persist the receipt

That gives you the benefit of:
- explainability
- auditability
- eval trace
without paying the main cost of brittle heuristic routing.

## Final answer
So to the user’s exact concern:
- yes, your discomfort is justified
- in the current form, the heuristic query router is not clearly better than letting the LLM decide
- if treated as a primary runtime router, it can absolutely introduce new downsides
- the patch is still salvageable and valuable if the heuristic part is downgraded to optional/advisory and the receipt part is kept

## Practical next move
The next patch should probably be:
- change `query_route.py` from “route chooser” to “route receipt recorder + guard validator”
- make the route an explicit input, or at least split propose vs record modes
- update docs so the helper is not socially interpreted as a mandatory semantic router
