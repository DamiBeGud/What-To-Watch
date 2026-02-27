from __future__ import annotations

import unittest

from src.domain.enums import RecommendationMode
from src.domain.requests import RecommendationFilters, RecommendationRequest
from tests._helpers import build_dependencies_or_skip


class RecommendationPipelineContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dependencies = build_dependencies_or_skip(self)
        self.service = self.dependencies.service_bundle.recommendation_service

    def test_returning_user_request_response_contract(self) -> None:
        request = RecommendationRequest(
            mode=RecommendationMode.RETURNING_USER,
            top_n=8,
            filters=RecommendationFilters(genres=(), year_min=None, year_max=None),
            user_id=711,
        )
        response = self.service.recommend(request)

        self.assertTrue(response.ok)
        self.assertLessEqual(len(response.items), 8)
        self.assertIsNotNone(response.mode_used)
        self.assertIn("timings_ms", response.debug)
        self.assertIn("effective_limits", response.debug)

    def test_new_user_weak_signal_fallback_contract(self) -> None:
        request = RecommendationRequest(
            mode=RecommendationMode.NEW_USER,
            top_n=6,
            filters=RecommendationFilters(genres=(), year_min=None, year_max=None),
            liked_movie_ids=(),
            genre_preferences=(),
        )
        response = self.service.recommend(request)

        self.assertTrue(response.ok)
        self.assertTrue(response.fallback_used)
        self.assertLessEqual(len(response.items), 6)
        self.assertIn("route", response.debug)
        self.assertIn("timings_ms", response.debug)

    def test_similar_movie_contract_contains_scan_and_timing_details(self) -> None:
        request = RecommendationRequest(
            mode=RecommendationMode.SIMILAR_MOVIE,
            top_n=7,
            filters=RecommendationFilters(genres=(), year_min=None, year_max=None),
            source_movie_id=1,
        )
        response = self.service.recommend(request)

        self.assertTrue(response.ok)
        self.assertLessEqual(len(response.items), 7)
        self.assertIn("timings_ms", response.debug)
        self.assertIn("similarity_scan", response.debug)
        self.assertIn("candidate_limit", response.debug)


if __name__ == "__main__":
    unittest.main()

