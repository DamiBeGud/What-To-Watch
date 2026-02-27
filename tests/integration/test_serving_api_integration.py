from __future__ import annotations

import unittest

from tests._helpers import build_dependencies_or_skip


class ServingAPIIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dependencies = build_dependencies_or_skip(self)
        self.api = self.dependencies.serving_api

    def test_public_interface_methods_are_available(self) -> None:
        self.assertTrue(callable(self.api.get_app_status))
        self.assertTrue(callable(self.api.get_ui_options))
        self.assertTrue(callable(self.api.search_titles))
        self.assertTrue(callable(self.api.recommend))

    def test_search_titles_returns_ui_ready_rows(self) -> None:
        rows = self.api.search_titles("Toy Story", limit=5)
        self.assertGreater(len(rows), 0)
        first = rows[0]
        self.assertIn("movieId", first)
        self.assertIn("title", first)

    def test_recommend_contract_for_all_modes(self) -> None:
        requests = [
            {
                "mode": "returning_user",
                "top_n": 5,
                "filters": {"genres": [], "year_range": []},
                "user_id": 711,
            },
            {
                "mode": "new_user",
                "top_n": 5,
                "filters": {"genres": [], "year_range": []},
                "liked_movie_ids": [],
                "genre_preferences": [],
            },
            {
                "mode": "similar_movie",
                "top_n": 5,
                "filters": {"genres": [], "year_range": []},
                "source_movie_id": None,
            },
        ]

        required_keys = {
            "ok",
            "mode_used",
            "fallback_used",
            "status_message",
            "warnings",
            "items",
            "debug",
        }

        for request in requests:
            with self.subTest(mode=request["mode"]):
                response = self.api.recommend(request)
                self.assertTrue(required_keys.issubset(set(response.keys())))
                self.assertIsInstance(response.get("warnings"), list)
                self.assertIsInstance(response.get("items"), list)

                debug = response.get("debug") or {}
                self.assertIn("timings_ms", debug)
                self.assertIn(
                    True,
                    [
                        isinstance(debug.get("effective_limits"), dict),
                        isinstance(debug.get("performance_limits"), dict),
                    ],
                )


if __name__ == "__main__":
    unittest.main()

