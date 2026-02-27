from __future__ import annotations

import unittest

from src.application.services.filter_service import FilterService
from src.domain.requests import RecommendationFilters
from src.domain.responses import RecommendationItem


def _item(movie_id: int, year: int | None, genres: str) -> RecommendationItem:
    return RecommendationItem(
        movie_id=movie_id,
        title=f"Movie {movie_id}",
        year=year,
        genres=genres,
        score=1.0,
        reason="reason",
        source_label="source",
    )


class FilterServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = FilterService()

    def test_empty_items_returns_noop(self) -> None:
        result = self.service.apply_shared_filters(
            items=(),
            filters=RecommendationFilters(genres=("Action",), year_min=2000, year_max=2010),
        )
        self.assertEqual(result.items, ())
        self.assertEqual(result.relaxation_steps, ("noop_empty",))
        self.assertFalse(result.relaxation_applied)

    def test_strict_filter_keeps_matching_items(self) -> None:
        items = (
            _item(1, 1999, "Action|Sci-Fi"),
            _item(2, 2005, "Drama"),
        )
        result = self.service.apply_shared_filters(
            items=items,
            filters=RecommendationFilters(genres=("Action",), year_min=1995, year_max=2001),
        )
        self.assertEqual([i.movie_id for i in result.items], [1])
        self.assertEqual(result.relaxation_steps, ("strict",))
        self.assertEqual(result.warnings, ())

    def test_relaxes_years_when_genre_matches_but_year_range_is_too_strict(self) -> None:
        items = (
            _item(1, 1999, "Action|Sci-Fi"),
            _item(2, 2001, "Action|Drama"),
        )
        result = self.service.apply_shared_filters(
            items=items,
            filters=RecommendationFilters(genres=("Action",), year_min=2020, year_max=2021),
        )
        self.assertEqual([i.movie_id for i in result.items], [1, 2])
        self.assertTrue(result.relaxation_applied)
        self.assertEqual(result.relaxation_steps, ("strict", "relax_years"))
        self.assertEqual(len(result.warnings), 1)

    def test_relaxes_genres_when_no_items_match_selected_genres(self) -> None:
        items = (
            _item(1, 2001, "Comedy"),
            _item(2, 2003, "Drama"),
        )
        result = self.service.apply_shared_filters(
            items=items,
            filters=RecommendationFilters(genres=("Horror",), year_min=2000, year_max=2005),
        )
        self.assertEqual([i.movie_id for i in result.items], [1, 2])
        self.assertTrue(result.relaxation_applied)
        self.assertEqual(result.relaxation_steps, ("strict", "relax_years", "relax_genres"))
        self.assertEqual(len(result.warnings), 1)


if __name__ == "__main__":
    unittest.main()

