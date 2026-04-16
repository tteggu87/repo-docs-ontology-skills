# DocTology

Portable knowledge/ontology skill pack plus a runnable local reference runtime.

This repository now has two intentional layers:

1. `.agent/skills/`
   - reusable skill modules
   - portable templates, references, eval fixtures, and helper scripts
2. root runtime/reference files
   - a small runnable LLM Wiki / workbench reference surface
   - useful when you want to test the public-facing flow directly instead of only browsing skill docs

So this repo is not just a pure skill dump anymore, and it is also not a checked-in personal vault.
It is best understood as:

`portable skill pack + runnable local reference repo`

## Layout

```text
DocTology/
├── .agent/
│   └── skills/
│       ├── repo-docs-intelligence-bootstrap/
│       ├── lightweight-ontology-core/
│       ├── lg-ontology/
│       ├── llm-wiki-bootstrap/
│       ├── llm-wiki-ontology-ingest/
│       └── ontology-pipeline-operator/
├── apps/
│   └── workbench/
├── scripts/
├── templates/
├── intelligence/
├── wikiconfig.json
├── wikiconfig.example.json
├── run-workbench.command
└── run_windows_workbench.bat
```

## What belongs here

### A. Portable skill-pack content

These belong under `.agent/skills/`:
- skill instructions
- reusable scripts bundled with a skill
- references
- eval fixtures
- templates owned by a specific skill

### B. Runnable reference-runtime content

These belong at repo root because they are part of the current public runnable reference:
- `apps/workbench/`
- `scripts/`
- `templates/`
- `intelligence/`
- `wikiconfig.json`
- `wikiconfig.example.json`
- launcher files such as `run-workbench.command` and `run_windows_workbench.bat`

Why they stay:
- `apps/workbench/` needs `scripts/workbench_api.py`
- `scripts/llm_wiki.py` uses `templates/source_page_template.md`
- `scripts/incremental_ingest.py` reads `intelligence/manifests/source_families.yaml`
- `scripts/workbench/repository.py` reads `wikiconfig.json`
- launcher files depend on the root runtime layout

## What still does NOT belong here

These are still project-local or generated outputs and should not be committed as part of this public repo baseline:
- personal `raw/`
- personal `wiki/`
- personal `warehouse/`
- vector stores
- local caches and scratch artifacts
- personal Obsidian vault contents

## Quick intent guide

- If you want reusable capability only: start in `.agent/skills/`
- If you want to run the local public reference flow: use the root runtime files

## Included skill families

- `repo-docs-intelligence-bootstrap`
  - structure an existing repo or PRD and establish current truth
- `lightweight-ontology-core`
  - extract canonical ontology truth from documents and notes
- `lg-ontology`
  - add graph projection and graph-style inspection on top of canonical JSONL truth
- `llm-wiki-bootstrap`
  - scaffold a new Obsidian-first LLM Wiki workspace
- `llm-wiki-ontology-ingest`
  - ingest sources into an existing ontology-backed LLM Wiki
- `ontology-pipeline-operator`
  - operate and refresh an existing ontology/wiki pipeline

## 한국어

### 이 레포를 한 문장으로 말하면

DocTology는
`재사용 가능한 skill pack`과
`직접 실행해볼 수 있는 로컬 reference runtime`을
같이 담는 공개 레포입니다.

### 왜 이렇게 두 층으로 두는가

이번 정리 기준은 다음입니다.

- `.agent/skills/` 아래에는 portable skill을 둔다
- 하지만 `apps/workbench`, `scripts`, `templates`, `intelligence`, `wikiconfig.json`, 실행 배치/커맨드 파일은 실제 runnable reference를 위해 루트에 둔다

즉:
- 이 레포는 순수 skill dump만은 아니다
- 그렇다고 개인용 `raw/wiki/warehouse`가 들어가는 실제 vault repo도 아니다
- 공개용으로 실행 가능한 기준 surface와 reusable skill을 함께 둔 하이브리드 레포다

### 무엇이 왜 필요한가

- `apps/workbench/`
  - 실제 public-facing reference UI
- `scripts/`
  - workbench backend와 local CLI
- `templates/`
  - `scripts/llm_wiki.py`가 직접 사용
- `intelligence/`
  - incremental ingest와 workbench contract가 직접 사용
- `wikiconfig.json`
  - helper-model 경로가 실제로 읽음
- `run-workbench.command`, `run_windows_workbench.bat`
  - 실행 진입점

### 무엇은 여전히 넣지 않는가

- 실제 개인 `raw/`, `wiki/`, `warehouse/`
- vector store
- 캐시/스크래치 산출물
- 개인용 vault 실데이터

## Notes

- `.agent` is the canonical portable folder name for skill-pack content in this repo.
- Root runtime files exist because this repo is also a runnable public reference.
- If a future fully separated demo/runtime repo is created, the root runtime layer can later be split out cleanly.