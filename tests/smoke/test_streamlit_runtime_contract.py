from __future__ import annotations

import unittest

from tests._helpers import build_dependencies_or_skip


class StreamlitRuntimeContractSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dependencies = build_dependencies_or_skip(self)
        self.api = self.dependencies.serving_api

    def test_status_ui_options_and_recommend_contract_are_stable(self) -> None:
        status = self.api.get_app_status()
        self.assertTrue(status.get("startup_ready"))
        self.assertIn("startup_timing_ms", status)
        self.assertIn("artifacts_summary", status)

        options = self.api.get_ui_options()
        self.assertEqual(
            options.get("available_modes"),
            ["returning_user", "new_user", "similar_movie"],
        )

        source_rows = self.api.search_titles("Toy Story", limit=3)
        source_movie_id = source_rows[0].get("movieId") if source_rows else None

        payload = {
            "mode": "similar_movie",
            "top_n": 7,
            "filters": {"genres": [], "year_range": []},
            "source_movie_id": source_movie_id,
        }
        response = self.api.recommend(payload)
        self.assertIn("ok", response)
        self.assertIn("items", response)
        self.assertIn("debug", response)

        debug = response.get("debug") or {}
        self.assertIn("timings_ms", debug)
        self.assertIn(
            True,
            [
                isinstance(debug.get("effective_limits"), dict),
                isinstance(debug.get("performance_limits"), dict),
            ],
        )
        if not response.get("fallback_used"):
            self.assertIn("similarity_scan", debug)


if __name__ == "__main__":
    unittest.main()

