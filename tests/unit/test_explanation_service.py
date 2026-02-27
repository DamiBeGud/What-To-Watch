from __future__ import annotations

import unittest

from src.application.services.explanation_service import ExplanationService
from src.domain.enums import FallbackReason


class ExplanationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ExplanationService()

    def test_global_popularity_reason_includes_context(self) -> None:
        reason = self.service.global_popularity_reason(
            scenario="new_user_fallback",
            rating_count=12345,
        )
        self.assertIn("cold-start fallback", reason)
        self.assertIn("12345", reason)

    def test_similar_movie_reason_mentions_source_and_overlap(self) -> None:
        reason = self.service.similar_movie_reason(
            source_title="Toy Story (1995)",
            overlap_genres=["Adventure", "Comedy"],
        )
        self.assertIn("Toy Story", reason)
        self.assertIn("Adventure", reason)

    def test_new_user_status_changes_when_fallback_used(self) -> None:
        normal = self.service.new_user_status(fallback_used=False)
        fallback = self.service.new_user_status(fallback_used=True)
        self.assertIn("genre-aware popularity", normal)
        self.assertIn("fallback", fallback.lower())

    def test_similar_movie_status_uses_fallback_specific_message(self) -> None:
        missing_source = self.service.similar_movie_status(
            source_title=None,
            fallback_reason=FallbackReason.MISSING_SOURCE_MOVIE,
        )
        missing_genres = self.service.similar_movie_status(
            source_title="Some Movie",
            fallback_reason=FallbackReason.MISSING_SOURCE_GENRES,
        )
        self.assertIn("select a title", missing_source.lower())
        self.assertIn("metadata", missing_genres.lower())

    def test_weak_signal_warning_differs_for_empty_vs_non_empty_preferences(self) -> None:
        no_prefs = self.service.warning_new_user_weak_signal(has_any_preferences=False)
        weak_prefs = self.service.warning_new_user_weak_signal(has_any_preferences=True)
        self.assertIn("Not enough preferences", no_prefs)
        self.assertIn("did not yield enough", weak_prefs)


if __name__ == "__main__":
    unittest.main()

