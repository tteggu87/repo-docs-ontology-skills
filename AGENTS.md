# AGENTS.md

This repository uses the project-local wiki under `wiki/` as a durable context surface.

## Startup Rule

Before making meaningful code, architecture, or product-direction changes:

1. read this root `AGENTS.md`
2. read `docs/CURRENT_STATE.md` and `docs/LAYERS.md`
3. if the task targets the current DocTology runtime/wiki surface, read:
   - `wiki/_meta/index.md`
   - recent relevant entries in `wiki/_meta/log.md`
4. read `wiki/AGENTS.md` and the deeper `wiki/wiki/*` tree only when the task explicitly targets the checked-in bootstrap/sample workspace or historical internal analyses stored there

Do not treat the chat transcript alone as the full source of working context when the repository already contains durable product/runtime context.

## Scope Guidance

- `wiki/` is the project-local knowledge workspace used by the current DocTology runtime
- root-level `wiki/_meta/`, `wiki/sources/`, and sibling directories are the primary runtime-facing surfaces
- the deeper `wiki/wiki/` subtree is retained as checked-in bootstrap/sample or historical analysis content and should be consulted only when a task explicitly targets it
- code, docs, and product decisions should prefer the latest durable runtime context when relevant
- if there is a conflict between this file and a deeper `AGENTS.md`, the deeper file wins for files in its scope

## Coding Workflow

When implementing code changes:

1. recover context from the wiki first
2. make the code change
3. if the change creates durable product, architecture, or contract knowledge, update the wiki

## Wiki Relationship

Use the wiki for:

- product direction notes
- architecture decisions
- contract clarifications
- implementation progress
- unresolved design questions

Keep the wiki readable for future agents so they can recover context without re-deriving everything from scratch.
