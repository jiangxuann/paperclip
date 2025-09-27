-- 070_user_management_configuration.sql
-- User Management & Configuration

BEGIN;

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

-- Create updated_at trigger if not exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    WHERE t.tgname = 'trg_user_preferences_updated_at'
      AND c.relname = 'user_preferences'
  ) THEN
    CREATE TRIGGER trg_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
END;
$$;

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

COMMIT;

