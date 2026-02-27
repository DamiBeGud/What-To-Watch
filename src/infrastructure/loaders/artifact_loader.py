from __future__ import annotations

import ast
import csv
import json
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union


class ArtifactError(Exception):
    """Base exception for artifact loading/validation failures."""


class ArtifactLoadError(ArtifactError):
    """Raised when an artifact cannot be loaded or parsed."""


class ArtifactValidationError(ArtifactError):
    """Raised when an artifact fails contract validation."""


@dataclass(frozen=True)
class NpyArrayHeader:
    """Lightweight `.npy` header metadata without loading the array payload."""

    source: str
    version: tuple[int, int]
    descr: str
    fortran_order: bool
    shape: tuple[int, ...]

    @property
    def ndim(self) -> int:
        return len(self.shape)


DEFAULT_ARTIFACTS_DIR = Path("artifacts")

USER_PROFILE_ARTIFACT_CANDIDATES = (
    "user_profiles_train.parquet",
    "user_profiles_train.csv",
    "user_profiles_train.jsonl",
)
RECOMMENDED_USER_PROFILE_ARTIFACT = "user_profiles_train.jsonl"
USER_PROFILE_SCHEMA_DOC_FILENAME = "user_profiles_schema.json"
PROVENANCE_FILENAME = "aaa_export_provenance.json"

REFERENCE_SELECTED_V1_PARAMS: dict[str, Union[int, float]] = {
    # Documented in C-Phase as the selected Streamlit v1 setup.
    "pop_min_count": 20,
    "content_profile_min_rating": 4.0,
    "cf_top_neighbors": 20,
    "hybrid_alpha": 0.8,
    "genre_pref_top_n": 3,
}

A_PHASE_ARTIFACT_MANIFEST_TEMPLATE: list[dict[str, str]] = [
    {
        "artifact_name": "movie_metadata_table",
        "path": "artifacts/movie_metadata.csv",
        "format": "CSV",
        "source": "movies.csv",
        "purpose": "Display titles/years/genres in Streamlit recommendation cards",
    },
    {
        "artifact_name": "global_popularity_table",
        "path": "artifacts/global_popularity_train.csv",
        "format": "CSV",
        "source": "train_ratings_df",
        "purpose": "Global popularity baseline and fallback recommendations",
    },
    {
        "artifact_name": "genre_popularity_table",
        "path": "artifacts/genre_popularity_train.csv",
        "format": "CSV",
        "source": "train_ratings_df + movies.csv",
        "purpose": "Genre-filtered popularity fallback and explanations",
    },
    {
        "artifact_name": "genre_feature_matrix",
        "path": "artifacts/genre_features.npz",
        "format": "NumPy NPZ",
        "source": "movies.csv",
        "purpose": "Content-based scoring and similar-movie recommendations",
    },
    {
        "artifact_name": "genre_feature_columns",
        "path": "artifacts/genre_feature_columns.json",
        "format": "JSON",
        "source": "movies.csv",
        "purpose": "Preserve genre encoder column order",
    },
    {
        "artifact_name": "collaborative_item_similarity",
        "path": "artifacts/cf_item_similarity.npz",
        "format": "NumPy NPZ",
        "source": "train_ratings_df (positive interactions)",
        "purpose": "Item-item collaborative scoring in Streamlit inference path",
    },
    {
        "artifact_name": "collaborative_item_ids",
        "path": "artifacts/cf_item_ids.npy",
        "format": "NumPy NPY",
        "source": "train_ratings_df",
        "purpose": "Map similarity matrix rows/cols to movie IDs",
    },
    {
        "artifact_name": "aaa_model_config",
        "path": "artifacts/aaa_selected_params.json",
        "format": "JSON",
        "source": "A-Phase tuning output",
        "purpose": "Store selected hyperparameters and evaluation settings",
    },
    {
        "artifact_name": "artifact_manifest",
        "path": "artifacts/aaa_artifact_manifest.json",
        "format": "JSON",
        "source": "A-Phase notebook",
        "purpose": "Document artifact paths, purposes, and provenance",
    },
]


def read_json_file(path: Union[str, Path]) -> Any:
    file_path = Path(path)
    if not file_path.exists():
        raise ArtifactLoadError(f"JSON artifact not found: {file_path}")
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(f"Invalid JSON in {file_path}: {exc}") from exc
    except OSError as exc:
        raise ArtifactLoadError(f"Failed to read JSON artifact {file_path}: {exc}") from exc


def write_json_file(path: Union[str, Path], payload: Any, *, indent: int = 2) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, indent=indent), encoding="utf-8")


def load_artifact_manifest(artifacts_dir: Union[str, Path] = DEFAULT_ARTIFACTS_DIR) -> list[dict[str, Any]]:
    manifest_path = Path(artifacts_dir) / "aaa_artifact_manifest.json"
    manifest = read_json_file(manifest_path)
    if not isinstance(manifest, list):
        raise ArtifactLoadError(
            f"Manifest format error in {manifest_path}: expected a JSON list of entries, got {type(manifest).__name__}."
        )
    return manifest


