from __future__ import annotations

import unittest

from src.application.services.routing_service import RoutingService
from src.domain.enums import FallbackReason, RecommendationExecutionMode, RecommendationMode


class RoutingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = RoutingService()

    def test_returning_user_uses_primary_mode_when_profile_signal_is_strong(self) -> None:
        decision = self.service.route_returning_user(
            user_id=711,
            has_profile=True,
            has_preferred_genres=True,
            has_genre_candidates=True,
        )
        self.assertEqual(decision.mode_requested, RecommendationMode.RETURNING_USER)
        self.assertEqual(decision.mode_used, RecommendationExecutionMode.RETURNING_USER)
        self.assertFalse(decision.fallback_used)
        self.assertIsNone(decision.fallback_reason)

    def test_returning_user_falls_back_when_profile_is_missing(self) -> None:
        decision = self.service.route_returning_user(
            user_id=999999,
            has_profile=False,
            has_preferred_genres=False,
            has_genre_candidates=False,
        )
        self.assertTrue(decision.fallback_used)
        self.assertEqual(decision.mode_used, RecommendationExecutionMode.COLD_START_FALLBACK)
        self.assertEqual(decision.fallback_reason, FallbackReason.MISSING_OR_WEAK_USER_PROFILE)

    def test_new_user_uses_genre_mode_with_effective_candidates(self) -> None:
        decision = self.service.route_new_user(
            has_selected_genres=True,
            has_liked_movies=True,
            has_effective_genres=True,
            has_genre_candidates=True,
        )
        self.assertEqual(decision.mode_used, RecommendationExecutionMode.NEW_USER)
        self.assertFalse(decision.fallback_used)

    def test_new_user_falls_back_when_preference_signal_is_weak(self) -> None:
        decision = self.service.route_new_user(
            has_selected_genres=False,
            has_liked_movies=False,
            has_effective_genres=False,
            has_genre_candidates=False,
        )
        self.assertTrue(decision.fallback_used)
        self.assertEqual(decision.mode_used, RecommendationExecutionMode.COLD_START_FALLBACK)
        self.assertEqual(decision.fallback_reason, FallbackReason.INSUFFICIENT_PREFERENCE_SIGNAL)

    def test_similar_movie_falls_back_when_source_is_missing(self) -> None:
        decision = self.service.route_similar_movie(
            source_movie_id=None,
            source_exists=False,
            has_source_genres=False,
        )
        self.assertTrue(decision.fallback_used)
        self.assertEqual(decision.mode_used, RecommendationExecutionMode.SIMILAR_MOVIE)
        self.assertEqual(decision.fallback_reason, FallbackReason.MISSING_SOURCE_MOVIE)

    def test_similar_movie_uses_primary_route_with_valid_source(self) -> None:
        decision = self.service.route_similar_movie(
            source_movie_id=1,
            source_exists=True,
            has_source_genres=True,
        )
        self.assertFalse(decision.fallback_used)
        self.assertIsNone(decision.fallback_reason)
        self.assertEqual(decision.mode_used, RecommendationExecutionMode.SIMILAR_MOVIE)


if __name__ == "__main__":
    unittest.main()

