-- duckdb_analytical.schema.sql
-- Purpose: analytical warehouse schema for a file-canonical LLM Wiki

CREATE TABLE IF NOT EXISTS sources (
  source_id VARCHAR PRIMARY KEY,
  source_type VARCHAR,
  uri VARCHAR,
  created_at TIMESTAMP,
  raw_checksum VARCHAR
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
