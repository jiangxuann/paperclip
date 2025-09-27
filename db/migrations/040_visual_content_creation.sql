-- 040_visual_content_creation.sql
-- Visual Content Creation

BEGIN;

DO $$ BEGIN
  CREATE TYPE generated_visual_type AS ENUM ('background', 'overlay', 'chart', 'animation', 'text_graphic');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE template_category AS ENUM ('educational', 'corporate', 'casual', 'tech', 'medical');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

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

COMMIT;

