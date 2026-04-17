# AGENTS.md

This repository uses the project-local wiki under `wiki/` as a durable context surface.

## Startup Rule

Before making meaningful code, architecture, or product-direction changes:

1. read this root `AGENTS.md`
2. read `wiki/AGENTS.md` if the `wiki/` workspace exists
3. read `wiki/wiki/_meta/index.md`
4. read recent relevant entries in `wiki/wiki/_meta/log.md`

Do not treat the chat transcript alone as the full source of working context when the wiki has already accumulated durable analysis.

## Scope Guidance

- `wiki/` is the project-local knowledge workspace
- code, docs, and product decisions should prefer the latest durable wiki context when relevant
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
