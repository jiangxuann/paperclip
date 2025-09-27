-- 0002_app_schema.sql
-- Extend schema to cover Script Generation, Visuals, Videos, Jobs, Analytics, Users
-- and provide compatibility views for document_content, document_assets, document_data_points

BEGIN;

-- Enums for the app layer
DO $$ BEGIN
  CREATE TYPE doc_content_type AS ENUM ('heading', 'paragraph', 'list', 'quote', 'table');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE asset_type AS ENUM ('image', 'chart', 'diagram', 'table', 'formula');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE data_point_type AS ENUM ('number', 'percentage', 'date', 'currency', 'metric');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE target_platform AS ENUM ('tiktok', 'youtube_shorts', 'instagram_reels', 'general');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE script_status AS ENUM ('generated', 'approved', 'rejected');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE segment_type AS ENUM ('hook', 'content', 'transition', 'conclusion', 'cta');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE generated_visual_type AS ENUM ('background', 'overlay', 'chart', 'animation', 'text_graphic');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE template_category AS ENUM ('educational', 'corporate', 'casual', 'tech', 'medical');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE render_status AS ENUM ('queued', 'rendering', 'completed', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE job_type AS ENUM ('parse_document', 'generate_script', 'create_visuals', 'render_video');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE job_status AS ENUM ('queued', 'processing', 'completed', 'failed', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE test_metric AS ENUM ('engagement', 'completion', 'shares');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE ab_test_status AS ENUM ('running', 'completed', 'paused');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Minor alignment with requested fields
-- Add optional columns to media_assets to support thumbnails and alt text
DO $$ BEGIN
  ALTER TABLE media_assets ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(2048);
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE media_assets ADD COLUMN IF NOT EXISTS alt_text TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

-- Script generation
CREATE TABLE IF NOT EXISTS video_scripts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title VARCHAR(255),
  total_duration INTEGER CHECK (total_duration IS NULL OR total_duration >= 0),
  target_platform target_platform NOT NULL DEFAULT 'general',
  script_status script_status NOT NULL DEFAULT 'generated',
  generation_prompt TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_video_scripts_project ON video_scripts(project_id);

CREATE TABLE IF NOT EXISTS script_segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  script_id UUID NOT NULL REFERENCES video_scripts(id) ON DELETE CASCADE,
  segment_order INTEGER NOT NULL,
  segment_type segment_type NOT NULL DEFAULT 'content',
  text_content TEXT,
  estimated_duration INTEGER CHECK (estimated_duration IS NULL OR (estimated_duration >= 0 AND estimated_duration <= 600)),
  source_content_ids UUID[], -- references document_content (compat view)
  visual_cues JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_script_segments_script_order ON script_segments(script_id, segment_order);

-- Visuals
CREATE TABLE IF NOT EXISTS generated_visuals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  visual_type generated_visual_type NOT NULL,
  file_url VARCHAR(2048),
  thumbnail_url VARCHAR(2048),
  generation_prompt TEXT,
  generation_model VARCHAR(128),
  style_template VARCHAR(128),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_generated_visuals_project ON generated_visuals(project_id);
CREATE INDEX IF NOT EXISTS idx_generated_visuals_type ON generated_visuals(visual_type);

CREATE TABLE IF NOT EXISTS visual_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  category template_category NOT NULL,
  template_config JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  usage_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_visual_templates_category ON visual_templates(category);
CREATE INDEX IF NOT EXISTS idx_visual_templates_active ON visual_templates(is_active);

-- Video production
CREATE TABLE IF NOT EXISTS videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  script_id UUID REFERENCES video_scripts(id) ON DELETE SET NULL,
  title VARCHAR(255),
  description TEXT,
  duration INTEGER CHECK (duration IS NULL OR duration >= 0),
  resolution VARCHAR(64),
  file_url VARCHAR(2048),
  thumbnail_url VARCHAR(2048),
  platform_optimized VARCHAR(64)[],
  render_status render_status NOT NULL DEFAULT 'queued',
  render_progress INTEGER NOT NULL DEFAULT 0 CHECK (render_progress >= 0 AND render_progress <= 100),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_videos_project_status ON videos(project_id, render_status);

CREATE TABLE IF NOT EXISTS video_segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  script_segment_id UUID REFERENCES script_segments(id) ON DELETE SET NULL,
  start_time DOUBLE PRECISION CHECK (start_time IS NULL OR start_time >= 0),
  end_time DOUBLE PRECISION CHECK (end_time IS NULL OR end_time >= 0),
  visual_assets UUID[],  -- references generated_visuals (no FK on arrays)
  source_assets UUID[],  -- references document_assets (compat view)
  audio_track VARCHAR(2048),
  effects JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_video_segments_video ON video_segments(video_id);

-- Processing jobs
CREATE TABLE IF NOT EXISTS processing_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  job_type job_type NOT NULL,
  status job_status NOT NULL DEFAULT 'queued',
  priority INTEGER NOT NULL DEFAULT 0,
  progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
  error_message TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status_priority ON processing_jobs(status, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_project ON processing_jobs(project_id, job_type);

-- Analytics and experiments
CREATE TABLE IF NOT EXISTS video_analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  platform VARCHAR(64) NOT NULL,
  views BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_video_analytics_video_platform ON video_analytics(video_id, platform);

CREATE TABLE IF NOT EXISTS ab_tests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  test_name VARCHAR(255) NOT NULL,
  variant_a_video_id UUID REFERENCES videos(id) ON DELETE SET NULL,
  variant_b_video_id UUID REFERENCES videos(id) ON DELETE SET NULL,
  test_metric test_metric NOT NULL,
  sample_size INTEGER,
  confidence_level REAL,
  results JSONB,
  status ab_test_status NOT NULL DEFAULT 'running',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ab_tests_project ON ab_tests(project_id, status);

-- User settings and usage
CREATE TABLE IF NOT EXISTS user_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  default_style_template UUID REFERENCES visual_templates(id) ON DELETE SET NULL,
  preferred_platforms VARCHAR(64)[],
  video_duration_preference INTEGER CHECK (video_duration_preference IS NULL OR video_duration_preference > 0),
  voice_settings JSONB,
  brand_colors VARCHAR(64)[],
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id);

CREATE TRIGGER trg_user_preferences_updated_at
BEFORE UPDATE ON user_preferences
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS user_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  month_year VARCHAR(7) NOT NULL, -- YYYY-MM
  documents_processed INTEGER NOT NULL DEFAULT 0,
  videos_generated INTEGER NOT NULL DEFAULT 0,
  storage_used BIGINT NOT NULL DEFAULT 0,
  api_calls INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(user_id, month_year),
  CONSTRAINT chk_user_usage_month CHECK (month_year ~ '^[0-9]{4}-[0-9]{2}$')
);
CREATE INDEX IF NOT EXISTS idx_user_usage_user_month ON user_usage(user_id, month_year);

-- Additional composite indexes requested
CREATE INDEX IF NOT EXISTS idx_projects_user_status ON projects(user_id, status);
CREATE INDEX IF NOT EXISTS idx_documents_project_status ON documents(project_id, upload_status);

-- Compatibility views to align naming without duplicating data
DROP VIEW IF EXISTS document_content;
CREATE VIEW document_content AS
SELECT
  cb.id,
  cb.document_id,
  (
    CASE cb.block_type
      WHEN 'heading' THEN 'heading'
      WHEN 'paragraph' THEN 'paragraph'
      WHEN 'list_item' THEN 'list'
      WHEN 'quote' THEN 'quote'
      WHEN 'table' THEN 'table'
      ELSE 'paragraph'
    END
  )::doc_content_type AS content_type,
  cb.text_content,
  dp.page_number,
  cb.order_index AS position_index,
  CASE WHEN cb.block_type = 'heading' THEN COALESCE((cb.metadata->>'level')::INT, 1) ELSE NULL END AS hierarchy_level,
  cb.created_at AS extracted_at
FROM content_blocks cb
LEFT JOIN document_pages dp ON dp.id = cb.page_id;

DROP VIEW IF EXISTS document_assets;
CREATE VIEW document_assets AS
SELECT
  ma.id,
  ma.document_id,
  (
    CASE
      WHEN ma.media_type = 'table' THEN 'table'
      WHEN (ma.metadata->>'category') = 'formula' THEN 'formula'
      WHEN ma.media_type = 'image' THEN 'image'
      WHEN ma.media_type = 'diagram' THEN 'diagram'
      WHEN ma.media_type = 'chart' THEN 'chart'
      ELSE 'image'
    END
  )::asset_type AS asset_type,
  ma.file_url,
  ma.thumbnail_url,
  dp.page_number,
  (ma.bbox->>'x')::FLOAT AS position_x,
  (ma.bbox->>'y')::FLOAT AS position_y,
  (ma.bbox->>'width')::FLOAT AS width,
  (ma.bbox->>'height')::FLOAT AS height,
  COALESCE(ma.alt_text, ma.metadata->>'alt_text') AS alt_text,
  ma.metadata,
  ma.created_at AS extracted_at
FROM media_assets ma
LEFT JOIN document_pages dp ON dp.id = ma.page_id;

DROP VIEW IF EXISTS document_data_points;
CREATE VIEW document_data_points AS
SELECT
  ee.id,
  ee.document_id,
  (
    CASE COALESCE(ee.normalized->>'type', '')
      WHEN 'number' THEN 'number'
      WHEN 'percentage' THEN 'percentage'
      WHEN 'date' THEN 'date'
      WHEN 'currency' THEN 'currency'
      ELSE 'metric'
    END
  )::data_point_type AS data_type,
  COALESCE(ee.normalized->>'value', ee.raw_text) AS value,
  COALESCE(cb.text_content, dp.text_content, ee.raw_text) AS context,
  dp.page_number,
  ee.confidence AS confidence_score,
  ee.created_at AS extracted_at
FROM extracted_entities ee
LEFT JOIN content_blocks cb ON cb.id = ee.block_id
LEFT JOIN document_pages dp ON dp.id = ee.page_id
WHERE ee.entity_type = 'statistic';

COMMIT;

