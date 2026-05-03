# DocTology Project Skills

This directory tracks the project-local DocTology skill surfaces that should be
visible in GitHub:

- `llm-wiki-bootstrap`
- `llm-wiki-ontology-ingest`
- `ontology-pipeline-operator`

These files document the intended LLM-first ontology workflow for agents working
from this repository.  The bootstrap skill keeps a thin local launcher and
delegates the full scaffold generator to the installed Codex skill script to
avoid maintaining two divergent generator implementations.

Core rules preserved here:

- helper LLMs are optional accelerators, not the default semantic authority
- missing or disabled helper LLMs should emit agent handoff material, not
  heuristic semantic success
- active wiki truth changes remain proposal/review-driven
- durable query answers may be saved under `wiki/analyses/`
- `content_units` remain citation anchors, not RAG chunks
