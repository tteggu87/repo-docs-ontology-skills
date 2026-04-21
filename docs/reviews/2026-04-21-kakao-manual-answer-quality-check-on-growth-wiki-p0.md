# Kakao manual answer-quality check on growth-wiki P0

_Date: 2026-04-21_

## Purpose

사용자 의도는 `ask` 자동검증 유무가 아니라, **현재 P0 + 카카오톡 txt ingest 상태에서 사람이 실제로 읽었을 때 답변 품질이 어느 정도인지 확인**하는 것이다.

이번 평가는 다음 원칙으로 진행했다.

1. 현재 브랜치에 실제 ingest된 카카오톡 txt (`raw/processed/2026-04-21-kakao-agent-korea-full-chat-normalized.txt`)를 기준으로 본다.
2. 현재 유지된 wiki/source surface와 raw evidence를 함께 본다.
3. 자동 ask runtime이 없더라도, **현재 레이어만으로 사람이 답을 만들 수 있는지**를 본다.
4. 판정은 `pass / partial / fail`로 한다.

## Important current-state observation

현재 source page `wiki/sources/source-2026-04-21-kakaotalk-agent-korea-full-chat-csv-normalized-to-txt.md`는 아직 다음 상태다.

- Summary: `TBD`
- Key Facts: `TBD`
- Important Claims: `TBD`

즉 **현재 품질은 "wiki가 이미 답을 정리해주는 수준"이 아니라, raw/canonical evidence를 사람이 읽으면 어디까지 답할 수 있나**의 평가다.

## Question set and judgment

### 1) 라텔이 관심있어하는 생물과 그 이유는?

#### Evidence
- `raw/...normalized.txt:2519`
  - `라텔 / 개발: 카피바라 나오면 그때 던질까 생각중입니다`
- `raw/...normalized.txt:2546`
  - `라텔 / 개발: 오픈클로 자체 보다는 이제 가재에 더 관심을`
- `raw/...normalized.txt:2725`
  - `라텔 / 개발: 바닷가재 그 자체`
- `raw/...normalized.txt:3375`
  - `라텔 / 개발: 개미는 사실 분업을 알아서 해서`
- `raw/...normalized.txt:3378`
  - `라텔 / 개발: Task 당 몇마리를 쓸지는 군체가 알아서 정합니다`
- `raw/...normalized.txt:3629`
  - `라텔 / 개발: 유저타입 ant???`
- `raw/...normalized.txt:3636`
  - `라텔 / 개발: 개미 운명인가`
- `raw/...normalized.txt:3642`
  - `라텔 / 개발: Ant-only`

#### Current-level answer
라텔은 한 가지 생물만 말한 것이 아니라, 대화 맥락상 **개미 / 가재(바닷가재) / 카피바라**를 반복적으로 언급한다.

그중 **이유가 비교적 직접적으로 붙는 것은 개미**다. 개미는 `분업을 알아서 하고`, `Task 당 몇 마리를 쓸지는 군체가 알아서 정한다`고 말해서, **멀티 에이전트/군집적 태스크 분배의 비유**로 쓰고 있다.

반면 **가재/바닷가재**는 `오픈클로 자체 보다는 이제 가재에 더 관심`이라고 해서 최근 취향/관심 이동이 드러나지만, 이유 설명은 약하다. **카피바라**는 `나오면 그때 던질까 생각중`이라며 어떤 대상이 나오면 검토하겠다는 맥락이다.

#### Judgment
- **partial**

#### Why
현재 raw만 읽으면 **답은 만들 수 있다**. 하지만
- 질문이 단수형("어떤 생물")인데 evidence는 복수 후보로 흩어져 있고,
- `관심 대상`과 `이유`가 한 줄에 같이 나오지 않으며,
- wiki/source page가 아직 이걸 정리하지 않았다.

즉 **사람이 읽고 합성하면 답이 되지만, 현재 레이어 자체가 이미 깔끔한 답변을 제공하는 수준은 아니다.**

---

### 2) 온톨로지가 뭔지?

#### Evidence
- `raw/...normalized.txt:559`
  - `Comad.J: 이걸 코마드브레인에 온톨로지로 심어두려고 가공 중이에ㅛ`
- `raw/...normalized.txt:814`
  - `Dominic: 개인 온톨로지 구축해주는 서비스`
- `raw/...normalized.txt:1172`
  - `읽기쓰기/반도체연구원: ... 프로젝트 드리프트 막으려고 플젝 온톨로지 문서 만들어 놓았는데요`

#### Current-level answer
이 코퍼스에서의 `온톨로지`는 사전식 정의로 길게 설명되기보다,
**정보를 엔티티와 관계로 구조화해서 어떤 시스템이나 프로젝트에 심는 지식 구조**라는 뜻으로 쓰인다.

구체적으로는:
- `주요 정보들 각각 엔티티로 정의해서 관계성 추출`
- `코마드브레인에 온톨로지로 심는다`
- `개인 온톨로지 구축`
- `프로젝트 드리프트를 막기 위한 플젝 온톨로지 문서`

정도로 나타난다.

#### Judgment
- **partial**

#### Why
현재 코퍼스에는 **온톨로지의 사용 예시와 역할**은 있지만,
`온톨로지가 무엇인가`를 초심자용으로 직접 정의한 문장은 없다.
그래서 현재 수준에서 만들 수 있는 답은 **맥락 기반 설명**이지, **깔끔한 정의형 정답**은 아니다.

---

