# Comparison Workflow

Use this workflow before deciding that a graph layer is worth keeping.

## Goal

Compare direct canonical lookup against graph-style neighborhood expansion for the same explicitly chosen seed entity.

## Recommended Steps

1. Validate the ontology core.
2. Export the graph projection.
3. If you need help locating a seed, run discovery mode:
   - `python scripts/compare_graph_modes.py --repo-root <path> --find "<partial text>"`
4. Run comparison mode with an explicit seed:
   - `python scripts/compare_graph_modes.py --repo-root <path> --entity-id <entity-id>`
   - or `python scripts/compare_graph_modes.py --repo-root <path> --entity-label "<Exact Label>"`
5. Check whether graph mode reveals materially useful extra context.
6. Only then decide whether Ladybug is justified.

## What To Look For

- extra reachable entities that matter
- clearer provenance chains
- easier path explanation
- useful multi-hop context that direct lookup missed

## What Not To Overclaim

- more nodes does not mean better answers
- denser graphs do not prove higher quality
- graph traversal does not replace claim review
- discovery mode does not count as exact seed selection

## Good Seeds

- exact entity id such as `svc.api`
- exact entity label such as `Public API Service`
- exact central concept labels in educational material
- exact focal company or metric identifiers in finance notes

## Decision Rule

Keep the graph layer only if the extra context is meaningfully helpful for:

- explanation
- exploration
- graph-assisted context assembly

If the result is only cosmetic, stay with the core workflow.
