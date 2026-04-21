-- sqlite_operational.schema.sql
-- Purpose: operational index schema for a file-canonical LLM Wiki

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS pages (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  page_type TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  checksum TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS page_links (
  from_page_id TEXT NOT NULL,
  to_page_id TEXT,
  to_link_text TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('resolved', 'unresolved')),
  created_at TEXT NOT NULL,
  FOREIGN KEY (from_page_id) REFERENCES pages(id)
);

CREATE TABLE IF NOT EXISTS page_sources (
  page_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  relation_type TEXT NOT NULL CHECK (relation_type IN ('primary', 'supporting', 'mentioned')),
  PRIMARY KEY (page_id, source_id, relation_type),
  FOREIGN KEY (page_id) REFERENCES pages(id)
);

CREATE TABLE IF NOT EXISTS aliases (
  alias_text TEXT NOT NULL,
  target_type TEXT NOT NULL CHECK (target_type IN ('page', 'entity')),
  target_id TEXT NOT NULL,
  PRIMARY KEY (alias_text, target_type, target_id)
);

CREATE TABLE IF NOT EXISTS tags (
  page_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  PRIMARY KEY (page_id, tag),
  FOREIGN KEY (page_id) REFERENCES pages(id)
);

CREATE TABLE IF NOT EXISTS memories (
  id TEXT PRIMARY KEY,
  memory_type TEXT NOT NULL CHECK (
    memory_type IN ('preference', 'active_context', 'agent_note', 'task_memory', 'working_fact')
  ),
  subject TEXT,
  content TEXT NOT NULL,
  source_ref TEXT,
  confidence REAL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL CHECK (
    job_type IN ('register_source', 'reindex_sqlite', 'refresh_duckdb', 'extract_claims', 'audit_health')
  ),
  status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'success', 'failed')),
  started_at TEXT,
  finished_at TEXT,
  detail TEXT
);

CREATE INDEX IF NOT EXISTS idx_pages_title ON pages(title);
CREATE INDEX IF NOT EXISTS idx_page_links_from ON page_links(from_page_id);
CREATE INDEX IF NOT EXISTS idx_page_links_to ON page_links(to_page_id);
CREATE INDEX IF NOT EXISTS idx_aliases_text ON aliases(alias_text);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

