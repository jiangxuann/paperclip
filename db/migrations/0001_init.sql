-- 0001_init.sql
-- Initial schema for Paperclip content pipeline
-- Target: PostgreSQL 13+

BEGIN;

-- Extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS citext;

-- Utility: updated_at trigger
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Enums
DO $$ BEGIN
  CREATE TYPE project_status AS ENUM ('processing', 'completed', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE file_type AS ENUM ('pdf', 'txt', 'docx', 'md');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE upload_status AS ENUM ('uploaded', 'processing', 'parsed', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE content_block_type AS ENUM (
    'heading', 'paragraph', 'list_item', 'table', 'figure', 'code', 'quote', 'caption', 'footnote', 'page_header', 'page_footer'
  );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE media_type AS ENUM ('image', 'diagram', 'chart', 'table', 'other');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE entity_type AS ENUM ('quote', 'statistic', 'key_concept');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE task_type AS ENUM ('upload', 'parse', 'analyze', 'segment', 'visual_generate');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE task_status AS ENUM ('queued', 'running', 'completed', 'failed', 'canceled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE segment_status AS ENUM ('draft', 'generated', 'edited', 'approved', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE visual_type AS ENUM ('chart', 'infographic', 'diagram', 'image');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE visual_status AS ENUM ('queued', 'generating', 'ready', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Users (minimal, replace/merge with your auth system as needed)
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email CITEXT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Projects
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status project_status NOT NULL DEFAULT 'processing',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);

CREATE TRIGGER trg_projects_updated_at
BEFORE UPDATE ON projects
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Documents
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  filename VARCHAR(512) NOT NULL,
  file_type file_type NOT NULL,
  file_size BIGINT CHECK (file_size >= 0),
  file_url VARCHAR(2048) NOT NULL,
  upload_status upload_status NOT NULL DEFAULT 'uploaded',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
);
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_upload_status ON documents(upload_status);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin ON documents USING GIN (metadata);

CREATE TRIGGER trg_documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Is this needed??
--
-- Document pages (structure preservation)
CREATE TABLE IF NOT EXISTS document_pages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_number INTEGER NOT NULL CHECK (page_number > 0),
  text_content TEXT,
  content_tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('english', coalesce(text_content, ''))
  ) STORED,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(document_id, page_number)
);
CREATE INDEX IF NOT EXISTS idx_document_pages_document_id ON document_pages(document_id);
CREATE INDEX IF NOT EXISTS idx_document_pages_tsv ON document_pages USING GIN (content_tsv);
CREATE INDEX IF NOT EXISTS idx_document_pages_metadata_gin ON document_pages USING GIN (metadata);

CREATE TRIGGER trg_document_pages_updated_at
BEFORE UPDATE ON document_pages
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Content blocks (paragraphs, headings, tables, figures, etc.)
CREATE TABLE IF NOT EXISTS content_blocks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_id UUID REFERENCES document_pages(id) ON DELETE CASCADE,
  block_type content_block_type NOT NULL,
  order_index INTEGER NOT NULL DEFAULT 0,
  text_content TEXT,
  text_tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('english', coalesce(text_content, ''))
  ) STORED,
  bbox JSONB, -- {x, y, width, height} in page coords
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_content_blocks_document_id ON content_blocks(document_id);
CREATE INDEX IF NOT EXISTS idx_content_blocks_page_id ON content_blocks(page_id);
CREATE INDEX IF NOT EXISTS idx_content_blocks_type ON content_blocks(block_type);
CREATE INDEX IF NOT EXISTS idx_content_blocks_order ON content_blocks(document_id, page_id, order_index);
CREATE INDEX IF NOT EXISTS idx_content_blocks_tsv ON content_blocks USING GIN (text_tsv);
CREATE INDEX IF NOT EXISTS idx_content_blocks_metadata_gin ON content_blocks USING GIN (metadata);

CREATE TRIGGER trg_content_blocks_updated_at
BEFORE UPDATE ON content_blocks
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Media assets extracted from documents
CREATE TABLE IF NOT EXISTS media_assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_id UUID REFERENCES document_pages(id) ON DELETE SET NULL,
  source_block_id UUID REFERENCES content_blocks(id) ON DELETE SET NULL,
  media_type media_type NOT NULL,
  file_url VARCHAR(2048) NOT NULL,
  width INTEGER CHECK (width IS NULL OR width > 0),
  height INTEGER CHECK (height IS NULL OR height > 0),
  format VARCHAR(50),
  size_bytes BIGINT CHECK (size_bytes IS NULL OR size_bytes >= 0),
  checksum VARCHAR(128),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(document_id, file_url)
);
CREATE INDEX IF NOT EXISTS idx_media_assets_document_id ON media_assets(document_id);
CREATE INDEX IF NOT EXISTS idx_media_assets_media_type ON media_assets(media_type);
CREATE INDEX IF NOT EXISTS idx_media_assets_checksum ON media_assets(checksum);
CREATE INDEX IF NOT EXISTS idx_media_assets_metadata_gin ON media_assets USING GIN (metadata);

