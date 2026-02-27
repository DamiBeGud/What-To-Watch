from __future__ import annotations

import unittest

from src.infrastructure.loaders.artifact_loader import load_runtime_artifacts
from src.infrastructure.repositories import build_artifact_repository_bundle
from tests._helpers import ensure_runtime_dependencies_or_skip


class RepositoryBundleIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        ensure_runtime_dependencies_or_skip(self)

    def test_load_runtime_artifacts_and_build_repository_bundle(self) -> None:
        runtime_artifacts = load_runtime_artifacts("artifacts")
        bundle = build_artifact_repository_bundle(
            runtime_artifacts,
            artifacts_dir="artifacts",
        )

        self.assertGreater(bundle.movie_metadata.count_movies(), 0)
        self.assertGreater(bundle.global_popularity.count_rows(), 0)
        self.assertGreater(bundle.genre_popularity.count_rows(), 0)
        self.assertGreaterEqual(bundle.user_profiles.count_profiles(), 1)

        similarity_summary = bundle.similarity.get_summary()
        self.assertTrue(similarity_summary.has_content_assets)
        self.assertTrue(similarity_summary.has_collaborative_assets)
        self.assertGreater(similarity_summary.content_movie_count, 0)
        self.assertGreater(similarity_summary.collaborative_item_count, 0)


if __name__ == "__main__":
    unittest.main()

