"""
Concrete repository implementations using asyncpg.

Provides database-backed implementations of domain repositories
for PostgreSQL (Supabase-compatible) database.
"""

import asyncpg
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from core.domain.entities import (
    Project, ContentSource, PDFSource, URLSource, Chapter, Script, Video,
    ProcessingJob, VideoAnalytics, ABTest, SimpleProject, Document,
    JobType, JobStatus, TestMetric, ABTestStatus, ProcessingStatus,
    ProjectStatus, FileType, UploadStatus
)
from core.domain.repositories import (
    ProjectRepository, ContentSourceRepository, ChapterRepository,
    ScriptRepository, VideoRepository,
    ProcessingJobRepository, VideoAnalyticsRepository, ABTestRepository,
    SimpleProjectRepository, DocumentRepository
)
from core.domain.value_objects import ProjectId, SourceId, ChapterId, ScriptId, VideoId


class DatabaseConnection:
    """Database connection manager."""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool."""
        self.pool = await asyncpg.create_pool(self.dsn)

    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()

    async def get_connection(self):
        """Get a database connection from the pool."""
        if not self.pool:
            await self.connect()
        return await self.pool.acquire()


class PostgresProjectRepository(ProjectRepository):
    """PostgreSQL implementation of ProjectRepository."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create(self, project: Project) -> Project:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                INSERT INTO projects (id, name, description, status, config, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, name, description, status, config, created_at, updated_at
            """, project.id, project.name, project.description, project.status.value,
                 project.config, project.created_at, project.updated_at)

            return Project(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                status=ProcessingStatus(row['status']),
                config=row['config'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_by_id(self, project_id: ProjectId) -> Optional[Project]:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                SELECT id, name, description, status, config, created_at, updated_at
                FROM projects WHERE id = $1
            """, project_id)

            if not row:
                return None

            return Project(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                status=ProcessingStatus(row['status']),
                config=row['config'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_all(self) -> List[Project]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, name, description, status, config, created_at, updated_at
                FROM projects ORDER BY created_at DESC
            """)

            return [Project(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                status=ProcessingStatus(row['status']),
                config=row['config'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ) for row in rows]
        finally:
            await self.db.pool.release(conn)

    async def update(self, project: Project) -> Project:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                UPDATE projects
                SET name = $2, description = $3, status = $4, config = $5, updated_at = $6
                WHERE id = $1
                RETURNING id, name, description, status, config, created_at, updated_at
            """, project.id, project.name, project.description, project.status.value,
                 project.config, project.updated_at)

            return Project(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                status=ProcessingStatus(row['status']),
                config=row['config'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def delete(self, project_id: ProjectId) -> None:
        conn = await self.db.get_connection()
        try:
            await conn.execute("DELETE FROM projects WHERE id = $1", project_id)
        finally:
            await self.db.pool.release(conn)

    async def get_with_sources(self, project_id: ProjectId) -> Optional[Project]:
        # Implementation would join with sources table
        # For brevity, using basic get_by_id for now
        return await self.get_by_id(project_id)


class PostgresProcessingJobRepository(ProcessingJobRepository):
    """PostgreSQL implementation of ProcessingJobRepository."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create(self, job: ProcessingJob) -> ProcessingJob:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                INSERT INTO processing_jobs (id, project_id, job_type, status, priority, progress,
                                           error_message, started_at, completed_at, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id, project_id, job_type, status, priority, progress,
                         error_message, started_at, completed_at, created_at
            """, job.id, job.project_id, job.job_type.value, job.status.value, job.priority,
                 job.progress, job.error_message, job.started_at, job.completed_at, job.created_at)

            return ProcessingJob(
                id=row['id'],
                project_id=row['project_id'],
                job_type=JobType(row['job_type']),
                status=JobStatus(row['status']),
                priority=row['priority'],
                progress=row['progress'],
                error_message=row['error_message'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_by_id(self, job_id: UUID) -> Optional[ProcessingJob]:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                SELECT id, project_id, job_type, status, priority, progress,
                       error_message, started_at, completed_at, created_at
                FROM processing_jobs WHERE id = $1
            """, job_id)

            if not row:
                return None

            return ProcessingJob(
                id=row['id'],
                project_id=row['project_id'],
                job_type=JobType(row['job_type']),
                status=JobStatus(row['status']),
                priority=row['priority'],
                progress=row['progress'],
                error_message=row['error_message'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_by_project_id(self, project_id: ProjectId) -> List[ProcessingJob]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, project_id, job_type, status, priority, progress,
                       error_message, started_at, completed_at, created_at
                FROM processing_jobs
                WHERE project_id = $1
                ORDER BY created_at DESC
            """, project_id)

            return [ProcessingJob(
                id=row['id'],
                project_id=row['project_id'],
                job_type=JobType(row['job_type']),
                status=JobStatus(row['status']),
                priority=row['priority'],
                progress=row['progress'],
                error_message=row['error_message'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                created_at=row['created_at']
            ) for row in rows]
        finally:
            await self.db.pool.release(conn)

    async def get_by_status(self, status: str) -> List[ProcessingJob]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, project_id, job_type, status, priority, progress,
                       error_message, started_at, completed_at, created_at
                FROM processing_jobs
                WHERE status = $1
                ORDER BY priority DESC, created_at ASC
            """, status)

            return [ProcessingJob(
                id=row['id'],
                project_id=row['project_id'],
                job_type=JobType(row['job_type']),
                status=JobStatus(row['status']),
                priority=row['priority'],
                progress=row['progress'],
                error_message=row['error_message'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                created_at=row['created_at']
            ) for row in rows]
        finally:
            await self.db.pool.release(conn)

    async def get_queued_jobs(self, limit: int = 50) -> List[ProcessingJob]:
        return await self.get_by_status('queued')

    async def update(self, job: ProcessingJob) -> ProcessingJob:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                UPDATE processing_jobs
                SET status = $2, priority = $3, progress = $4, error_message = $5,
                    started_at = $6, completed_at = $7
                WHERE id = $1
                RETURNING id, project_id, job_type, status, priority, progress,
                         error_message, started_at, completed_at, created_at
            """, job.id, job.status.value, job.priority, job.progress, job.error_message,
                 job.started_at, job.completed_at)

            return ProcessingJob(
                id=row['id'],
                project_id=row['project_id'],
                job_type=JobType(row['job_type']),
                status=JobStatus(row['status']),
                priority=row['priority'],
                progress=row['progress'],
                error_message=row['error_message'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def delete(self, job_id: UUID) -> None:
        conn = await self.db.get_connection()
        try:
            await conn.execute("DELETE FROM processing_jobs WHERE id = $1", job_id)
        finally:
            await self.db.pool.release(conn)

    async def get_active_jobs_for_project(self, project_id: ProjectId) -> List[ProcessingJob]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, project_id, job_type, status, priority, progress,
                       error_message, started_at, completed_at, created_at
                FROM processing_jobs
                WHERE project_id = $1 AND status IN ('queued', 'processing')
                ORDER BY priority DESC, created_at ASC
            """, project_id)

            return [ProcessingJob(
                id=row['id'],
                project_id=row['project_id'],
                job_type=JobType(row['job_type']),
                status=JobStatus(row['status']),
                priority=row['priority'],
                progress=row['progress'],
                error_message=row['error_message'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                created_at=row['created_at']
            ) for row in rows]
        finally:
            await self.db.pool.release(conn)


class PostgresVideoAnalyticsRepository(VideoAnalyticsRepository):
    """PostgreSQL implementation of VideoAnalyticsRepository."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create(self, analytics: VideoAnalytics) -> VideoAnalytics:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                INSERT INTO video_analytics (id, video_id, platform, views, created_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, video_id, platform, views, created_at
            """, analytics.id, analytics.video_id, analytics.platform, analytics.views, analytics.created_at)

            return VideoAnalytics(
                id=row['id'],
                video_id=row['video_id'],
                platform=row['platform'],
                views=row['views'],
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_by_video_id(self, video_id: VideoId) -> List[VideoAnalytics]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, video_id, platform, views, created_at
                FROM video_analytics
                WHERE video_id = $1
                ORDER BY created_at DESC
            """, video_id)

            return [VideoAnalytics(
                id=row['id'],
                video_id=row['video_id'],
                platform=row['platform'],
                views=row['views'],
                created_at=row['created_at']
            ) for row in rows]
        finally:
            await self.db.pool.release(conn)

    async def get_by_platform(self, video_id: VideoId, platform: str) -> Optional[VideoAnalytics]:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                SELECT id, video_id, platform, views, created_at
                FROM video_analytics
                WHERE video_id = $1 AND platform = $2
            """, video_id, platform)

            if not row:
                return None

            return VideoAnalytics(
                id=row['id'],
                video_id=row['video_id'],
                platform=row['platform'],
                views=row['views'],
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def increment_views(self, video_id: VideoId, platform: str, count: int = 1) -> VideoAnalytics:
        conn = await self.db.get_connection()
        try:
            # Try to update existing record
            row = await conn.fetchrow("""
                UPDATE video_analytics
                SET views = views + $3
                WHERE video_id = $1 AND platform = $2
                RETURNING id, video_id, platform, views, created_at
            """, video_id, platform, count)

            if row:
                return VideoAnalytics(
                    id=row['id'],
                    video_id=row['video_id'],
                    platform=row['platform'],
                    views=row['views'],
                    created_at=row['created_at']
                )

            # Create new record if none exists
            analytics = VideoAnalytics(
                id=UUID(),
                video_id=video_id,
                platform=platform,
                views=count
            )
            return await self.create(analytics)
        finally:
            await self.db.pool.release(conn)

    async def get_total_views(self, video_id: VideoId) -> int:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                SELECT COALESCE(SUM(views), 0) as total_views
                FROM video_analytics
                WHERE video_id = $1
            """, video_id)

            return row['total_views']
        finally:
            await self.db.pool.release(conn)

    async def get_platform_stats(self, video_id: VideoId) -> Dict[str, int]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT platform, SUM(views) as total_views
                FROM video_analytics
                WHERE video_id = $1
                GROUP BY platform
            """, video_id)

            return {row['platform']: row['total_views'] for row in rows}
        finally:
            await self.db.pool.release(conn)


class PostgresABTestRepository(ABTestRepository):
    """PostgreSQL implementation of ABTestRepository."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create(self, test: ABTest) -> ABTest:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                INSERT INTO ab_tests (id, project_id, test_name, variant_a_video_id, variant_b_video_id,
                                    test_metric, sample_size, confidence_level, results, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id, project_id, test_name, variant_a_video_id, variant_b_video_id,
                         test_metric, sample_size, confidence_level, results, status, created_at
            """, test.id, test.project_id, test.test_name, test.variant_a_video_id, test.variant_b_video_id,
                 test.test_metric.value, test.sample_size, test.confidence_level, test.results,
                 test.status.value, test.created_at)

            return ABTest(
                id=row['id'],
                project_id=row['project_id'],
                test_name=row['test_name'],
                variant_a_video_id=row['variant_a_video_id'],
                variant_b_video_id=row['variant_b_video_id'],
                test_metric=TestMetric(row['test_metric']),
                sample_size=row['sample_size'],
                confidence_level=row['confidence_level'],
                results=row['results'],
                status=ABTestStatus(row['status']),
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_by_id(self, test_id: UUID) -> Optional[ABTest]:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                SELECT id, project_id, test_name, variant_a_video_id, variant_b_video_id,
                       test_metric, sample_size, confidence_level, results, status, created_at
                FROM ab_tests WHERE id = $1
            """, test_id)

            if not row:
                return None

            return ABTest(
                id=row['id'],
                project_id=row['project_id'],
                test_name=row['test_name'],
                variant_a_video_id=row['variant_a_video_id'],
                variant_b_video_id=row['variant_b_video_id'],
                test_metric=TestMetric(row['test_metric']),
                sample_size=row['sample_size'],
                confidence_level=row['confidence_level'],
                results=row['results'],
                status=ABTestStatus(row['status']),
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_by_project_id(self, project_id: ProjectId) -> List[ABTest]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, project_id, test_name, variant_a_video_id, variant_b_video_id,
                       test_metric, sample_size, confidence_level, results, status, created_at
                FROM ab_tests
                WHERE project_id = $1
                ORDER BY created_at DESC
            """, project_id)

            return [ABTest(
                id=row['id'],
                project_id=row['project_id'],
                test_name=row['test_name'],
                variant_a_video_id=row['variant_a_video_id'],
                variant_b_video_id=row['variant_b_video_id'],
                test_metric=TestMetric(row['test_metric']),
                sample_size=row['sample_size'],
                confidence_level=row['confidence_level'],
                results=row['results'],
                status=ABTestStatus(row['status']),
                created_at=row['created_at']
            ) for row in rows]
        finally:
            await self.db.pool.release(conn)

    async def get_active_tests(self) -> List[ABTest]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, project_id, test_name, variant_a_video_id, variant_b_video_id,
                       test_metric, sample_size, confidence_level, results, status, created_at
                FROM ab_tests
                WHERE status = 'running'
                ORDER BY created_at DESC
            """)

            return [ABTest(
                id=row['id'],
                project_id=row['project_id'],
                test_name=row['test_name'],
                variant_a_video_id=row['variant_a_video_id'],
                variant_b_video_id=row['variant_b_video_id'],
                test_metric=TestMetric(row['test_metric']),
                sample_size=row['sample_size'],
                confidence_level=row['confidence_level'],
                results=row['results'],
                status=ABTestStatus(row['status']),
                created_at=row['created_at']
            ) for row in rows]
        finally:
            await self.db.pool.release(conn)

    async def update(self, test: ABTest) -> ABTest:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                UPDATE ab_tests
                SET test_name = $2, variant_a_video_id = $3, variant_b_video_id = $4,
                    test_metric = $5, sample_size = $6, confidence_level = $7,
                    results = $8, status = $9
                WHERE id = $1
                RETURNING id, project_id, test_name, variant_a_video_id, variant_b_video_id,
                         test_metric, sample_size, confidence_level, results, status, created_at
            """, test.id, test.test_name, test.variant_a_video_id, test.variant_b_video_id,
                 test.test_metric.value, test.sample_size, test.confidence_level, test.results,
                 test.status.value)

            return ABTest(
                id=row['id'],
                project_id=row['project_id'],
                test_name=row['test_name'],
                variant_a_video_id=row['variant_a_video_id'],
                variant_b_video_id=row['variant_b_video_id'],
                test_metric=TestMetric(row['test_metric']),
                sample_size=row['sample_size'],
                confidence_level=row['confidence_level'],
                results=row['results'],
                status=ABTestStatus(row['status']),
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def delete(self, test_id: UUID) -> None:
        conn = await self.db.get_connection()
        try:
            await conn.execute("DELETE FROM ab_tests WHERE id = $1", test_id)
        finally:
            await self.db.pool.release(conn)

    async def get_tests_by_video(self, video_id: VideoId) -> List[ABTest]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, project_id, test_name, variant_a_video_id, variant_b_video_id,
                       test_metric, sample_size, confidence_level, results, status, created_at
                FROM ab_tests
                WHERE variant_a_video_id = $1 OR variant_b_video_id = $1
                ORDER BY created_at DESC
            """, video_id)

            return [ABTest(
                id=row['id'],
                project_id=row['project_id'],
                test_name=row['test_name'],
                variant_a_video_id=row['variant_a_video_id'],
                variant_b_video_id=row['variant_b_video_id'],
                test_metric=TestMetric(row['test_metric']),
                sample_size=row['sample_size'],
                confidence_level=row['confidence_level'],
                results=row['results'],
                status=ABTestStatus(row['status']),
                created_at=row['created_at']
            ) for row in rows]
        finally:
            await self.db.pool.release(conn)

class PostgresSimpleProjectRepository(SimpleProjectRepository):
    """PostgreSQL implementation of SimpleProjectRepository."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create(self, project: SimpleProject) -> SimpleProject:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                INSERT INTO projects (id, name, description, user_id, status, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, name, description, user_id, status, created_at, updated_at
            """, project.id, project.name, project.description, project.user_id, project.status.value,
                 project.created_at, project.updated_at)

            return SimpleProject(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                user_id=row['user_id'],
                status=ProjectStatus(row['status']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_by_id(self, project_id: UUID) -> Optional[SimpleProject]:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                SELECT id, name, description, user_id, status, created_at, updated_at
                FROM projects WHERE id = $1
            """, project_id)

            if not row:
                return None

            return SimpleProject(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                user_id=row['user_id'],
                status=ProjectStatus(row['status']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_by_user_id(self, user_id: UUID) -> List[SimpleProject]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, name, description, user_id, status, created_at, updated_at
                FROM projects WHERE user_id = $1 ORDER BY created_at DESC
            """, user_id)

            return [SimpleProject(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                user_id=row['user_id'],
                status=ProjectStatus(row['status']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ) for row in rows]
        finally:
            await self.db.pool.release(conn)

    async def update(self, project: SimpleProject) -> SimpleProject:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                UPDATE projects
                SET name = $2, description = $3, status = $4, updated_at = $5
                WHERE id = $1
                RETURNING id, name, description, user_id, status, created_at, updated_at
            """, project.id, project.name, project.description, project.status.value, project.updated_at)

            return SimpleProject(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                user_id=row['user_id'],
                status=ProjectStatus(row['status']),
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def delete(self, project_id: UUID) -> None:
        conn = await self.db.get_connection()
        try:
            await conn.execute("DELETE FROM projects WHERE id = $1", project_id)
        finally:
            await self.db.pool.release(conn)


class PostgresDocumentRepository(DocumentRepository):
    """PostgreSQL implementation of DocumentRepository."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def create(self, document: Document) -> Document:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                INSERT INTO documents (id, project_id, filename, file_type, file_size, file_url, upload_status, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id, project_id, filename, file_type, file_size, file_url, upload_status, metadata, created_at
            """, document.id, document.project_id, document.filename, document.file_type.value,
                 document.file_size, document.file_url, document.upload_status.value, document.metadata, document.created_at)

            return Document(
                id=row['id'],
                project_id=row['project_id'],
                filename=row['filename'],
                file_type=FileType(row['file_type']),
                file_size=row['file_size'],
                file_url=row['file_url'],
                upload_status=UploadStatus(row['upload_status']),
                metadata=row['metadata'],
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_by_id(self, document_id: UUID) -> Optional[Document]:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                SELECT id, project_id, filename, file_type, file_size, file_url, upload_status, metadata, created_at
                FROM documents WHERE id = $1
            """, document_id)

            if not row:
                return None

            return Document(
                id=row['id'],
                project_id=row['project_id'],
                filename=row['filename'],
                file_type=FileType(row['file_type']),
                file_size=row['file_size'],
                file_url=row['file_url'],
                upload_status=UploadStatus(row['upload_status']),
                metadata=row['metadata'],
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def get_by_project_id(self, project_id: UUID) -> List[Document]:
        conn = await self.db.get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, project_id, filename, file_type, file_size, file_url, upload_status, metadata, created_at
                FROM documents WHERE project_id = $1 ORDER BY created_at DESC
            """, project_id)

            return [Document(
                id=row['id'],
                project_id=row['project_id'],
                filename=row['filename'],
                file_type=FileType(row['file_type']),
                file_size=row['file_size'],
                file_url=row['file_url'],
                upload_status=UploadStatus(row['upload_status']),
                metadata=row['metadata'],
                created_at=row['created_at']
            ) for row in rows]
        finally:
            await self.db.pool.release(conn)

    async def update(self, document: Document) -> Document:
        conn = await self.db.get_connection()
        try:
            row = await conn.fetchrow("""
                UPDATE documents
                SET filename = $2, file_type = $3, file_size = $4, file_url = $5, upload_status = $6, metadata = $7
                WHERE id = $1
                RETURNING id, project_id, filename, file_type, file_size, file_url, upload_status, metadata, created_at
            """, document.id, document.filename, document.file_type.value, document.file_size,
                 document.file_url, document.upload_status.value, document.metadata)

            return Document(
                id=row['id'],
                project_id=row['project_id'],
                filename=row['filename'],
                file_type=FileType(row['file_type']),
                file_size=row['file_size'],
                file_url=row['file_url'],
                upload_status=UploadStatus(row['upload_status']),
                metadata=row['metadata'],
                created_at=row['created_at']
            )
        finally:
            await self.db.pool.release(conn)

    async def delete(self, document_id: UUID) -> None:
        conn = await self.db.get_connection()
        try:
            await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
        finally:
            await self.db.pool.release(conn)


# Placeholder implementations for other repositories (to be implemented)

# Placeholder implementations for other repositories (to be implemented)
class PostgresContentSourceRepository(ContentSourceRepository):
    async def create(self, source: ContentSource) -> ContentSource: pass
    async def get_by_id(self, source_id: SourceId) -> Optional[ContentSource]: pass
    async def get_by_project_id(self, project_id: ProjectId) -> List[ContentSource]: pass
    async def update(self, source: ContentSource) -> ContentSource: pass
    async def delete(self, source_id: SourceId) -> None: pass
    async def create_pdf_source(self, source: PDFSource) -> PDFSource: pass
    async def create_url_source(self, source: URLSource) -> URLSource: pass
    async def get_pdf_sources(self, project_id: ProjectId) -> List[PDFSource]: pass
    async def get_url_sources(self, project_id: ProjectId) -> List[URLSource]: pass


class PostgresChapterRepository(ChapterRepository):
    async def create(self, chapter: Chapter) -> Chapter: pass
    async def get_by_id(self, chapter_id: ChapterId) -> Optional[Chapter]: pass
    async def get_by_source_id(self, source_id: SourceId) -> List[Chapter]: pass
    async def get_by_project_id(self, project_id: ProjectId) -> List[Chapter]: pass
    async def update(self, chapter: Chapter) -> Chapter: pass
    async def delete(self, chapter_id: ChapterId) -> None: pass
    async def create_batch(self, chapters: List[Chapter]) -> List[Chapter]: pass


class PostgresScriptRepository(ScriptRepository):
    async def create(self, script: Script) -> Script: pass
    async def get_by_id(self, script_id: ScriptId) -> Optional[Script]: pass
    async def get_by_chapter_id(self, chapter_id: ChapterId) -> Optional[Script]: pass
    async def get_by_project_id(self, project_id: ProjectId) -> List[Script]: pass
    async def update(self, script: Script) -> Script: pass
    async def delete(self, script_id: ScriptId) -> None: pass
    async def get_ready_for_video_generation(self) -> List[Script]: pass


class PostgresVideoRepository(VideoRepository):
    async def create(self, video: Video) -> Video: pass
    async def get_by_id(self, video_id: VideoId) -> Optional[Video]: pass
    async def get_by_script_id(self, script_id: ScriptId) -> Optional[Video]: pass
    async def get_by_project_id(self, project_id: ProjectId) -> List[Video]: pass
    async def update(self, video: Video) -> Video: pass
    async def delete(self, video_id: VideoId) -> None: pass
    async def get_processing_videos(self) -> List[Video]: pass
    async def get_completed_videos(self, project_id: ProjectId) -> List[Video]: passc