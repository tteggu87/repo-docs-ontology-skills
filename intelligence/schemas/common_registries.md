# Common Registry Schemas

## content_units.jsonl
Required fields: `unit_id`, `document_id`, `source_family_id`, `profile_id`, `unit_kind`, `sequence`, `text`.

Allowed `unit_kind` defaults:
- `email_message`
- `education_section`
- `report_section`
- `paragraph`

Validation:
- `unit_id` unique
- `document_id` must resolve in `documents.jsonl`
- stable id rule: sha1(document_id + unit_kind + sequence + normalized text prefix)

## observations.jsonl
Required fields: `observation_id`, `profile_id`, `observation_type`, `document_id`, `summary`, `review_state`.

Rules:
- `observation_type` must include namespace (`email.*`, `education.*`, `report.*`, `common.*`)
- `review_state` default: `needs_review`

## analysis_runs.jsonl
Required fields: `analysis_id`, `profile_id`, `created_at`, `wiki_output_path`.

## analysis_findings.jsonl
Required fields: `finding_id`, `analysis_id`, `profile_id`, `finding_key`, `finding_text`, `consistency_status`.

Enums:
- `consistency_status`: `stable`, `changed_with_new_evidence`, `scope_difference`, `method_difference`, `unexplained_flip`, `mixed`, `insufficient_history`
- `conclusion_direction`: `bullish`, `neutral`, `cautious`, `mixed`, `unknown`