def load_selected_params(artifacts_dir: Union[str, Path] = DEFAULT_ARTIFACTS_DIR) -> dict[str, Any]:
    params_path = Path(artifacts_dir) / "aaa_selected_params.json"
    payload = read_json_file(params_path)
    if not isinstance(payload, dict):
        raise ArtifactLoadError(
            f"Selected params format error in {params_path}: expected a JSON object, got {type(payload).__name__}."
        )
    return payload


def resolve_user_profiles_artifact(artifacts_dir: Union[str, Path] = DEFAULT_ARTIFACTS_DIR) -> Optional[Path]:
    base = Path(artifacts_dir)
    for candidate in USER_PROFILE_ARTIFACT_CANDIDATES:
        candidate_path = base / candidate
        if candidate_path.exists():
            return candidate_path
    return None


def read_csv_header(path: Union[str, Path]) -> list[str]:
    file_path = Path(path)
    if not file_path.exists():
        raise ArtifactLoadError(f"CSV artifact not found: {file_path}")
    try:
        with file_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration as exc:
                raise ArtifactLoadError(f"CSV artifact is empty (no header row): {file_path}") from exc
    except OSError as exc:
        raise ArtifactLoadError(f"Failed to read CSV header from {file_path}: {exc}") from exc
    return [str(col) for col in header]


