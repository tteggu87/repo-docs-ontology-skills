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

If `wikiconfig.json` is not configured, the command returns the full LLM prompt/evidence bundle instead of making a heuristic answer.

## Query workflow

Entrypoint:

```bash
python3 scripts/llm_query.py "question"
```

The workflow is intentionally two-stage:

1. LLM chooses which wiki pages to read from the page inventory.
2. The system expands the wikilink neighborhood and asks the LLM to answer from the selected wiki/ontology/source evidence.

The mechanical index only helps navigation. It is not the semantic judge.

## Heuristic boundary

Heuristic analyzers are optional low-trust drafts only:

```bash
python3 scripts/pipeline_refresh.py --source ... --heuristic-draft
```

They must be marked:

```yaml
analysis_method: heuristic_draft
trust_level: low
```

Use `--write-analysis` for the LLM-first compile path.
