from __future__ import annotations

import unittest

from src.infrastructure.loaders.startup_validator import validate_startup_artifacts
from tests._helpers import build_dependencies_or_skip


class StartupValidArtifactsSmokeTests(unittest.TestCase):
    def test_startup_validation_and_dependency_wiring_succeeds(self) -> None:
        report = validate_startup_artifacts("artifacts", require_user_profiles=True)
        self.assertGreaterEqual(len(report.notes), 1)
        self.assertIsNotNone(report.detected_user_profiles_artifact)

        dependencies = build_dependencies_or_skip(self)
        status = dependencies.serving_api.get_app_status()
        self.assertTrue(status.get("startup_ready"))
        self.assertIsInstance(status.get("startup_timing_ms"), dict)
        self.assertIn("total_startup_ms", status.get("startup_timing_ms") or {})


if __name__ == "__main__":
    unittest.main()

