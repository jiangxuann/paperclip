Database schema for Paperclip

Overview
- PostgreSQL schema supporting:
  - Document parsing with structure preservation (`document_pages`, `content_blocks`)
  - Media extraction and management (`media_assets`)
  - Classification of quotes, statistics, key concepts (`extracted_entities`)
  - Script generation and segmentation (`segments`, `segment_sources`)
  - Visual content generation and integration (`visuals`, `visualization_data`, `segment_media`)
  - Pipeline orchestration (`processing_tasks`)
  - Video scripts and segments (`video_scripts`, `script_segments`)
  - Video production and mapping (`videos`, `video_segments`)
  - Generated visuals and templates (`generated_visuals`, `visual_templates`)
  - Jobs and analytics (`processing_jobs`, `video_analytics`, `ab_tests`)
  - User settings and usage (`user_preferences`, `user_usage`)

Quick start
1) Ensure PostgreSQL 13+ and `psql` are installed.
2) Create a database and set `DATABASE_URL` (or pass connection flags to `psql`).
3) Apply the initial migration:

   psql "$DATABASE_URL" -f db/migrations/0001_init.sql

4) Apply the extended app schema:

   psql "$DATABASE_URL" -f db/migrations/0002_app_schema.sql

Notes
- Extensions: The migration enables `pgcrypto`, `pg_trgm`, and `btree_gin`.
- Updated timestamps: Most tables have `updated_at` maintained by the `set_updated_at()` trigger.
- Full‑text search: `document_pages.content_tsv` and `content_blocks.text_tsv` are generated columns with GIN indexes.
- JSONB: Rich metadata fields are indexed with GIN for flexible querying.
- Enums: Enumerated types are used for statuses and types; adding new values requires a migration (ALTER TYPE ... ADD VALUE ...).

Entity map (core)
- projects: Top‑level container per user.
- documents: Source files (pdf/txt/docx/md) tied to projects.
- document_pages: Page‑level text + metadata; preserves pagination.
- content_blocks: Structured blocks (paragraphs, headings, tables, figures) with order and optional bounding boxes.
- media_assets: Extracted images/diagrams/charts/tables stored in object storage.
- extracted_entities: Quotes, statistics, and key concepts with provenance and confidence.
- processing_tasks: Tracks pipeline steps and outcomes (upload/parse/analyze/segment/visual_generate).
- segments: Short‑form content units with hooks and durations.
- segment_sources: Provenance linking segments to document blocks/media.
- visuals: Generated/curated visuals associated to segments/projects.
- visualization_data: Chart/infographic specs and normalized data.
- segment_media: Attach extracted media to segments with roles and ordering.
 - video_scripts: Container for generated scripts per project.
 - script_segments: Ordered segments (hook/content/transition/cta) with optional visual cues.
 - generated_visuals: Produced assets for use in video assembly.
 - visual_templates: Reusable style/layout templates.
 - videos: Final rendered videos with status/progress and metadata.
 - video_segments: Timing map from script segments to the final video, with asset arrays.
 - processing_jobs: Job queue entries for pipeline stages; complements `processing_tasks`.
 - video_analytics: Per-platform counters for published videos.
 - ab_tests: A/B experiments across video variants.
 - user_preferences: Per-user defaults and brand settings.
 - user_usage: Monthly usage aggregation for quotas/billing.

Compatibility views
- document_content: View over `content_blocks` (+ `document_pages`) providing
  the exact shape requested: content_type, text_content, page_number,
  position_index, hierarchy_level, extracted_at.
- document_assets: View over `media_assets` (+ `document_pages`) mapping media
  to asset_type, and exposing positions from `bbox` and alt text.
- document_data_points: View over `extracted_entities` restricted to statistics,
  with normalized type/value and page/context.

Indexes
- Requested compound indexes are created on: `projects(user_id, status)`,
  `documents(project_id, upload_status)`, `script_segments(script_id, segment_order)`,
  `videos(project_id, render_status)`, `processing_jobs(status, priority, created_at)`,
  `video_analytics(video_id, platform)`, `user_usage(user_id, month_year)`.
  Note: `document_content` is a view; underlying index
  `content_blocks(document_id, order_index)` serves its access pattern.

Flow overview (simplified)
- Upload: User creates `projects` and uploads `documents` (cloud `file_url`).
- Parse: Jobs in `processing_jobs` extract text into `content_blocks`/`document_pages`,
  media into `media_assets`, and statistics into `extracted_entities`.
- Analyze: The app queries `document_content`, `document_assets`, and
  `document_data_points` to assemble context.
- Script: Generates `video_scripts` and `script_segments` with `visual_cues`.
- Visuals: Creates `generated_visuals`; optional templates from `visual_templates`.
- Render: Produces `videos` and `video_segments`; status tracked via `processing_jobs`.
- Measure: Stores metrics in `video_analytics` and experiments in `ab_tests`.

Operational guidance
- Deletion behavior: Deleting a project cascades to documents and dependent entities. Deleting a document cascades to pages/blocks/media/entities. Segment/visual links use CASCADE/SET NULL to preserve history where appropriate.
- Query performance: Start with provided indexes; add platform‑specific ones after measuring workload. Consider partitioning large tables by `project_id` if needed at scale.
- Access control: Tie `projects.user_id` to your auth system. Replace the included minimal `users` table or point the FK to your auth schema.
- Observability: Use `processing_tasks` to track end‑to‑end runs and capture errors/results per step.

Examples
- Find all quotes for a project with their page and block context:

  SELECT ee.id, ee.raw_text, dp.page_number, cb.block_type
  FROM extracted_entities ee
  JOIN documents d ON d.id = ee.document_id
  LEFT JOIN document_pages dp ON dp.id = ee.page_id
  LEFT JOIN content_blocks cb ON cb.id = ee.block_id
  WHERE ee.entity_type = 'quote' AND d.project_id = $1
  ORDER BY dp.page_number NULLS LAST;

- Full‑text search across blocks:

  SELECT id, document_id
  FROM content_blocks
  WHERE text_tsv @@ plainto_tsquery('english', $1)
  ORDER BY ts_rank_cd(text_tsv, plainto_tsquery('english', $1)) DESC
  LIMIT 50;
