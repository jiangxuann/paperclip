-- 060_processing_pipeline_analytics.sql
-- Processing Pipeline & Analytics

BEGIN;

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

COMMIT;

