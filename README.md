# DocTology

Public home for a reusable local-first knowledge/ontology skill pack.

This repository is intentionally organized as a portable agent skill bundle under `.agent/skills/`.
It is not meant to be a checked-in example of a generated LLM Wiki workspace.
In other words:

- this repo stores reusable skills
- target projects generate their own `raw/`, `wiki/`, `warehouse/`, `docs/`, and `intelligence/`
- those generated workspace artifacts should normally live in the target repo, not here

Current skill bundle layout:

```text
.agent/
└── skills/
    ├── repo-docs-intelligence-bootstrap/
    ├── lightweight-ontology-core/
    ├── lg-ontology/
    ├── llm-wiki-bootstrap/
    ├── llm-wiki-ontology-ingest/
    └── ontology-pipeline-operator/
```

## What this repo is for

DocTology is for people who want to build knowledge systems in stages instead of jumping straight into a heavy graph platform.
The intended progression is:

`repo/bootstrap discipline -> canonical ontology -> optional graph projection -> optional LLM Wiki ingest/operator loop`

The main roles of the included skills are:

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

## What is intentionally not stored at the repo root

The following are considered generated or project-local outputs and are not the point of this repository:

- generated `docs/` from a specific target workspace
- generated `intelligence/` contracts from a specific target workspace
- generated `raw/`, `wiki/`, `warehouse/`, or `vector/` data
- local helper configs and operator scratch state
- a personal Obsidian vault's live contents

Those should be created inside the target project that uses these skills.

## 한국어

### 이 레포를 한 문장으로 말하면

DocTology는 `문서/노트/회의록/PRD/리서치 메모`를
단순한 파일 모음이 아니라,
`사람은 wiki로 읽고 에이전트는 ontology로 추적할 수 있는 지식 시스템`으로 바꾸기 위한 스킬 묶음입니다.

### 왜 이렇게 정리했는가

이 레포는 이제 특정 LLM Wiki workspace의 결과물을 직접 담는 저장소가 아니라,
그런 workspace를 만들고 운영할 때 재사용할 수 있는 skill pack을 담는 저장소로 정리되어 있습니다.

즉:
- 이 레포 안에는 `.agent/skills/` 밑의 reusable skill만 둡니다
- 실제 `raw/`, `wiki/`, `warehouse/`, `docs/`, `intelligence/`는 대상 프로젝트에서 생성합니다
- 그래서 이 레포는 productized skill bundle이고, 각 실제 지식 저장소는 이 레포를 사용해 따로 만들어집니다

### 빠른 선택

- 기존 프로젝트/PRD를 먼저 구조화: `repo-docs-intelligence-bootstrap`
- canonical ontology만 만들기: `lightweight-ontology-core`
- graph projection까지 보기: `lg-ontology`
- 새 LLM Wiki workspace 시작: `llm-wiki-bootstrap`
- 기존 LLM Wiki에 반복 ingest: `llm-wiki-ontology-ingest`
- 기존 ontology/wiki 파이프라인 운영: `ontology-pipeline-operator`

### 추천 기본 순서

- 프로젝트 구조와 current truth 정리: `repo-docs`
- 그다음 canonical ontology: `lightweight-ontology-core`
- 필요할 때만 graph projection: `lg-ontology`
- LLM Wiki가 목표라면 별도 대상 repo에서 `llm-wiki-bootstrap`과 `llm-wiki-ontology-ingest` 사용

## Notes

- `.agent` is the canonical portable folder name in this repo.
- Skill docs should prefer neutral skill names or `.agent`-style paths over old `.codex`-specific paths.
- If a future public demo repo is needed, build that as a separate generated example repo instead of polluting this skill-pack repository.
