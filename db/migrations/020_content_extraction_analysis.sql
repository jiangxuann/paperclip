-- 020_content_extraction_analysis.sql
-- Content Extraction & Analysis

BEGIN;

-- App-facing enums (views will cast to these where applicable)
DO $$ BEGIN
  CREATE TYPE doc_content_type AS ENUM ('heading', 'paragraph', 'list', 'quote', 'table');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE asset_type AS ENUM ('image', 'chart', 'diagram', 'table', 'formula');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE data_point_type AS ENUM ('number', 'percentage', 'date', 'currency', 'metric');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Compatibility views (align to requested logical tables)
CREATE OR REPLACE VIEW document_content AS
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

CREATE OR REPLACE VIEW document_assets AS
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

CREATE OR REPLACE VIEW document_data_points AS
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

