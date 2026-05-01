# Profile Observation Contract

This is the draft contract for built-in profile observations.

Important boundary: profile observation code must not become the semantic answer layer. Deterministic code may extract source-backed observations and citation anchors, but semantic compile/query must stay LLM-first over wiki/ontology/source evidence with explicit citations.

## Common fields

- `observation_id`: stable id derived from profile, observation type, unit id, and normalized text
- `profile_id`: one of `email-analysis`, `education-analysis`, `report-consistency-analysis`
- `observation_type`: namespaced type such as `email.topic_mention`
- `unit_id`: source-backed content unit id when available
- `document_id`: canonical document id when available
- `review_state`: default `pending`
- `metadata`: profile-specific fields

## Email metadata

- `email.topic_mention`: `topic`, `subject`, `thread_id`, `sender`
- `email.stance`: `topic`, `stance_label`, `confidence`
- `common.action_item`: `assignee`, `due_hint`, `action_text`
- `common.open_question`: `question_text`, `thread_id`

## Education metadata

- `education.key_concept`: `concept`, `heading`, `difficulty_hint`
- `education.definition`: `concept`, `definition_text`, `citation`
- `common.open_question`: `question_text`, `concept`

## Report metadata

- `report.finding`: `finding_key`, `finding_text`, `citation`
- `report.consistency_signal`: `finding_key`, `consistency_status`, `previous_finding_key`
- `common.open_question`: `question_text`, `section`
