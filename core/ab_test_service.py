"""
A/B testing service for video optimization.

Handles variant selection, result calculation, and statistical analysis
for A/B tests comparing different video versions.
"""

import random
import math
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging

from .domain.entities import ABTest, VideoId, TestMetric
from .domain.repositories import ABTestRepository, VideoAnalyticsRepository

logger = logging.getLogger(__name__)


class ABTestService:
    """
    Service for managing A/B tests and variant selection.

    Provides methods for selecting video variants for users and
    calculating test results with statistical significance.
    """

    def __init__(self, ab_test_repo: ABTestRepository, analytics_repo: VideoAnalyticsRepository):
        """
        Initialize A/B test service.

        Args:
            ab_test_repo: Repository for A/B test data
            analytics_repo: Repository for analytics data
        """
        self.ab_test_repo = ab_test_repo
        self.analytics_repo = analytics_repo

    async def select_video_variant(self, test_id: UUID, user_id: Optional[str] = None) -> Optional[VideoId]:
        """
        Select a video variant for a user based on A/B test configuration.

        Uses consistent hashing or random selection to ensure users see
        the same variant across sessions.

        Args:
            test_id: A/B test ID
            user_id: User identifier for consistent assignment

        Returns:
            Selected video variant ID, or None if test not found or inactive
        """
        test = await self.ab_test_repo.get_by_id(test_id)
        if not test or not test.is_active:
            return None

        if not test.variant_a_video_id or not test.variant_b_video_id:
            logger.warning(f"A/B test {test_id} missing video variants")
            return None

        # Use user_id for consistent assignment, fallback to random
        if user_id:
            # Simple hash-based selection for consistency
            hash_value = hash(f"{test_id}:{user_id}") % 100
            selected_variant = test.variant_a_video_id if hash_value < 50 else test.variant_b_video_id
        else:
            # Random selection
            selected_variant = random.choice([test.variant_a_video_id, test.variant_b_video_id])

        logger.debug(f"Selected variant {selected_variant} for test {test_id}, user {user_id}")
        return selected_variant

    async def get_test_results(self, test_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Calculate and return A/B test results with statistical analysis.

        Args:
            test_id: A/B test ID

        Returns:
            Dictionary with test results and statistics, or None if test not found
        """
        test = await self.ab_test_repo.get_by_id(test_id)
        if not test:
            return None

        # Get analytics for both variants
        variant_a_views = await self.analytics_repo.get_total_views(test.variant_a_video_id)
        variant_b_views = await self.analytics_repo.get_total_views(test.variant_b_video_id)

        # Calculate metrics based on test type
        if test.test_metric == TestMetric.ENGAGEMENT:
            # For engagement, we might need more complex metrics
            # For now, use views as proxy
            metric_a = variant_a_views
            metric_b = variant_b_views
            metric_name = "views"
        elif test.test_metric == TestMetric.COMPLETION:
            # Completion rate would require video completion tracking
            # Placeholder implementation
            metric_a = variant_a_views * 0.8  # Assume 80% completion rate
            metric_b = variant_b_views * 0.75
            metric_name = "completion_rate"
        elif test.test_metric == TestMetric.SHARES:
            # Shares would require share tracking
            # Placeholder implementation
            metric_a = variant_a_views * 0.05  # Assume 5% share rate
            metric_b = variant_b_views * 0.03
            metric_name = "shares"
        else:
            metric_a = variant_a_views
            metric_b = variant_b_views
            metric_name = "views"

        # Calculate statistical significance
        stats = self._calculate_significance(metric_a, metric_b, test.sample_size or 1000)

        results = {
            "test_id": str(test_id),
            "test_name": test.test_name,
            "metric": test.test_metric.value,
            "variants": {
                "A": {
                    "video_id": str(test.variant_a_video_id),
                    "metric_value": metric_a,
                    "sample_size": variant_a_views,
                },
                "B": {
                    "video_id": str(test.variant_b_video_id),
                    "metric_value": metric_b,
                    "sample_size": variant_b_views,
                }
            },
            "statistics": stats,
            "winner": stats.get("winner"),
            "confidence_level": stats.get("confidence_level"),
            "is_significant": stats.get("is_significant", False),
        }

        return results

    async def check_test_completion(self, test_id: UUID) -> bool:
        """
        Check if an A/B test has reached its sample size and can be completed.

        Args:
            test_id: A/B test ID

        Returns:
            True if test should be completed
        """
        test = await self.ab_test_repo.get_by_id(test_id)
        if not test or test.status != "running":
            return False

        if not test.sample_size:
            return False

        # Check if both variants have reached sample size
        variant_a_views = await self.analytics_repo.get_total_views(test.variant_a_video_id)
        variant_b_views = await self.analytics_repo.get_total_views(test.variant_b_video_id)

        min_views = min(variant_a_views, variant_b_views)
        return min_views >= test.sample_size

    async def complete_test_if_ready(self, test_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Complete an A/B test if it has reached its sample size.

        Args:
            test_id: A/B test ID

        Returns:
            Test results if completed, None otherwise
        """
        if await self.check_test_completion(test_id):
            results = await self.get_test_results(test_id)
            if results:
                test = await self.ab_test_repo.get_by_id(test_id)
                await test.mark_completed(results)
                await self.ab_test_repo.update(test)
                logger.info(f"Completed A/B test {test_id} with winner: {results.get('winner')}")
                return results

        return None

    def _calculate_significance(self, metric_a: float, metric_b: float,
                              sample_size: int) -> Dict[str, Any]:
        """
        Calculate statistical significance between two variants.

        Uses a simplified statistical test (could be enhanced with proper A/B testing libraries).

        Args:
            metric_a: Metric value for variant A
            metric_b: Metric value for variant B
            sample_size: Target sample size

        Returns:
            Dictionary with statistical results
        """
        # Simple proportion test approximation
        # In a real implementation, use scipy.stats or similar

        if metric_a == 0 and metric_b == 0:
            return {
                "winner": None,
                "confidence_level": 0.0,
                "is_significant": False,
                "p_value": 1.0,
            }

        # Calculate relative improvement
        if metric_a > 0:
            relative_improvement = (metric_b - metric_a) / metric_a
        else:
            relative_improvement = 1.0 if metric_b > 0 else 0.0

        # Determine winner
        if metric_b > metric_a:
            winner = "B"
            improvement = relative_improvement
        elif metric_a > metric_b:
            winner = "A"
            improvement = -relative_improvement
        else:
            winner = None
            improvement = 0.0

        # Simplified significance calculation
        # This is a rough approximation - real A/B testing uses proper statistical methods
        total_metric = metric_a + metric_b
        if total_metric > 0:
            # Use sample size to estimate confidence
            effective_sample = min(sample_size, int(total_metric))
            confidence_level = min(0.95, effective_sample / sample_size) if sample_size > 0 else 0.0

            # Consider significant if confidence > 80% and improvement > 5%
            is_significant = confidence_level > 0.8 and abs(improvement) > 0.05
        else:
            confidence_level = 0.0
            is_significant = False

        return {
            "winner": winner,
            "improvement": improvement,
            "confidence_level": confidence_level,
            "is_significant": is_significant,
            "p_value": 1.0 - confidence_level,  # Simplified
        }

    async def get_active_tests_for_video(self, video_id: VideoId) -> List[ABTest]:
        """
        Get all active A/B tests that include a specific video.

        Args:
            video_id: Video ID

        Returns:
            List of active A/B tests
        """
        tests = await self.ab_test_repo.get_tests_by_video(video_id)
        return [test for test in tests if test.is_active]

    async def get_recommended_video(self, video_ids: List[VideoId],
                                  user_id: Optional[str] = None) -> Optional[VideoId]:
        """
        Get the recommended video from a list, considering A/B test results.

        Args:
            video_ids: List of video IDs to choose from
            user_id: User ID for consistent selection

        Returns:
            Recommended video ID, or None if no clear winner
        """
        # Check for active A/B tests involving these videos
        active_tests = []
        for video_id in video_ids:
            tests = await self.get_active_tests_for_video(video_id)
            active_tests.extend(tests)

        # If there are active tests, use test selection
        for test in active_tests:
            if test.variant_a_video_id in video_ids and test.variant_b_video_id in video_ids:
                selected = await self.select_video_variant(test.id, user_id)
                if selected:
                    return selected

        # No active tests, check for completed tests to use winners
        for video_id in video_ids:
            tests = await self.ab_test_repo.get_tests_by_video(video_id)
            for test in tests:
                if test.status == "completed" and test.results:
                    winner_variant = test.results.get("winner")
                    if winner_variant == "A" and test.variant_a_video_id == video_id:
                        return video_id
                    elif winner_variant == "B" and test.variant_b_video_id == video_id:
                        return video_id

        # No test results, return first video
        return video_ids[0] if video_ids else None