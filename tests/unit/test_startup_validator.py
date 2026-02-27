from __future__ import annotations

import unittest
from pathlib import Path

from src.infrastructure.loaders.startup_validator import StartupValidationError, validate_startup_artifacts
from tests._helpers import temporary_artifacts_copy


class StartupValidatorTests(unittest.TestCase):
    def test_validates_current_artifact_bundle(self) -> None:
        report = validate_startup_artifacts("artifacts", require_user_profiles=True)
        self.assertIn("artifacts", report.artifacts_dir)
        self.assertIsNotNone(report.detected_user_profiles_artifact)

    def test_missing_manifest_raises_actionable_error(self) -> None:
        with temporary_artifacts_copy() as copied_artifacts:
            manifest_path = copied_artifacts / "aaa_artifact_manifest.json"
            manifest_path.unlink()

            with self.assertRaises(StartupValidationError) as ctx:
                validate_startup_artifacts(copied_artifacts, require_user_profiles=True)

            message = str(ctx.exception)
            self.assertIn("Missing required artifact manifest file", message)
            self.assertIn("artifact_exporter", message)

    def test_metadata_schema_mismatch_is_reported_clearly(self) -> None:
        with temporary_artifacts_copy() as copied_artifacts:
            metadata_path = copied_artifacts / "movie_metadata.csv"
            lines = metadata_path.read_text(encoding="utf-8").splitlines()
            self.assertGreater(len(lines), 1)
            lines[0] = "movieId,year,genres"
            metadata_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            with self.assertRaises(StartupValidationError) as ctx:
                validate_startup_artifacts(copied_artifacts, require_user_profiles=True)

            message = str(ctx.exception)
            self.assertIn("Metadata column mismatch", message)
            self.assertIn("missing ['title']", message)


if __name__ == "__main__":
    unittest.main()

