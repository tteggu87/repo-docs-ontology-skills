# DocTology Project Skills

This directory tracks the project-local DocTology skill surfaces that should be
visible in GitHub:

- `llm-wiki-bootstrap`
- `llm-wiki-ontology-ingest`
- `ontology-pipeline-operator`

These files are the committed project-local DocTology skill package for agents
working from this repository.  The bootstrap skill includes the full scaffold
generator and support files so a clean GitHub clone can create a new
`llm-first-ontology` workspace without relying on `~/.codex/skills`.

Core rules preserved here:

- helper LLMs are optional accelerators, not the default semantic authority
- missing or disabled helper LLMs should emit agent handoff material, not
  heuristic semantic success
- active wiki truth changes remain proposal/review-driven
- durable query answers may be saved under `wiki/analyses/`
- `content_units` remain citation anchors, not RAG chunks