def read_jsonl_first_record(path: Union[str, Path]) -> Optional[dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        raise ArtifactLoadError(f"JSONL artifact not found: {file_path}")
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ArtifactLoadError(
                        f"Invalid JSONL record in {file_path} at line {line_number}: {exc}"
                    ) from exc
                if not isinstance(payload, dict):
                    raise ArtifactLoadError(
                        f"Invalid JSONL record in {file_path} at line {line_number}: expected object, got {type(payload).__name__}."
                    )
                return payload
    except OSError as exc:
        raise ArtifactLoadError(f"Failed to read JSONL artifact {file_path}: {exc}") from exc
    return None


def _read_exact(stream: BinaryIO, size: int, *, source: str) -> bytes:
    data = stream.read(size)
    if len(data) != size:
        raise ArtifactLoadError(
            f"Unexpected EOF while reading NumPy header from {source}: needed {size} bytes, got {len(data)}."
        )
    return data


def _read_npy_header_from_stream(stream: BinaryIO, *, source: str) -> NpyArrayHeader:
    magic = _read_exact(stream, 6, source=source)
    if magic != b"\x93NUMPY":
        raise ArtifactLoadError(
            f"Invalid .npy magic header for {source}: expected NumPy binary file, got {magic!r}."
        )

    version_bytes = _read_exact(stream, 2, source=source)
    version = (int(version_bytes[0]), int(version_bytes[1]))
    major, minor = version

    if major == 1:
        header_len = struct.unpack("<H", _read_exact(stream, 2, source=source))[0]
    elif major in (2, 3):
        header_len = struct.unpack("<I", _read_exact(stream, 4, source=source))[0]
    else:
        raise ArtifactLoadError(f"Unsupported NumPy header version {version!r} for {source}.")

    header_bytes = _read_exact(stream, int(header_len), source=source)
    encoding = "latin1" if major < 3 else "utf-8"
    try:
        header = ast.literal_eval(header_bytes.decode(encoding))
    except (UnicodeDecodeError, SyntaxError, ValueError) as exc:
        raise ArtifactLoadError(f"Failed to parse NumPy header in {source}: {exc}") from exc

    if not isinstance(header, dict):
        raise ArtifactLoadError(f"Invalid NumPy header in {source}: expected dict, got {type(header).__name__}.")

    shape_raw = header.get("shape")
    if not isinstance(shape_raw, tuple):
        raise ArtifactLoadError(f"Invalid NumPy header in {source}: missing tuple 'shape'.")

    try:
        shape = tuple(int(dim) for dim in shape_raw)
    except (TypeError, ValueError) as exc:
        raise ArtifactLoadError(f"Invalid NumPy shape in {source}: {shape_raw!r}") from exc

    descr = header.get("descr")
    fortran_order = header.get("fortran_order")
    if not isinstance(descr, str):
        raise ArtifactLoadError(f"Invalid NumPy header in {source}: missing string 'descr'.")
    if not isinstance(fortran_order, bool):
        raise ArtifactLoadError(f"Invalid NumPy header in {source}: missing bool 'fortran_order'.")

    return NpyArrayHeader(
        source=source,
        version=version,
        descr=descr,
        fortran_order=fortran_order,
        shape=shape,
    )


def read_npy_header(path: Union[str, Path]) -> NpyArrayHeader:
    file_path = Path(path)
    if not file_path.exists():
        raise ArtifactLoadError(f"NumPy artifact not found: {file_path}")
    try:
        with file_path.open("rb") as handle:
            return _read_npy_header_from_stream(handle, source=str(file_path))
    except OSError as exc:
        raise ArtifactLoadError(f"Failed to read NumPy artifact {file_path}: {exc}") from exc


def read_npz_headers(path: Union[str, Path]) -> dict[str, NpyArrayHeader]:
    file_path = Path(path)
    if not file_path.exists():
        raise ArtifactLoadError(f"NumPy ZIP artifact not found: {file_path}")
    try:
        with zipfile.ZipFile(file_path, "r") as archive:
            headers: dict[str, NpyArrayHeader] = {}
            for member_name in archive.namelist():
                if not member_name.endswith(".npy"):
                    continue
                with archive.open(member_name, "r") as member_stream:
                    header = _read_npy_header_from_stream(member_stream, source=f"{file_path}:{member_name}")
                key = member_name[:-4] if member_name.endswith(".npy") else member_name
                headers[key] = header
            if not headers:
                raise ArtifactLoadError(f"NPZ artifact {file_path} contains no .npy members.")
            return headers
    except zipfile.BadZipFile as exc:
        raise ArtifactLoadError(f"Invalid NPZ artifact (bad zip file): {file_path}") from exc
    except OSError as exc:
        raise ArtifactLoadError(f"Failed to read NPZ artifact {file_path}: {exc}") from exc


def _require_runtime_dependencies() -> tuple[Any, Any]:
    try:
        import numpy as np  # type: ignore
    except ModuleNotFoundError as exc:
        raise ArtifactLoadError(
            "Missing dependency 'numpy' required for runtime artifact loading. "
            "Install runtime dependencies and rerun."
        ) from exc

    try:
        import pandas as pd  # type: ignore
    except ModuleNotFoundError as exc:
        raise ArtifactLoadError(
            "Missing dependency 'pandas' required for runtime artifact loading. "
            "Install runtime dependencies and rerun."
        ) from exc

    return np, pd


def load_runtime_artifacts(artifacts_dir: Union[str, Path] = DEFAULT_ARTIFACTS_DIR) -> dict[str, Any]:
    """
    Load the core Streamlit-serving artifacts into memory.

    This is intentionally infrastructure-layer code so later UI/service code can depend on a
    single loader instead of parsing files directly.
    """

    np, pd = _require_runtime_dependencies()
    base = Path(artifacts_dir)

    try:
        manifest = load_artifact_manifest(base)
        selected_params = load_selected_params(base)

        movie_metadata = pd.read_csv(base / "movie_metadata.csv")
        global_popularity = pd.read_csv(base / "global_popularity_train.csv")
        genre_popularity = pd.read_csv(base / "genre_popularity_train.csv")

        genre_feature_columns = read_json_file(base / "genre_feature_columns.json")
        if not isinstance(genre_feature_columns, list):
            raise ArtifactLoadError(
                f"Invalid genre_feature_columns.json in {base}: expected JSON list, got {type(genre_feature_columns).__name__}."
            )

        with np.load(base / "genre_features.npz", allow_pickle=False) as genre_npz:
            genre_features = {
                "movie_ids": genre_npz["movie_ids"],
                "genre_matrix": genre_npz["genre_matrix"],
            }

        with np.load(base / "cf_item_similarity.npz", allow_pickle=False) as cf_npz:
            cf_item_similarity = cf_npz["similarity"]
        cf_item_ids = np.load(base / "cf_item_ids.npy", allow_pickle=False)

        user_profiles_path = resolve_user_profiles_artifact(base)
        user_profiles = None
        if user_profiles_path is not None:
            suffix = user_profiles_path.suffix.lower()
            if suffix == ".jsonl":
                user_profiles = pd.read_json(user_profiles_path, lines=True)
            elif suffix == ".csv":
                user_profiles = pd.read_csv(user_profiles_path)
            elif suffix == ".parquet":
                user_profiles = pd.read_parquet(user_profiles_path)
            else:
                raise ArtifactLoadError(f"Unsupported user profile artifact format: {user_profiles_path}")

        return {
            "artifacts_dir": str(base.resolve()),
            "manifest": manifest,
            "selected_params": selected_params,
            "movie_metadata": movie_metadata,
            "global_popularity": global_popularity,
            "genre_popularity": genre_popularity,
            "genre_feature_columns": genre_feature_columns,
            "genre_features": genre_features,
            "cf_item_similarity": cf_item_similarity,
            "cf_item_ids": cf_item_ids,
            "user_profiles_path": str(user_profiles_path) if user_profiles_path else None,
            "user_profiles": user_profiles,
        }
    except ArtifactLoadError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapper for caller clarity.
        raise ArtifactLoadError(
            f"Unexpected failure while loading runtime artifacts from {base}: {type(exc).__name__}: {exc}"
        ) from exc
