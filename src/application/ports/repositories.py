from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Collection, Iterable, Optional, Protocol, Sequence


@dataclass(frozen=True)
class MovieMetadataRecord:
    movie_id: int
    title: str
    year: Optional[int]
    genres: str
    genres_list: tuple[str, ...]


@dataclass(frozen=True)
class GlobalPopularityEntry:
    movie_id: int
    rating_count: Optional[int]
    mean_rating: Optional[float]
    pop_weighted_rating: Optional[float]
    pop_score: Optional[float]


@dataclass(frozen=True)
class GenrePopularityEntry:
    genre: str
    movie_id: int
    rating_count: Optional[int]
    mean_rating: Optional[float]
    genre_pop_score: Optional[float]


@dataclass(frozen=True)
class UserProfileRecord:
    user_id: int
    train_interaction_count: Optional[int]
    positive_interaction_count: Optional[int]
    train_mean_rating: Optional[float]
    seen_movie_ids: tuple[int, ...]
    positive_seed_movie_ids: tuple[int, ...]
    preferred_genres: tuple[str, ...]


@dataclass(frozen=True)
class SimilarityAssetsSummary:
    has_content_assets: bool
    has_collaborative_assets: bool
    content_movie_count: int
    content_feature_count: int
    collaborative_item_count: int
    content_genre_matrix_shape: Optional[tuple[int, ...]]
    collaborative_similarity_shape: Optional[tuple[int, ...]]
    content_feature_columns: tuple[str, ...]


class MovieMetadataRepository(Protocol):
    def count_movies(self) -> int: ...
    def get_movie(self, movie_id: int) -> Optional[MovieMetadataRecord]: ...
    def get_movie_label(self, movie_id: int) -> str: ...
    def get_movie_genres(self, movie_id: int) -> tuple[str, ...]: ...
    def iter_movie_genres(self) -> Iterable[tuple[int, tuple[str, ...]]]: ...
    def list_genres(self) -> list[str]: ...
    def get_year_bounds(self) -> tuple[Optional[int], Optional[int]]: ...
    def search_titles(self, query: str, *, limit: int) -> list[dict[str, Any]]: ...
    def get_title_search_seed(self, *, limit: int) -> list[dict[str, Any]]: ...
    def lookup_by_normalized_title(self, normalized_title: str) -> list[dict[str, Any]]: ...


class GlobalPopularityRepository(Protocol):
    def count_rows(self) -> int: ...
    def top(
        self,
        *,
        limit: int,
        exclude_movie_ids: Optional[Collection[int]] = None,
    ) -> list[GlobalPopularityEntry]: ...


class GenrePopularityRepository(Protocol):
    def count_rows(self) -> int: ...
    def available_genres(self) -> list[str]: ...
    def top_for_genres(
        self,
        genres: Sequence[str],
        *,
        limit: int,
        exclude_movie_ids: Optional[Collection[int]] = None,
    ) -> list[GenrePopularityEntry]: ...


class SimilarityRepository(Protocol):
    def get_summary(self) -> SimilarityAssetsSummary: ...
    def get_content_feature_columns(self) -> list[str]: ...
    def get_content_movie_ids(self) -> Any: ...
    def get_content_genre_matrix(self) -> Any: ...
    def get_collaborative_item_ids(self) -> Any: ...
    def get_collaborative_similarity_matrix(self) -> Any: ...
    def get_content_row_index(self, movie_id: int) -> Optional[int]: ...
    def get_collaborative_row_index(self, movie_id: int) -> Optional[int]: ...


class UserProfileRepository(Protocol):
    def count_profiles(self) -> int: ...
    def get_source_path(self) -> Optional[str]: ...
    def known_user_ids(self, *, limit: Optional[int] = None) -> list[int]: ...
    def get_profile(self, user_id: int) -> Optional[UserProfileRecord]: ...


class ArtifactManifestRepository(Protocol):
    def get_artifacts_dir(self) -> str: ...
    def get_manifest_entries(self) -> list[dict[str, Any]]: ...
    def get_selected_params(self) -> dict[str, Any]: ...
    def get_provenance(self) -> Optional[dict[str, Any]]: ...


class RepositoryBundle(Protocol):
    @property
    def movie_metadata(self) -> MovieMetadataRepository: ...

    @property
    def global_popularity(self) -> GlobalPopularityRepository: ...

    @property
    def genre_popularity(self) -> GenrePopularityRepository: ...

    @property
    def similarity(self) -> SimilarityRepository: ...

    @property
    def user_profiles(self) -> UserProfileRepository: ...

    @property
    def artifact_manifest(self) -> ArtifactManifestRepository: ...

