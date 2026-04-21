# Red team / Blue team review — graph answer value in current DocTology

_Date: 2026-04-21_

## Review question

질문:

> 현재 그래프가 위키/온톨로지 답변에 실제로 도움을 주는가?
> 그렇다면 지금 개선 우선순위를 높여야 하는가?

판정 기준:
1. 현재 repo 계약 정합성 (`AGENTS.md`, `docs/LAYERS.md`, `docs/CURRENT_STATE.md`)
2. 기존 graph 검증 기록
3. 현재 growth-wiki P0 현실

## Ground truth used

### Repo contract
- `AGENTS.md`: `wiki/`를 durable context surface로 둔다.
- `docs/LAYERS.md`: truth order는 `raw -> warehouse/jsonl -> wiki -> derived`.
- 같은 문서에서 graph projection은
  - `bounded graph inspect`
  - `graph hints and neighborhood/path support`
  - `derived read-only sidecar`
  로 정의되고, truth owner가 되면 안 된다고 적혀 있다.

### Current branch reality
- 현재 growth-wiki P0는
  - ingest / doctor / status / canonical jsonl / graph projection은 있음
  - 하지만 ask runtime은 없음
    - `scripts/llm_wiki.py`에 `ask` 없음
    - `scripts/doctology.py` 없음
    - `scripts/workbench/repository.py` 없음
- 현재 warehouse count:
  - `graph_nodes`: 8838
  - `graph_edges`: 19852
  - `derived_edges`: 19852
  - `claims/messages/segments`: 각 8467
  - `entities`: 965

### Historical graph evidence already recorded
`wiki/_meta/log.md` 기준:
- 2026-04-20 graph meaningful-answer validation:
  - raw answer changed `5/5`
  - core answer changed `0/5`
  - 결론: graph는 support context는 늘렸지만 main answer body는 못 바꿈
- minimal graph-backed context line patch 후:
  - core answer changed `5/5`
  - 하지만 이는 graph line을 본문에 주입한 결과
- blind Kakao graph validation:
  - required answer phrase recovered `0/3` with graph
  - required answer phrase recovered `0/3` without graph
- 이후 방향 정리:
  - graph는 bounded sidecar로 두고
  - terminal ask는 wiki-first로 가야 한다고 정리됨

## Red team view

### 주장
**현재 graph는 답변 품질의 핵심 병목이 아니며, 지금 더 prominence를 줄 이유가 없다.**

### 이유
1. 현재 계약 자체가 graph를 sidecar로 둔다.
2. 기존 실험에서 graph는 주로 sidecar context만 바꿨고, blind answer recovery는 개선하지 못했다.
3. 지금 브랜치에는 ask runtime이 없어서 graph가 실제 answer path를 개선할 자리도 없다.
4. `graph_edges`와 `derived_edges` 개수가 동일한 것은, 현재 graph가 상당 부분 기존 derived edge를 재포장한 층이라는 뜻이다.
5. 현재 더 큰 문제는 graph 부족보다
   - ask runtime 부재
   - source/wiki synthesis 부족
   - evidence selection / multi-line synthesis 약함
   쪽이다.

### Red team verdict
- **그래프를 지금 더 키우거나 주연으로 승격하는 것은 반대**

## Blue team view

### 주장
**graph는 지금도 일정한 가치가 있으므로 없애거나 무시할 층은 아니다. 다만 assist-only로만 다뤄야 한다.**

### 인정할 수 있는 현재 가치
1. graph projection이 실제로 populated 되어 있어 inspect/hint 용도로는 빈 껍데기가 아니다.
2. repo 문서도 graph inspect와 graph hints를 강한 surface로 인정한다.
3. graph-backed context line 같은 좁은 방식으로는 answer body에 영향을 줄 수 있었다.
4. neighborhood/path support는 review/operator drilldown에는 유효할 수 있다.

### 단, 지켜야 할 경계
- truth order는 절대 바꾸지 않기
- graph를 truth owner로 승격하지 않기
- graph를 main answer engine으로 오해하지 않기
- wiki-first / canonical-backed answer path를 유지하기

### Blue team verdict
- **graph는 유지하되 bounded sidecar로만 선택적 개선 가능**

## Neutral judgment

## 최종 판정
**현재 그래프는 “조금은 도움되지만, 답변 품질을 결정적으로 바꾸는 층은 아니다.”**

더 직접적으로 말하면:
- **도움은 된다** → yes, but limited
- **지금 개선 1순위여야 한다** → no

## Why
1. 현재 empirical evidence상 graph는 answer recovery의 핵심 개선 요인이 아니었다.
2. 현재 branch에서는 ask runtime 자체가 비어 있어 graph가 answer quality를 끌어올릴 주 경로가 없다.
3. 현재 더 높은 레버리지는 graph보다
   - wiki-first ask/runtime 복구
   - source/wiki synthesis 강화
   - canonical evidence selection 개선
   에 있다.
4. graph는 현 상태로도 계약상 역할(derived inspect/hints sidecar)은 수행 중이다.

## Practical decision

### 지금 해야 할 것
1. `wiki-first ask/runtime` 최소 복구
2. `TBD` source/wiki synthesis 강화
3. canonical evidence 기반 answer composition 강화

### 지금 미루는 것이 맞는 것
- graph를 main answer path로 승격
- graph ranking/synthesis에 큰 투자
- graph 중심 answer architecture 실험

### 나중에 해도 되는 bounded graph work
- review/inspect surface에서 path/neighborhood hint 개선
- graph-backed context line을 더 provenance-friendly 하게 다듬기
- graph가 evidence recall candidate를 정말 늘리는지 별도 측정

## One-line conclusion

> **현재 graph는 위키/온톨로지 답변의 “보조 컨텍스트 층”으로는 유효하지만, 지금 DocTology에서 가장 먼저 개선해야 할 핵심 answer layer는 아니다.**