CREATE TRIGGER trg_media_assets_updated_at
BEFORE UPDATE ON media_assets
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Extracted entities: quotes, statistics, key concepts
CREATE TABLE IF NOT EXISTS extracted_entities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  page_id UUID REFERENCES document_pages(id) ON DELETE SET NULL,
  block_id UUID REFERENCES content_blocks(id) ON DELETE SET NULL,
  entity_type entity_type NOT NULL,
  raw_text TEXT,
  normalized JSONB, -- e.g., numbers, units for statistics
  confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  span_start INTEGER, -- char start in block/page text
  span_end INTEGER,   -- char end (exclusive)
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_entities_document_id ON extracted_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON extracted_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_page_block ON extracted_entities(page_id, block_id);
CREATE INDEX IF NOT EXISTS idx_entities_normalized_gin ON extracted_entities USING GIN (normalized);

-- Processing tasks (pipeline orchestration)
CREATE TABLE IF NOT EXISTS processing_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  task task_type NOT NULL,
  status task_status NOT NULL DEFAULT 'queued',
  attempt INTEGER NOT NULL DEFAULT 0,
  params JSONB NOT NULL DEFAULT '{}'::jsonb,
  result JSONB,
  error TEXT,
  queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON processing_tasks(project_id, task, status);
CREATE INDEX IF NOT EXISTS idx_tasks_document ON processing_tasks(document_id, task, status);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON processing_tasks(status, queued_at);

-- Segments (short-form content units)
CREATE TABLE IF NOT EXISTS segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title VARCHAR(255),
  hook TEXT,
  content TEXT,
  duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds BETWEEN 5 AND 120),
  order_index INTEGER NOT NULL DEFAULT 0,
  status segment_status NOT NULL DEFAULT 'draft',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_segments_project_order ON segments(project_id, order_index);
CREATE INDEX IF NOT EXISTS idx_segments_status ON segments(status);
CREATE INDEX IF NOT EXISTS idx_segments_metadata_gin ON segments USING GIN (metadata);

CREATE TRIGGER trg_segments_updated_at
BEFORE UPDATE ON segments
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Provenance mapping: which sources feed a segment
CREATE TABLE IF NOT EXISTS segment_sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  segment_id UUID NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  page_id UUID REFERENCES document_pages(id) ON DELETE SET NULL,
  block_id UUID REFERENCES content_blocks(id) ON DELETE SET NULL,
  media_asset_id UUID REFERENCES media_assets(id) ON DELETE SET NULL,
  weight REAL CHECK (weight IS NULL OR (weight >= 0 AND weight <= 1)),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_segment_sources_has_ref CHECK (
    document_id IS NOT NULL OR block_id IS NOT NULL OR media_asset_id IS NOT NULL
  )
);
CREATE INDEX IF NOT EXISTS idx_segment_sources_segment ON segment_sources(segment_id);
CREATE INDEX IF NOT EXISTS idx_segment_sources_doc ON segment_sources(document_id);
CREATE INDEX IF NOT EXISTS idx_segment_sources_block ON segment_sources(block_id);
CREATE INDEX IF NOT EXISTS idx_segment_sources_media ON segment_sources(media_asset_id);

-- Visuals (generated or curated assets)
CREATE TABLE IF NOT EXISTS visuals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  segment_id UUID REFERENCES segments(id) ON DELETE SET NULL,
  visual_type visual_type NOT NULL,
  status visual_status NOT NULL DEFAULT 'queued',
  storage_url VARCHAR(2048),
  thumbnail_url VARCHAR(2048),
  prompt TEXT,        -- optional prompt used for generation
  generator VARCHAR(128), -- model/tool name
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_visuals_project ON visuals(project_id);
CREATE INDEX IF NOT EXISTS idx_visuals_segment ON visuals(segment_id);
CREATE INDEX IF NOT EXISTS idx_visuals_status ON visuals(status);
CREATE INDEX IF NOT EXISTS idx_visuals_type ON visuals(visual_type);

CREATE TRIGGER trg_visuals_updated_at
BEFORE UPDATE ON visuals
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Visualization data/specs (for charts/infographics)
CREATE TABLE IF NOT EXISTS visualization_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  visual_id UUID NOT NULL REFERENCES visuals(id) ON DELETE CASCADE,
  spec JSONB NOT NULL,  -- e.g., Vega-Lite spec
  data JSONB,           -- normalized data used to render
  source_entity_id UUID REFERENCES extracted_entities(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_visualization_data_visual ON visualization_data(visual_id);

-- Attach original media to segments (integration of extracted assets)
CREATE TABLE IF NOT EXISTS segment_media (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  segment_id UUID NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
  media_asset_id UUID NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
  role VARCHAR(64), -- e.g., background, overlay, reference
  order_index INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(segment_id, media_asset_id)
);
CREATE INDEX IF NOT EXISTS idx_segment_media_segment ON segment_media(segment_id, order_index);

COMMIT;
