from __future__ import annotations

import unittest

from src.core.config import AppConfig
from src.core.dependencies import initialize_app_dependencies
from src.infrastructure.loaders.startup_validator import StartupValidationError, validate_startup_artifacts
from tests._helpers import temporary_artifacts_copy


class StartupMissingArtifactSmokeTests(unittest.TestCase):
    def test_missing_required_artifact_fails_with_actionable_message(self) -> None:
        with temporary_artifacts_copy() as copied_artifacts:
            missing_path = copied_artifacts / "cf_item_ids.npy"
            missing_path.unlink()

            with self.assertRaises(StartupValidationError) as ctx:
                validate_startup_artifacts(copied_artifacts, require_user_profiles=True)
            error_text = str(ctx.exception)
            self.assertIn("collaborative_item_ids", error_text)
            self.assertIn("artifact_exporter", error_text)

            dependencies = initialize_app_dependencies(
                AppConfig(
                    artifacts_dir=str(copied_artifacts),
                    require_user_profiles=True,
                )
            )
            self.assertFalse(dependencies.startup_ready)
            self.assertIsNotNone(dependencies.setup_user_message)
            self.assertIn("Setup issue", dependencies.setup_user_message or "")


if __name__ == "__main__":
    unittest.main()

