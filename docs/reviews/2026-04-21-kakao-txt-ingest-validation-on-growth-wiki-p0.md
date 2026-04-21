# KakaoTalk normalized txt ingest validation on growth-wiki P0

_Date: 2026-04-21_

## Goal

Validate that the restored `growth-wiki-42067a2` branch can:
1. register a KakaoTalk normalized `.txt` source,
2. run production ontology ingest against it,
3. refresh canonical JSONL and graph projection,
4. confirm that `라텔` / `개미` / `가재` / `카피바라` evidence is actually present in canonical outputs.

## Source used

Original validation artifact reused from Playground:
- `/Users/hoyasung007hotmail.com/Documents/Playground/doctology-kakao-full-validation-2026-04-21/normalized_txt/raw/processed/2026-04-21-kakao-agent-korea-full-chat-normalized.txt`

Copied into current repo:
- `raw/processed/2026-04-21-kakao-agent-korea-full-chat-normalized.txt`

Registered source page:
- `wiki/sources/source-2026-04-21-kakaotalk-agent-korea-full-chat-csv-normalized-to-txt.md`

## Commands executed

### 1. Source registration
```bash
python3 scripts/llm_wiki.py ingest raw/processed/2026-04-21-kakao-agent-korea-full-chat-normalized.txt --title 'KakaoTalk Agent Korea full chat (csv normalized to txt)'
```

### 2. Production ingest
```bash
python3 scripts/ontology_ingest.py \
  --root /Users/hoyasung007hotmail.com/Documents/my_project/DocTology \
  --allow-main-repo \
  --build-graph-projection \
  --wiki-reconcile-mode shadow \
  --raw-path raw/processed/2026-04-21-kakao-agent-korea-full-chat-normalized.txt
```

### 3. Health / shadow checks
```bash
python3 scripts/llm_wiki.py doctor
python3 scripts/llm_wiki.py reconcile-shadow --root /Users/hoyasung007hotmail.com/Documents/my_project/DocTology
python3 scripts/llm_wiki.py status
```

## Result summary

### Registration
Succeeded.

Created:
- `wiki/sources/source-2026-04-21-kakaotalk-agent-korea-full-chat-csv-normalized-to-txt.md`

Updated:
- `wiki/_meta/index.md`
- `wiki/_meta/log.md`

### Production ingest
Succeeded.

Key output counts after ingest:
- `document_count: 22`
- `message_count: 8467`
- `claim_count: 8467`
- `entity_count: 965`
- `derived_edge_count: 19852`

Shadow reconcile preview:
- `wiki/state/ontology_reconcile_preview.json`
- new Kakao source page appears in affected source pages

### Doctor after ingest
Important signals:
- `Raw total: 22`
- `Source pages: 18`
- `Canonical rows: 34879`
- `Derived edges: 19852`
- `Graph projection available: True`
- `Save-readiness floor: review_required`
- `Support status counts: provisional=8467`
- `Lifecycle state counts: draft=8467`

Interpretation:
- ingest path is working
- graph projection is being rebuilt
- current canonical truth is populated
- but all new claim support remains provisional/draft, so this is not save-ready promotion output yet

## Ratel-related evidence found
The current branch does **not** have an `ask` command yet, so this validation was done at the evidence layer.

Confirmed raw evidence in the ingested file:
- `라텔 / 개발: 카피바라 나오면 그때 던질까 생각중입니다`
- `라텔 / 개발: 오픈클로 자체 보다는 이제 가재에 더 관심을`
- `라텔 / 개발: 바닷가재 그 자체`
- `라텔 / 개발: 개미는 사실 분업을 알아서 해서`
- `라텔 / 개발: Task 당 몇마리를 쓸지는 군체가 알아서 정합니다`

Confirmed canonical presence after ingest:
- `documents.jsonl` contains the Kakao document row
- `segments.jsonl` contains the ant / creature / reason-bearing lines
- `messages.jsonl` contains the related multi-line windows such as:
  - `유저타입 ant?`
  - `Ant-only`
  - `개미 운명인가`
  - `아전개미`
  - `기승전 개미`

## Important limitation

This is **not yet** an answer-runtime validation.

Why:
- `scripts/llm_wiki.py` has no `ask` subcommand
- `scripts/doctology.py` is still absent on this branch
- `scripts/workbench/repository.py` is absent, so `query_preview()`, `source_detail()`, and `review_summary()` are unavailable

So the current branch can now prove:
- source registration works
- production ingest works
- canonical evidence exists
- graph projection rebuild works

But it still cannot run the previous automated `라텔 질문` ask comparison loop.

## Next practical step

To move from **evidence-layer validation** to **question-answer validation**, the smallest next useful absorption is:
1. `scripts/workbench/repository.py`
2. `scripts/workbench/llm_config.py`

That would restore:
- `source_detail()`
- `review_summary()`
- `query_preview()`

without immediately requiring the full workbench UI.

## Bottom line

The growth-wiki P0 branch can successfully ingest the KakaoTalk normalized `.txt` and materialize the Ratel/ant/creature evidence into canonical JSONL + graph projection.
What it still lacks is the query/runtime layer needed to turn that evidence into an automated ask benchmark.
