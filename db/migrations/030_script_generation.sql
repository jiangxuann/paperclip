-- 030_script_generation.sql
-- Script Generation

BEGIN;

DO $$ BEGIN
  CREATE TYPE target_platform AS ENUM ('tiktok', 'youtube_shorts', 'instagram_reels', 'general');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE script_status AS ENUM ('generated', 'approved', 'rejected');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE segment_type AS ENUM ('hook', 'content', 'transition', 'conclusion', 'cta');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

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
  source_content_ids UUID[],
  visual_cues JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_script_segments_script_order ON script_segments(script_id, segment_order);

COMMIT;

