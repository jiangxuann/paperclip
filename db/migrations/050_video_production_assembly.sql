-- 050_video_production_assembly.sql
-- Video Production & Assembly

BEGIN;

DO $$ BEGIN
  CREATE TYPE render_status AS ENUM ('queued', 'rendering', 'completed', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

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
  visual_assets UUID[],
  source_assets UUID[],
  audio_track VARCHAR(2048),
  effects JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_video_segments_video ON video_segments(video_id);

COMMIT;

