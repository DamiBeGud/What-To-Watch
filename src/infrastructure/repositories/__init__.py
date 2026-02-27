from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from src.infrastructure.loaders.artifact_loader import ArtifactLoadError

from .artifact_manifest_repository import ArtifactManifestRepositoryImpl
from .genre_popularity_repository import GenrePopularityRepositoryImpl
from .movie_metadata_repository import MovieMetadataRepositoryImpl
from .popularity_repository import GlobalPopularityRepositoryImpl
from .similarity_repository import SimilarityRepositoryImpl
from .user_profile_repository import UserProfileRepositoryImpl


@dataclass(frozen=True)
class ArtifactRepositoryBundle:
    movie_metadata: MovieMetadataRepositoryImpl
    global_popularity: GlobalPopularityRepositoryImpl
    genre_popularity: GenrePopularityRepositoryImpl
    similarity: SimilarityRepositoryImpl
    user_profiles: UserProfileRepositoryImpl
    artifact_manifest: ArtifactManifestRepositoryImpl


def _require_runtime_key(runtime_artifacts: Mapping[str, Any], key: str) -> Any:
    if key not in runtime_artifacts:
        raise ArtifactLoadError(f"Runtime artifacts missing required key '{key}' for repository initialization.")
    value = runtime_artifacts[key]
    if value is None:
        raise ArtifactLoadError(f"Runtime artifacts key '{key}' is None; repository initialization requires loaded data.")
    return value


def build_artifact_repository_bundle(
    runtime_artifacts: Mapping[str, Any],
    *,
    artifacts_dir: str,
) -> ArtifactRepositoryBundle:
    """Build concrete artifact-backed repositories from the Task 7 runtime loader output."""

    try:
        runtime_dict = dict(runtime_artifacts)
        movie_metadata = _require_runtime_key(runtime_dict, "movie_metadata")
        global_popularity = _require_runtime_key(runtime_dict, "global_popularity")
        genre_popularity = _require_runtime_key(runtime_dict, "genre_popularity")
        genre_features = _require_runtime_key(runtime_dict, "genre_features")
        cf_item_similarity = _require_runtime_key(runtime_dict, "cf_item_similarity")
        cf_item_ids = _require_runtime_key(runtime_dict, "cf_item_ids")
        genre_feature_columns = _require_runtime_key(runtime_dict, "genre_feature_columns")

        if not isinstance(genre_features, Mapping):
            raise ArtifactLoadError(
                "Runtime artifact 'genre_features' has invalid type for repository initialization; expected mapping."
            )
        content_movie_ids = genre_features.get("movie_ids")
        content_genre_matrix = genre_features.get("genre_matrix")
        if content_movie_ids is None or content_genre_matrix is None:
            raise ArtifactLoadError(
                "Runtime artifact 'genre_features' is missing required members 'movie_ids' and/or 'genre_matrix'."
            )

        return ArtifactRepositoryBundle(
            movie_metadata=MovieMetadataRepositoryImpl(movie_metadata),
            global_popularity=GlobalPopularityRepositoryImpl(global_popularity),
            genre_popularity=GenrePopularityRepositoryImpl(genre_popularity),
            similarity=SimilarityRepositoryImpl(
                content_movie_ids=content_movie_ids,
                content_genre_matrix=content_genre_matrix,
                content_feature_columns=list(genre_feature_columns) if isinstance(genre_feature_columns, list) else [],
                collaborative_item_ids=cf_item_ids,
                collaborative_similarity_matrix=cf_item_similarity,
            ),
            user_profiles=UserProfileRepositoryImpl(
                runtime_dict.get("user_profiles"),
                source_path=runtime_dict.get("user_profiles_path"),
            ),
            artifact_manifest=ArtifactManifestRepositoryImpl.from_runtime_artifacts(
                runtime_dict,
                artifacts_dir=artifacts_dir,
            ),
        )
    except ArtifactLoadError:
        raise
    except Exception as exc:  # pragma: no cover - defensive wrapper for clearer dependency setup errors
        raise ArtifactLoadError(
            f"Unexpected failure while building artifact repositories from runtime artifacts: "
            f"{type(exc).__name__}: {exc}"
        ) from exc


__all__ = [
    "ArtifactRepositoryBundle",
    "ArtifactManifestRepositoryImpl",
    "GenrePopularityRepositoryImpl",
    "GlobalPopularityRepositoryImpl",
    "MovieMetadataRepositoryImpl",
    "SimilarityRepositoryImpl",
    "UserProfileRepositoryImpl",
    "build_artifact_repository_bundle",
]
