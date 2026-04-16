-- duckdb_analytical.schema.sql
-- Purpose: analytical warehouse schema for a file-canonical LLM Wiki

CREATE TABLE IF NOT EXISTS sources (
  source_id VARCHAR PRIMARY KEY,
  source_type VARCHAR,
  uri VARCHAR,
  created_at TIMESTAMP,
  raw_checksum VARCHAR
);

CREATE TABLE IF NOT EXISTS chunks (
  chunk_id VARCHAR PRIMARY KEY,
  source_id VARCHAR,
  chunk_index BIGINT,
  text VARCHAR,
  token_count BIGINT
);

CREATE TABLE IF NOT EXISTS claims (
  claim_id VARCHAR PRIMARY KEY,
  source_id VARCHAR,
  chunk_id VARCHAR,
  claim_text VARCHAR,
  confidence DOUBLE,
  extraction_run_id VARCHAR
);

CREATE TABLE IF NOT EXISTS entities (
  entity_id VARCHAR PRIMARY KEY,
  canonical_name VARCHAR,
  entity_type VARCHAR
);

CREATE TABLE IF NOT EXISTS claim_entities (
  claim_id VARCHAR,
  entity_id VARCHAR,
  role VARCHAR
);

CREATE TABLE IF NOT EXISTS relations (
  relation_id VARCHAR PRIMARY KEY,
  source_entity_id VARCHAR,
  relation_type VARCHAR,
  target_entity_id VARCHAR,
  evidence_claim_id VARCHAR,
  relation_confidence DOUBLE,
  extraction_run_id VARCHAR
);

CREATE TABLE IF NOT EXISTS page_coverage_snapshots (
  page_id VARCHAR,
  run_id VARCHAR,
  source_count BIGINT,
  claim_count BIGINT,
  entity_count BIGINT,
  freshness_score DOUBLE,
  coverage_score DOUBLE,
  captured_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_events (
  run_id VARCHAR,
  phase VARCHAR,
  status VARCHAR,
  detail VARCHAR,
  page_id VARCHAR,
  severity VARCHAR,
  created_at TIMESTAMP
);