### 3) 오픈크랩은 어떤 용도로 추천됐나?

#### Evidence
- `raw/...normalized.txt:6745`
  - `알렉스님 그런데 나무온톨로지도 오픈크랩으로 만든건가요? 오픈크랩 사용법을 좀 익히고 싶어서요.`
- `raw/...normalized.txt:6748`
  - `Alexai @alexai_mcp: 오픈크랩으로 했어요`
- `raw/...normalized.txt:6749`
  - `Alexai @alexai_mcp: 플랜트온톨로지도`
- `raw/...normalized.txt:6751`
  - `오픈크랩 클코에 | 플러그인으로 설치`
- `raw/...normalized.txt:6752`
  - `준비된데이터셋 경로 주고`
- `raw/...normalized.txt:6753`
  - `오픈크랩으로 돌려`
- `raw/...normalized.txt:6759`
  - `메타엣지 문법이 오픈크랩에 적용되어있어요`

#### Current-level answer
오픈크랩은 이 대화에서 **온톨로지/지식구조를 실제로 생성·실행하는 도구/워크플로우**로 추천된다.

구체적으로는:
- 나무온톨로지, 플랜트온톨로지 같은 결과물을 만드는 데 사용됐고,
- `클코에 플러그인으로 설치`한 뒤,
- `준비된 데이터셋 경로`를 주고,
- `오픈크랩으로 돌리는` 방식으로 설명된다.

#### Judgment
- **pass**

#### Why
질문이 요구하는 `용도`가 대화 안에서 비교적 직접적으로 드러난다. 설명이 완전한 튜토리얼은 아니어도, **무엇에 쓰는지**는 현재 raw 기준으로 충분히 답할 수 있다.

---

### 4) pm2가 언급된 맥락은 뭐야?

#### Evidence
- `raw/...normalized.txt:3`
  - `... 백그라운드에서도 계속 실행되게 업그레이드 해야겠네요`
- `raw/...normalized.txt:4`
  - `플라잉따릉이: systemd / launchd에 설치해달라고 하세요`
- `raw/...normalized.txt:5`
  - `플라잉따릉이: 아니면 pm2`
- `raw/...normalized.txt:7`
  - `... pm2 는 처음 들어봐여`
- `raw/...normalized.txt:8`
  - `플라잉따릉이: 어 비슷한거에요`

#### Current-level answer
pm2는 **프로그램을 백그라운드에서 계속 실행되게 하는 대안**으로 언급됐다.
즉 `systemd / launchd` 같은 서비스 관리 방식과 비슷한 맥락에서,
"계속 살아있게 돌리는 운영 방법" 쪽 제안이다.

#### Judgment
- **pass**

#### Why
맥락이 아주 짧고 명확하다. 현재 raw만 읽어도 오해 없이 답변 가능하다.

---

### 5) 에이전트코리아 디스코드에는 어떻게 들어오라고 했나?

#### Evidence
- `raw/...normalized.txt:109`
  - `... 에이전트코리아 디스코드에도 | 현 카톡방과 같은 대화명으로 들어오세요 | https://discord.gg/QEjSSkfZ9E |`

같은 문구가 입장 안내 메시지로 반복 등장함.

#### Current-level answer
에이전트코리아 디스코드에는 **현재 카톡방과 같은 대화명으로 들어오라**고 안내한다.
링크도 함께 제공된다: `https://discord.gg/QEjSSkfZ9E`

#### Judgment
- **pass**

#### Why
직접 지시문이 반복되어 있어 회수와 답변이 가장 쉽다.

---

## Overall judgment

현재 P0 + 카카오톡 txt ingest 상태에서의 **사람 기준 답변 품질**은 다음처럼 보는 것이 맞다.

- `pass`: 3개
  - 오픈크랩 용도
  - pm2 맥락
  - 디스코드 입장 방식
- `partial`: 2개
  - 라텔이 관심있어하는 생물과 이유
  - 온톨로지가 뭔지
- `fail`: 0개
  - 이번 5문항에서는 raw evidence를 직접 읽는 방식으로는 실패까지는 아니었다.

## Interpretation

핵심은 이렇다.

1. **현재 raw/canonical ingest 자체는 충분히 살아 있다.**
   - 짧고 직접적인 질문은 이미 답변 품질이 꽤 괜찮다.

2. **하지만 wiki/source synthesis는 아직 비어 있다.**
   - source page가 `TBD` 상태라서,
   - 사람이 raw를 직접 읽어 합성해야 하는 비용이 아직 크다.

3. **특히 추상형 질문은 아직 약하다.**
   - `온톨로지가 뭔지?`
   - `라텔이 관심있어하는 생물과 그 이유는?`
   같은 질문은 evidence가 흩어져 있어서, 현재 수준에서는 자동이든 수동이든 정리 비용이 남아 있다.

## Practical next step implied by this check

다음 ask runtime 분리 품질개선의 초점은 단순 검색보다 다음에 맞다.

1. **multi-line synthesis 강화**
   - target + reason이 여러 줄에 흩어진 질문
2. **source/wiki synthesis surface 강화**
   - `TBD` source page를 evidence-backed summary로 채우기
3. **definition-style answer composition 강화**
   - 예시 나열이 아니라 `무엇인지`를 설명하는 답변 형태

이 체크의 결론은:

> 현재 수준은 `ingest는 됐고, 짧은 질문은 꽤 답할 수 있으며, 추상형 질문은 아직 사람이 합성해줘야 하는 수준`이다.
