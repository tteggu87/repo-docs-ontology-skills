# compare_graph_modes Non-Heuristic Improvement Plan

> For Hermes: use this plan when improving graph comparison tooling without smuggling lexical heuristics into the main runtime path.

Goal: Make `lg-ontology/scripts/compare_graph_modes.py` less brittle by reducing lexical seed matching and making seed selection more explicit, auditable, and operator-friendly.

Architecture: Keep `compare_graph_modes.py` as an operator/eval tool, not a primary answer runtime. Replace the current free-text substring seed matching with explicit seed inputs plus optional candidate-list mode. The tool should help operators inspect graph value, not pretend to semantically understand arbitrary natural-language questions.

Tech stack: existing JSONL registries, lightweight CLI flags, no new heavy dependencies.

---

## Why this matters
Current behavior:
- `compare_graph_modes.py --query "..."` tries to match free text to entity ids / labels / aliases using substring logic.
- This is acceptable for rough operator experiments, but it is still a lexical heuristic.
- If copied elsewhere, it would conflict with a wiki-first, LLM-led reasoning philosophy.

The right direction is:
- explicit seeds for exact comparison
- optional discovery mode for human/operator assistance
- no pretending that substring matching is semantic understanding

---

## Recommended target shape

### Preferred CLI modes
1. exact seed mode
- `python scripts/compare_graph_modes.py --repo-root <path> --entity-id <id>`

2. explicit label mode
- `python scripts/compare_graph_modes.py --repo-root <path> --entity-label "Exact Label"`

3. candidate discovery mode
- `python scripts/compare_graph_modes.py --repo-root <path> --find "partial text"`
- outputs candidate entity ids / labels / aliases only
- does not run the comparison automatically

4. optional multi-seed mode later
- repeated `--entity-id`
- or `--seed-file`

### Behavioral rule
- only exact seed modes may run baseline-vs-graph comparison
- discovery mode is advisory and separate
- no free-text implicit semantic routing in the comparison command itself

---

## Task 1: Split seed discovery from comparison

Files:
- Modify: `lg-ontology/scripts/compare_graph_modes.py`
- Modify: `lg-ontology/SKILL.md`
- Modify: `lg-ontology/references/comparison-workflow.md`

Steps:
1. add parser args:
   - `--entity-id`
   - `--entity-label`
   - `--find`
2. deprecate or remove `--query` as the main seed input
3. ensure `--find` only prints candidates and exits
4. ensure comparison requires exact seed resolution before execution

---

## Task 2: Tighten exact matching semantics

Files:
- Modify: `lg-ontology/scripts/compare_graph_modes.py`

Steps:
1. exact `entity_id` should match only exact id
2. exact `entity_label` should match normalized full label equality first
3. alias equality may be allowed, but not substring expansion for comparison mode
4. if multiple matches remain, print candidates and exit rather than choosing implicitly

---

## Task 3: Improve operator receipts

Files:
- Modify: `lg-ontology/scripts/compare_graph_modes.py`
- Optional create: `warehouse/jsonl/graph_comparison_receipts.jsonl` in downstream repos, not in the base skill

Steps:
1. emit which seed mode was used
2. emit whether the comparison was exact-id, exact-label, alias, or discovery-only
3. emit candidate ambiguity when relevant
4. keep this as operator/eval trace, not canonical truth

---

## Task 4: Update docs so this remains an operator tool

Files:
- Modify: `lg-ontology/SKILL.md`
- Modify: `lg-ontology/references/comparison-workflow.md`

Doc changes:
- explicitly say this tool is for operator graph evaluation
- explicitly say it should not be used as the primary answer router
- explicitly separate discovery mode from comparison mode

---

## Definition of done
- comparison no longer relies on substring matching to silently choose seeds
- ambiguous seed text produces candidate output instead of automatic comparison
- operator docs describe the tool as eval/inspection only
- no new lexical seed matcher is introduced into the main answer/runtime path

## Nice-to-have later
- allow the LLM to prepare a seed explicitly, then pass that exact entity id into the tool
- add a small `--json` candidate discovery output for workbench integration
- add receipts for graph comparison experiments if the team wants benchmark history
