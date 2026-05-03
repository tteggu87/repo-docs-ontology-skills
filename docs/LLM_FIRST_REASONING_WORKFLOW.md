# LLM-First Reasoning Workflow

DocTology is not meant to be a simple RAG chunk-stuffing system.

The primary reasoning surface is:

1. Obsidian wiki pages
2. Zettelkasten-style links
3. ontology-like concept/entity/source/analysis structure
4. source-backed content units as citation anchors
5. raw source material as immutable evidence

## Source compile workflow

Entrypoint:

```bash
python3 scripts/llm_compile_source.py --source-page <source-page-stem-or-path>
```

The workflow collects:

- source page
- raw path excerpt
- content units
- wiki index
- linked existing wiki pages

Then it asks an LLM to produce:

- existing pages to update
- new page candidates
- uncertainty and open questions
- citation links
- compile notes

If `wikiconfig.json` is not configured or `llmWiki.enabled=false`, the command emits an agent handoff bundle for the surrounding chat LLM and does not claim semantic success. Use `--emit-bundle` when you explicitly want to inspect the prompt/evidence bundle without invoking a helper model.

## Query workflow

Entrypoint:

```bash
python3 scripts/llm_query.py "question"
```

The workflow is intentionally two-stage:

1. LLM chooses which wiki pages to read from the wiki map, link map, source coverage surface, and page metadata.
2. The system reads selected page bodies, expands the wikilink neighborhood, and asks the LLM to answer from the selected wiki/ontology/source evidence.

The mechanical index only helps navigation. It is not the semantic judge.

## Wiki graph navigation

Entrypoint:

```bash
python3 scripts/wiki_graph_navigation.py --write
```

This produces LLM-readable navigation pages:

- `wiki/_meta/moc.md`
- `wiki/_meta/link-map.md`
- `wiki/_meta/orphan-review.md`
- `wiki/_meta/stale-review.md`
- `wiki/_meta/contradiction-review.md`
- `wiki/_meta/source-coverage.md`

These are structural navigation aids. They should help the LLM choose and inspect pages, but they must not be treated as canonical truth.

## Strict LLM boundary

Semantic compile/query workflows require an LLM but not necessarily a configured helper LLM. When no helper is configured, local scripts emit agent handoff bundles/prompts for the surrounding chat LLM. Deterministic code may read files, compute IDs, calculate line ranges, create citation anchors, refresh indexes, and validate structure; it must not create answer drafts or semantic wiki updates.

```bash
python3 scripts/llm_compile_source.py --source-page <source-page>
python3 scripts/llm_query.py "question"
```

Prompt bundles are emitted only by explicit inspection flags:

```bash
python3 scripts/llm_compile_source.py --source-page <source-page> --emit-bundle
python3 scripts/llm_query.py "question" --emit-selection-prompt
```

LLM compile output is saved as a draft compile proposal for human review. It does not automatically modify active concept/entity/project pages.
