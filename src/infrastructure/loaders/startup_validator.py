from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Union

from .artifact_loader import (
    A_PHASE_ARTIFACT_MANIFEST_TEMPLATE,
    PROVENANCE_FILENAME,
    REFERENCE_SELECTED_V1_PARAMS,
    USER_PROFILE_ARTIFACT_CANDIDATES,
    USER_PROFILE_SCHEMA_DOC_FILENAME,
    ArtifactLoadError,
    ArtifactValidationError,
    load_artifact_manifest,
    load_selected_params,
    read_csv_header,
    read_json_file,
    read_jsonl_first_record,
    read_npy_header,
    read_npz_headers,
    resolve_user_profiles_artifact,
)


class StartupValidationError(ArtifactValidationError):
    """Raised when startup validation fails for the serving artifact bundle."""


@dataclass
class StartupValidationReport:
    artifacts_dir: str
    validated_at_utc: str
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    detected_user_profiles_artifact: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifacts_dir": self.artifacts_dir,
            "validated_at_utc": self.validated_at_utc,
            "warnings": self.warnings,
            "notes": self.notes,
            "detected_user_profiles_artifact": self.detected_user_profiles_artifact,
        }


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class StartupArtifactValidator:
    """Validates serving artifact presence and basic compatibility at app startup."""

    _required_manifest_entry_keys = {"artifact_name", "path", "format", "source", "purpose"}
    _required_metadata_columns = {"movieId", "title", "genres"}
    _optional_metadata_columns = {"year"}
    _required_global_pop_columns = {"movieId", "rating_count", "mean_rating", "pop_weighted_rating", "pop_score"}
    _required_genre_pop_columns = {"genre", "movieId", "rating_count", "mean_rating", "genre_pop_score"}
    _required_selected_param_keys = set(REFERENCE_SELECTED_V1_PARAMS.keys())
    _required_user_profile_keys = {
        "userId",
        "train_interaction_count",
        "positive_interaction_count",
        "train_mean_rating",
        "seen_movie_ids",
        "positive_seed_movie_ids",
        "preferred_genres",
    }
    _export_rerun_command = "python3 -m src.infrastructure.loaders.artifact_exporter --artifacts-dir artifacts"

    def __init__(self, artifacts_dir: Union[str, Path] = "artifacts", *, require_user_profiles: bool = True) -> None:
        self.artifacts_dir = Path(artifacts_dir)
        self.require_user_profiles = require_user_profiles
        self._errors: list[str] = []
        self._warnings: list[str] = []
        self._notes: list[str] = []

    def validate(self) -> StartupValidationReport:
        self._errors.clear()
        self._warnings.clear()
        self._notes.clear()

        if not self.artifacts_dir.exists():
            self._error(
                f"Missing artifacts directory: {self.artifacts_dir}",
                expected="directory exists",
                next_step=f"Create/export artifacts into {self.artifacts_dir} (rerun: {self._export_rerun_command}).",
            )
            self._raise_if_errors()

        if not self.artifacts_dir.is_dir():
            self._error(
                f"Invalid artifacts path: {self.artifacts_dir}",
                expected="directory",
                next_step=f"Point startup config to the artifact folder and rerun validation. Expected folder: {self.artifacts_dir}.",
            )
            self._raise_if_errors()

        manifest = self._validate_manifest()
        self._validate_selected_params()
        if manifest is None:
            self._validate_core_file_presence_fallback()

        # Schema/shape checks run only if the relevant files exist.
        self._validate_movie_metadata_schema()
        self._validate_popularity_schemas()
        self._validate_genre_feature_assets()
        self._validate_cf_similarity_assets()
        user_profiles_path = self._validate_user_profiles_artifact()
        self._validate_provenance_file()

        self._raise_if_errors()

        return StartupValidationReport(
            artifacts_dir=str(self.artifacts_dir.resolve()),
            validated_at_utc=_utc_now_iso(),
            warnings=list(self._warnings),
            notes=list(self._notes),
            detected_user_profiles_artifact=str(user_profiles_path) if user_profiles_path else None,
        )

    def _error(
        self,
        message: str,
        *,
        expected: Optional[str] = None,
        next_step: Optional[str] = None,
    ) -> None:
        parts = [message]
        if expected:
            parts.append(f"Expected: {expected}.")
        if next_step:
            parts.append(f"Next step: {next_step}")
        self._errors.append(" ".join(parts))

    def _warn(self, message: str) -> None:
        self._warnings.append(message)

    def _note(self, message: str) -> None:
        self._notes.append(message)

    def _raise_if_errors(self) -> None:
        if not self._errors:
            return
        lines = [
            f"Startup artifact validation failed for {self.artifacts_dir.resolve()}",
            "",
            "Errors:",
        ]
        lines.extend(f"- {msg}" for msg in self._errors)
        if self._warnings:
            lines.append("")
            lines.append("Warnings:")
            lines.extend(f"- {msg}" for msg in self._warnings)
        raise StartupValidationError("\n".join(lines))

    def _validate_manifest(self) -> Optional[list[dict[str, Any]]]:
        manifest_path = self.artifacts_dir / "aaa_artifact_manifest.json"
        if not manifest_path.exists():
            self._error(
                f"Missing required artifact manifest file: {manifest_path}",
                expected="readable JSON list matching A-Phase export entries",
                next_step=f"Rerun the offline artifact export ({self._export_rerun_command}).",
            )
            return None

        try:
            manifest = load_artifact_manifest(self.artifacts_dir)
        except ArtifactLoadError as exc:
            self._error(
                f"Unreadable manifest file: {manifest_path}",
                expected="valid JSON list",
                next_step=f"Fix or regenerate {manifest_path.name} (rerun: {self._export_rerun_command}). {exc}",
            )
            return None

        if len(manifest) < len(A_PHASE_ARTIFACT_MANIFEST_TEMPLATE):
            self._error(
                f"Manifest entry count too small in {manifest_path}",
                expected=f"at least {len(A_PHASE_ARTIFACT_MANIFEST_TEMPLATE)} A-Phase entries",
                next_step="Regenerate the manifest from the A-Phase export plan.",
            )

        manifest_by_name: dict[str, dict[str, Any]] = {}
        for idx, entry in enumerate(manifest):
            if not isinstance(entry, dict):
                self._error(
                    f"Invalid manifest entry #{idx} in {manifest_path}",
                    expected="JSON object with artifact_name/path/format/source/purpose",
                    next_step="Regenerate the manifest file from the A-Phase export step.",
                )
                continue
            missing_keys = self._required_manifest_entry_keys - set(entry.keys())
            if missing_keys:
                self._error(
                    f"Manifest entry #{idx} missing keys in {manifest_path}",
                    expected=f"keys {sorted(self._required_manifest_entry_keys)}; missing {sorted(missing_keys)}",
                    next_step="Regenerate the manifest file from the A-Phase export step.",
                )
                continue
            manifest_by_name[str(entry["artifact_name"])] = entry

        for expected_entry in A_PHASE_ARTIFACT_MANIFEST_TEMPLATE:
            name = expected_entry["artifact_name"]
            actual = manifest_by_name.get(name)
            if actual is None:
                self._error(
                    f"Manifest missing required entry '{name}' in {manifest_path}",
                    expected=f"path={expected_entry['path']}",
                    next_step="Regenerate the manifest from the A-Phase export step.",
                )
                continue

            for field in ("path", "format"):
                expected_value = expected_entry[field]
                actual_value = str(actual.get(field))
                if actual_value != expected_value:
                    self._error(
                        f"Manifest mismatch for entry '{name}' field '{field}' in {manifest_path}",
                        expected=expected_value,
                        next_step="Regenerate the manifest or update the app contract to match the exported bundle.",
                    )

            rel_path = str(actual.get("path", ""))
            expected_file = self._resolve_manifest_path(rel_path)
            if expected_file is None:
                self._error(
                    f"Manifest entry '{name}' has invalid path '{rel_path}'",
                    expected="relative path under artifacts/ (for example 'artifacts/movie_metadata.csv')",
                    next_step="Fix the manifest path or regenerate the artifact bundle.",
                )
                continue
            if not expected_file.exists():
                self._error(
                    f"Missing artifact file referenced by manifest entry '{name}': {expected_file}",
                    expected=f"file exists at {rel_path}",
                    next_step=f"Rerun the offline artifact export ({self._export_rerun_command}).",
                )

        self._note(f"Manifest file is readable: {manifest_path.name}")
        return manifest

    def _resolve_manifest_path(self, manifest_rel_path: str) -> Optional[Path]:
        if not manifest_rel_path:
            return None
        manifest_path = Path(manifest_rel_path)
        if manifest_path.is_absolute():
            return manifest_path
        # Expected format is 'artifacts/<file>' from A-Phase manifest.
        if manifest_path.parts and manifest_path.parts[0] == "artifacts":
            return self.artifacts_dir.parent / manifest_path
        return self.artifacts_dir / manifest_path

    def _validate_selected_params(self) -> Optional[dict[str, Any]]:
        params_path = self.artifacts_dir / "aaa_selected_params.json"
        if not params_path.exists():
            self._error(
                f"Missing required selected-params file: {params_path}",
                expected="JSON object with the selected v1 hybrid parameters",
                next_step=f"Rerun the offline artifact export ({self._export_rerun_command}).",
            )
            return None

        try:
            params = load_selected_params(self.artifacts_dir)
        except ArtifactLoadError as exc:
            self._error(
                f"Unreadable selected-params file: {params_path}",
                expected="valid JSON object",
                next_step=f"Fix or regenerate {params_path.name}. {exc}",
            )
            return None

        missing_keys = self._required_selected_param_keys - set(params.keys())
        if missing_keys:
            self._error(
                f"Selected params missing expected key(s) in {params_path}",
                expected=f"keys include {sorted(self._required_selected_param_keys)}; missing {sorted(missing_keys)}",
                next_step="Regenerate aaa_selected_params.json from the A-Phase/C-Phase selected v1 setup.",
            )

        numeric_checks: dict[str, tuple[Optional[float], Optional[float]]] = {
            "pop_min_count": (1, None),
            "content_profile_min_rating": (0.0, 5.0),
            "cf_top_neighbors": (1, None),
            "hybrid_alpha": (0.0, 1.0),
            "genre_pref_top_n": (1, None),
        }
        for key, (lower, upper) in numeric_checks.items():
            if key not in params:
                continue
            value = params[key]
            if not isinstance(value, (int, float)):
                self._error(
                    f"Selected params key '{key}' has invalid type in {params_path}",
                    expected="numeric value",
                    next_step=f"Fix {params_path.name} or regenerate it from the selected v1 setup.",
                )
                continue
            numeric_value = float(value)
            if lower is not None and numeric_value < lower:
                self._error(
                    f"Selected params key '{key}' is below supported range in {params_path}: {value}",
                    expected=f">= {lower}",
                    next_step="Update the selected params to a supported value or adjust app expectations.",
                )
            if upper is not None and numeric_value > upper:
                self._error(
                    f"Selected params key '{key}' is above supported range in {params_path}: {value}",
                    expected=f"<= {upper}",
                    next_step="Update the selected params to a supported value or adjust app expectations.",
                )

        for key, expected_value in REFERENCE_SELECTED_V1_PARAMS.items():
            if key in params and params[key] != expected_value:
                self._warn(
                    f"Selected params '{key}'={params[key]!r} differs from the documented C-Phase v1 reference value {expected_value!r}."
                )

        self._note(f"Selected params file is readable: {params_path.name}")
        return params

    def _validate_core_file_presence_fallback(self) -> None:
        # If manifest parsing fails, this still gives a clear, direct missing-file list.
        for entry in A_PHASE_ARTIFACT_MANIFEST_TEMPLATE:
            path = self._resolve_manifest_path(entry["path"])
            if path is None:
                continue
            if not path.exists():
                self._error(
                    f"Required artifact file missing: {path}",
                    expected=entry["path"],
                    next_step=f"Rerun the offline artifact export ({self._export_rerun_command}).",
                )

    def _validate_movie_metadata_schema(self) -> None:
        path = self.artifacts_dir / "movie_metadata.csv"
        if not path.exists():
            return
        try:
            columns = set(read_csv_header(path))
        except ArtifactLoadError as exc:
            self._error(
                f"Failed to read metadata schema from {path}",
                expected=f"CSV header including {sorted(self._required_metadata_columns)}",
                next_step=f"Regenerate {path.name}. {exc}",
            )
            return

        missing = self._required_metadata_columns - columns
        if missing:
            self._error(
                f"Metadata column mismatch in {path}",
                expected=f"columns include {sorted(self._required_metadata_columns)}; missing {sorted(missing)}",
                next_step="Regenerate movie_metadata.csv from the A-Phase export path or align the app schema.",
            )
        if "year" not in columns:
            self._warn(
                f"Optional metadata column 'year' is missing in {path}; app should handle year display/filtering gracefully."
            )
        else:
            self._note("Metadata includes optional 'year' column.")

    def _validate_popularity_schemas(self) -> None:
        global_path = self.artifacts_dir / "global_popularity_train.csv"
        if global_path.exists():
            try:
                columns = set(read_csv_header(global_path))
            except ArtifactLoadError as exc:
                self._error(
                    f"Failed to read global popularity schema from {global_path}",
                    expected=f"CSV header including {sorted(self._required_global_pop_columns)}",
                    next_step=f"Regenerate {global_path.name}. {exc}",
                )
            else:
                missing = self._required_global_pop_columns - columns
                if missing:
                    self._error(
                        f"Global popularity schema mismatch in {global_path}",
                        expected=f"columns include {sorted(self._required_global_pop_columns)}; missing {sorted(missing)}",
                        next_step="Regenerate the global popularity artifact from the train split export.",
                    )

        genre_path = self.artifacts_dir / "genre_popularity_train.csv"
        if genre_path.exists():
            try:
                columns = set(read_csv_header(genre_path))
            except ArtifactLoadError as exc:
                self._error(
                    f"Failed to read genre popularity schema from {genre_path}",
                    expected=f"CSV header including {sorted(self._required_genre_pop_columns)}",
                    next_step=f"Regenerate {genre_path.name}. {exc}",
                )
            else:
                missing = self._required_genre_pop_columns - columns
                if missing:
                    self._error(
                        f"Genre popularity schema mismatch in {genre_path}",
                        expected=f"columns include {sorted(self._required_genre_pop_columns)}; missing {sorted(missing)}",
                        next_step="Regenerate the genre popularity artifact from the train split export.",
                    )

    def _validate_genre_feature_assets(self) -> None:
        npz_path = self.artifacts_dir / "genre_features.npz"
        cols_path = self.artifacts_dir / "genre_feature_columns.json"
        if not (npz_path.exists() and cols_path.exists()):
            return

        try:
            headers = read_npz_headers(npz_path)
        except ArtifactLoadError as exc:
            self._error(
                f"Failed to inspect genre feature NPZ {npz_path}",
                expected="NPZ with 'movie_ids' and 'genre_matrix' arrays",
                next_step=f"Regenerate {npz_path.name}. {exc}",
            )
            return

        movie_ids_header = headers.get("movie_ids")
        genre_matrix_header = headers.get("genre_matrix")
        if movie_ids_header is None or genre_matrix_header is None:
            self._error(
                f"Genre feature asset member mismatch in {npz_path}",
                expected="NPZ members 'movie_ids' and 'genre_matrix'",
                next_step="Regenerate the genre feature artifact with the A-Phase export format.",
            )
            return

        if movie_ids_header.ndim != 1:
            self._error(
                f"Genre feature movie_ids shape mismatch in {npz_path}",
                expected="1D array for movie_ids",
                next_step="Regenerate genre_features.npz with the A-Phase export format.",
            )
        if genre_matrix_header.ndim != 2:
            self._error(
                f"Genre feature matrix shape mismatch in {npz_path}",
                expected="2D array for genre_matrix",
                next_step="Regenerate genre_features.npz with the A-Phase export format.",
            )

        if movie_ids_header.ndim == 1 and genre_matrix_header.ndim == 2:
            if movie_ids_header.shape[0] != genre_matrix_header.shape[0]:
                self._error(
                    f"Genre feature asset row mismatch between {npz_path} members",
                    expected=f"movie_ids length == genre_matrix rows (got {movie_ids_header.shape[0]} vs {genre_matrix_header.shape[0]})",
                    next_step="Regenerate genre_features.npz so rows align with movie_ids.",
                )

        try:
            cols = read_json_file(cols_path)
        except ArtifactLoadError as exc:
            self._error(
                f"Failed to read genre feature column list {cols_path}",
                expected="JSON list of genre feature column names",
                next_step=f"Regenerate {cols_path.name}. {exc}",
            )
            return

        if not isinstance(cols, list):
            self._error(
                f"Genre feature columns file has invalid type: {cols_path}",
                expected="JSON list",
                next_step=f"Regenerate {cols_path.name} with the A-Phase export format.",
            )
            return

        if genre_matrix_header.ndim == 2 and len(cols) != genre_matrix_header.shape[1]:
            self._error(
                f"Genre feature column count mismatch between {cols_path} and {npz_path}",
                expected=f"{genre_matrix_header.shape[1]} columns to match genre_matrix.shape[1]",
                next_step="Regenerate genre_feature_columns.json and genre_features.npz together from the same export run.",
            )

        self._note("Genre feature assets have compatible member shapes and feature-column count.")

    def _validate_cf_similarity_assets(self) -> None:
        sim_path = self.artifacts_dir / "cf_item_similarity.npz"
        ids_path = self.artifacts_dir / "cf_item_ids.npy"
        if not (sim_path.exists() and ids_path.exists()):
            return

        try:
            ids_header = read_npy_header(ids_path)
        except ArtifactLoadError as exc:
            self._error(
                f"Failed to inspect collaborative item IDs file {ids_path}",
                expected="1D .npy array of movieId values",
                next_step=f"Regenerate {ids_path.name}. {exc}",
            )
            return

        try:
            sim_headers = read_npz_headers(sim_path)
        except ArtifactLoadError as exc:
            self._error(
                f"Failed to inspect collaborative similarity file {sim_path}",
                expected="NPZ with 'similarity' member",
                next_step=f"Regenerate {sim_path.name}. {exc}",
            )
            return

        similarity_header = sim_headers.get("similarity")
        if similarity_header is None:
            self._error(
                f"Collaborative similarity asset member mismatch in {sim_path}",
                expected="NPZ member 'similarity'",
                next_step="Regenerate the CF similarity asset with the A-Phase export format.",
            )
            return

        if ids_header.ndim != 1:
            self._error(
                f"Collaborative item IDs shape mismatch in {ids_path}",
                expected="1D array",
                next_step="Regenerate cf_item_ids.npy.",
            )

        if similarity_header.ndim != 2:
            self._error(
                f"Collaborative similarity shape mismatch in {sim_path}",
                expected="2D square matrix",
                next_step="Regenerate cf_item_similarity.npz.",
            )
            return

        rows, cols = similarity_header.shape
        if rows != cols:
            self._error(
                f"Collaborative similarity matrix is not square in {sim_path}",
                expected=f"shape (n, n); got {similarity_header.shape}",
                next_step="Regenerate cf_item_similarity.npz and cf_item_ids.npy from the same export run.",
            )

        if ids_header.ndim == 1 and ids_header.shape and rows != ids_header.shape[0]:
            self._error(
                f"Collaborative shape compatibility mismatch between {sim_path} and {ids_path}",
                expected=f"similarity rows/cols == len(cf_item_ids) (got {rows} vs {ids_header.shape[0]})",
                next_step="Regenerate cf_item_similarity.npz and cf_item_ids.npy together from the same export run.",
            )

        self._note("Collaborative similarity assets have compatible shapes.")

    def _validate_user_profiles_artifact(self) -> Optional[Path]:
        path = resolve_user_profiles_artifact(self.artifacts_dir)
        if path is None:
            if self.require_user_profiles:
                choices = ", ".join(str(self.artifacts_dir / name) for name in USER_PROFILE_ARTIFACT_CANDIDATES)
                self._error(
                    "Missing returning-user support artifact (user profiles)",
                    expected=f"one of: {choices}",
                    next_step=(
                        "Export a compact train user-profile artifact for personalized mode. "
                        f"Rerun: {self._export_rerun_command}"
                    ),
                )
            return None

        schema_doc_path = self.artifacts_dir / USER_PROFILE_SCHEMA_DOC_FILENAME
        if not schema_doc_path.exists():
            self._warn(
                f"User profile schema doc is missing: {schema_doc_path}. Add it so personalized-mode assumptions stay explicit."
            )
        else:
            try:
                schema_doc = read_json_file(schema_doc_path)
            except ArtifactLoadError as exc:
                self._error(
                    f"Unreadable user profile schema doc: {schema_doc_path}",
                    expected="valid JSON schema/contract document",
                    next_step=f"Fix or regenerate {schema_doc_path.name}. {exc}",
                )
                schema_doc = None
            if isinstance(schema_doc, dict):
                doc_artifact_path = schema_doc.get("artifact_path")
                if isinstance(doc_artifact_path, str) and Path(doc_artifact_path).name != path.name:
                    self._warn(
                        f"User profile schema doc artifact_path={doc_artifact_path!r} does not match detected file {path.name!r}."
                    )

        suffix = path.suffix.lower()
        if suffix == ".jsonl":
            try:
                first_record = read_jsonl_first_record(path)
            except ArtifactLoadError as exc:
                self._error(
                    f"Failed to read user profile artifact {path}",
                    expected="JSONL with one object per user profile row",
                    next_step=f"Regenerate {path.name}. {exc}",
                )
                return path

            if first_record is None:
                self._error(
                    f"User profile artifact is empty: {path}",
                    expected="at least one user profile record",
                    next_step="Regenerate the user profile export from the AAA train split.",
                )
                return path

            missing = self._required_user_profile_keys - set(first_record.keys())
            if missing:
                self._error(
                    f"User profile schema mismatch in {path}",
                    expected=f"keys include {sorted(self._required_user_profile_keys)}; missing {sorted(missing)}",
                    next_step="Regenerate user_profiles_train with the documented schema for personalized mode.",
                )
                return path

            list_fields = ("seen_movie_ids", "positive_seed_movie_ids", "preferred_genres")
            for key in list_fields:
                if key in first_record and not isinstance(first_record[key], list):
                    self._error(
                        f"User profile field '{key}' has invalid type in {path}",
                        expected="JSON array",
                        next_step="Regenerate user_profiles_train.jsonl with list-valued fields for app runtime parsing.",
                    )

        elif suffix == ".csv":
            try:
                columns = set(read_csv_header(path))
            except ArtifactLoadError as exc:
                self._error(
                    f"Failed to read user profile CSV header from {path}",
                    expected=f"CSV header including {sorted(self._required_user_profile_keys)}",
                    next_step=f"Regenerate {path.name}. {exc}",
                )
                return path
            missing = self._required_user_profile_keys - columns
            if missing:
                self._error(
                    f"User profile CSV schema mismatch in {path}",
                    expected=f"columns include {sorted(self._required_user_profile_keys)}; missing {sorted(missing)}",
                    next_step="Regenerate user_profiles_train.csv with the documented schema.",
                )

        elif suffix == ".parquet":
            # Parquet schema validation requires pandas/pyarrow (or equivalent).
            try:
                import pandas as pd  # type: ignore
            except ModuleNotFoundError as exc:
                self._error(
                    f"Cannot validate parquet user profile schema for {path}: missing dependency 'pandas' (and parquet engine)",
                    expected=f"parquet columns include {sorted(self._required_user_profile_keys)}",
                    next_step="Install pandas + pyarrow, then rerun startup validation.",
                )
                return path
            try:
                cols = set(pd.read_parquet(path).columns.tolist())
            except Exception as exc:
                self._error(
                    f"Failed to read parquet user profile schema from {path}: {type(exc).__name__}: {exc}",
                    expected=f"parquet columns include {sorted(self._required_user_profile_keys)}",
                    next_step=f"Regenerate {path.name} or fix parquet dependencies.",
                )
                return path
            missing = self._required_user_profile_keys - cols
            if missing:
                self._error(
                    f"User profile parquet schema mismatch in {path}",
                    expected=f"columns include {sorted(self._required_user_profile_keys)}; missing {sorted(missing)}",
                    next_step="Regenerate user_profiles_train.parquet with the documented schema.",
                )
        else:
            self._error(
                f"Unsupported user profile artifact format: {path}",
                expected=f"one of extensions {', '.join(Path(n).suffix for n in USER_PROFILE_ARTIFACT_CANDIDATES)}",
                next_step="Export user profiles as .jsonl, .csv, or .parquet and rerun validation.",
            )

        self._note(f"User profile artifact detected: {path.name}")
        return path

    def _validate_provenance_file(self) -> None:
        path = self.artifacts_dir / PROVENANCE_FILENAME
        if not path.exists():
            self._warn(
                f"Provenance file not found ({path.name}). Add it to record the A-Phase config/run assumptions and sampled-vs-full notes."
            )
            return

        try:
            payload = read_json_file(path)
        except ArtifactLoadError as exc:
            self._warn(f"Provenance file exists but is unreadable ({path.name}): {exc}")
            return

        if not isinstance(payload, dict):
            self._warn(f"Provenance file {path.name} should be a JSON object, got {type(payload).__name__}.")
            return

        for key in ("source_notebook", "selected_params_path", "a_phase_config", "sampling_assumption"):
            if key not in payload:
                self._warn(f"Provenance file {path.name} is missing recommended key '{key}'.")
        self._note(f"Provenance file is readable: {path.name}")


def validate_startup_artifacts(
    artifacts_dir: Union[str, Path] = "artifacts", *, require_user_profiles: bool = True
) -> StartupValidationReport:
    validator = StartupArtifactValidator(artifacts_dir, require_user_profiles=require_user_profiles)
    return validator.validate()


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Streamlit serving artifacts at startup.")
    parser.add_argument("--artifacts-dir", default="artifacts", help="Path to the artifact directory (default: artifacts)")
    parser.add_argument(
        "--allow-missing-user-profiles",
        action="store_true",
        help="Do not fail validation if no user_profiles_train artifact is present.",
    )
    parser.add_argument("--json", action="store_true", help="Print the success report as JSON.")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        report = validate_startup_artifacts(
            args.artifacts_dir,
            require_user_profiles=not args.allow_missing_user_profiles,
        )
    except StartupValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"Startup artifact validation passed: {report.artifacts_dir}")
        if report.detected_user_profiles_artifact:
            print(f"- user profiles: {report.detected_user_profiles_artifact}")
        for note in report.notes:
            print(f"- note: {note}")
        for warning in report.warnings:
            print(f"- warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
