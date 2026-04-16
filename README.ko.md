# DocTology

[English](README.md) | [한국어](README.ko.md)

DocTology는 단순 LLM Wiki가 아니라, Obsidian-first 위키 위에 canonical ontology layer와 repo-intelligence contract를 결합한 개인 지식관리 starter kit입니다.

핵심 방향은 다음 네 가지입니다.

- 노트가 늘어나도 위키만 직접 훑는 대신 ontology layer를 함께 두어 에이전트의 읽기 범위와 토큰 팽창을 더 잘 제어
- 필요할 때는 ontology graph / neighborhood 확장까지 이어갈 수 있는 구조
- 에이전트가 읽을 프로젝트 메모리를 wiki page, JSONL ontology registry, intelligence contract로 함께 제공
- 재사용 가능한 skill pack + 로컬 reference runtime + private workspace bootstrap baseline을 한 레포에 제공

이 레포 하나로 DocTology는 다음을 같이 제공합니다.

- bootstrap, ontology, operator 워크플로를 담은 portable `.agent/skills/` 팩
- LLM Wiki CLI와 선택형 workbench UI가 포함된 로컬 reference runtime
- 개인 코퍼스를 공개 레포에 넣지 않고도 private workspace를 시작할 수 있는 깔끔한 baseline

![DocTology 워크벤치 질문 작업공간](assets/readme/doctology-workbench-question-workspace.jpg)

_DocTology 워크벤치 질문 작업공간 — 현재 위키를 확인하고, repo-local 질문 미리보기를 검토하며, bounded analysis page만 저장합니다._

현재 workbench의 실제 성격은 자유 대화형 LLM 작업공간이라기보다, 생성된 위키와 관련 preview를 읽고 검토하는 화면에 가깝습니다. 즉, 아직 능동적인 conversational chat 면은 아닙니다.

![참고 예시: 지식이 위키로 자라나는 모습](assets/readme/doctology-reference-obsidian-notes-forming-a-wiki.jpg)

_참고 예시 — 서로 거의 연결되지 않았던 Obsidian 노트들이 점차 구조와 neighborhood를 형성하며 위키처럼 자라나는 모습을 보여줍니다._

## 어디서 시작할지 먼저 고르세요

### 1) LLM Wiki를 먼저 쓰고 싶나요?
그렇다면 `llm-wiki-bootstrap`으로 시작하면 됩니다.

흐름은 단순합니다.

- 위키 부트스트랩 실행
- 생성된 `raw/inbox/` 폴더에 문서를 넣기
- `llm-wiki-ontology-ingest`로 ingest 진행
- 이후 질문·분석 워크플로로 위키를 계속 키우기

즉, 시작점은 항상 **wiki-first** 입니다.

### 2) 생성된 위키에서 ontology 관계를 더 다듬고 싶나요?
그렇다면 `lightweight-ontology-core`를 사용하세요.

이 단계에서는:

- 엔티티 / claim / evidence / relation 같은 canonical ontology layer를 정리하고
- 위키 아래의 JSONL truth를 더 정교하게 만들며
- 필요하면 이후 `lg-ontology`로 graph / neighborhood 확장까지 이어갈 수 있습니다.

즉, 위키를 만든 뒤 관계를 재정의하고 구조를 더 강하게 만들고 싶을 때 들어가는 단계입니다.

### 3) 프로젝트 전용 기억창고를 만들고 싶나요?
그렇다면 `repo-docs-intelligence-bootstrap`을 사용하세요.

이 경로는 개인 위키를 키우는 쪽보다:

- 특정 코드베이스나 프로젝트의 현재 상태를 기억시키고
- 에이전트가 읽을 project memory를 만들고
- repo-docs intelligence 스타일의 AGENTS / intelligence contract를 세우는 데 더 맞습니다.

즉, 이것은 **위키 부트스트랩의 대체 선택지**이지, 그 위에 겹쳐서 또 실행하는 단계가 아닙니다.

## 주의

**부트스트랩은 하나만 사용하세요.**

여러 부트스트랩을 연속으로 실행하면 `AGENTS.md`가 덮어쓰기되어 이전 설정과 운영 규칙이 무효가 될 수 있습니다.

처음에 먼저 선택해야 합니다.

- LLM Wiki를 키우고 싶은가?
- 아니면 repo용 intelligence / project memory를 만들고 싶은가?

둘 다 중요하지만, 시작 부트스트랩은 하나만 고르는 것이 맞습니다.

## 핵심 skill 경로

- `llm-wiki-bootstrap`
  - Obsidian-first LLM Wiki 시작
- `llm-wiki-ontology-ingest`
  - inbox 문서를 ontology-backed wiki로 ingest
- `lightweight-ontology-core`
  - 위키 아래의 canonical ontology truth 정리
- `lg-ontology`
  - ontology graph / neighborhood 확장
- `repo-docs-intelligence-bootstrap`
  - 프로젝트 전용 기억창고 / repo intelligence bootstrap

## 지금 체크인된 reference runtime에 대해

이 저장소에 포함된 workbench는 현재 자유 대화형 LLM 앱이라기보다:

- 생성된 위키를 확인하고
- repo-local preview를 검토하고
- bounded analysis page를 저장하는

읽기·검토용 reference surface에 가깝습니다.

즉, README의 핵심은 런타임 사용법보다 **어떤 부트스트랩을 고르고 어떤 기억 계층을 만들지**를 이해하는 데 있습니다.
