# Red team / Blue team review — Karpathy & rohit alignment

_Date: 2026-04-21_

## Review question

질문:

> DocTology가 Hermes의 raw 독해 강점을 더 가져가야 하는가?
> 그걸 지금 AGENTS/wiki/runtime에 심어야 하는가, 아니면 안 해도 되는가?

판정 기준:
1. Karpathy `LLM Wiki` gist 정합성
2. rohitg00 `LLM Wiki v2` gist 정합성
3. 현재 DocTology growth-wiki P0 상태 적합성

## Ground truth used

### Karpathy gist 핵심
- 3층 구조: `raw sources -> wiki -> schema`
- 핵심 철학: `stop re-deriving, start compiling`
- query는 **wiki against**
- 좋은 답은 다시 wiki에 저장 가능

### rohitg00 v2 gist 핵심
- Karpathy 기본 방향은 유지
- 추가되는 것은 lifecycle / confidence / supersession / graph / automation
- 하지만 query 기본 대상을 raw-first로 바꾸지는 않음

### 현재 DocTology 상태
- `AGENTS.md`는 wiki를 durable context surface로 둠
- `docs/LAYERS.md`는 `raw -> canonical jsonl -> wiki -> derived` 순서를 명시함
- `scripts/llm_wiki.py`는 `ingest`가 source registration only라고 밝힘
- `templates/source_page_template.md`는 여전히 `TBD` 중심이라 synthesis가 약함
- growth-wiki P0에는 아직 ask runtime이 없음 (`scripts/doctology.py`, `repository.py`, ask subcommand 부재)

## Red team view

### 주장
**지금 Hermes raw-first 성향을 DocTology 기본 아키텍처로 심으면 안 된다.**

### 이유
1. Karpathy는 분명히 `query the wiki`라고 말한다.
2. raw-first를 기본값으로 두면 wiki가 컴파일된 지식층이 아니라 장식품이 된다.
3. 지금 source page가 약한 것은 wiki를 더 잘 만들 문제이지, wiki를 우회할 이유가 아니다.
4. DocTology 현재 상태는 ask runtime 복구도 안 된 P0라서, 이 타이밍에 철학까지 바꾸면 과도한 drift가 생긴다.

### Red team verdict
- **Full adoption: reject**
- `raw-first ask`를 아키텍처 중심으로 심는 것은 반대

## Blue team view

### 주장
**제한적으로는 가져올 가치가 있다.**

### 가져올 수 있는 것
- 질문 surface 보존
- 짧은 evidence window 회수
- multi-line synthesis
- pass/partial/fail human-grade 판정
- contradiction / confidence / supersession 보강

### 단, 반드시 지켜야 할 경계
1. 기본 질의 경로는 여전히 `wiki-first`
2. raw는 fallback / repair / verification 용도
3. raw에서 얻은 좋은 답은 다시 wiki에 저장/승격되어야 함
4. graph는 assist-only

### Blue team verdict
- **Bounded adoption: yes**
- 단, `wiki-first + raw-backed repair`까지만 허용

## Neutral judgment

### 최종 판정
**지금 당장 “그렇게 해야 하는가?”에 대한 답은 `아니오`다.**

정확히는:
- **안 해도 되는 것**: `Hermes raw-first ask`를 DocTology 기본 구조로 심는 것
- **나중에 좁게 해도 되는 것**: `wiki-first`를 유지한 채 raw fallback / repair / verification 능력을 넣는 것

## Final decision

### Do not do now
- AGENTS에 `raw-first ask` 철학을 넣는 것
- runtime을 raw 재독해 중심으로 설계하는 것
- source/wiki보다 raw를 더 우선하는 query contract로 바꾸는 것

### Safe narrow move later
- AGENTS에 `wiki-first, raw-backed repair` 정도만 명시
- source template에 evidence / confidence / contradictions 보강
- ask runtime은 `wiki-first`, raw는 low-confidence / thin coverage일 때만 fallback

## One-line conclusion

> **Karpathy/rohit 기준으로 보면 DocTology는 Hermes처럼 raw-first가 되어야 하는 것이 아니라, wiki-first를 유지하면서 Hermes의 evidence handling을 보조 능력으로 흡수하면 된다.**

## Practical recommendation

현재 우선순위는 다음이 더 맞다.
1. ask runtime 최소 복구
2. source/wiki synthesis를 `TBD`에서 벗어나게 강화
3. 그 다음에 raw fallback을 제한적으로 추가

즉 순서는:

`raw-first 전환`이 아니라

`wiki-first 복구 -> synthesis 강화 -> bounded raw fallback`

이다.
