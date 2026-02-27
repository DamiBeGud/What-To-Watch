from __future__ import annotations

from typing import Any, Optional

from src.application.ports.repositories import SimilarityAssetsSummary

from ._base import array_to_int_index, shape_tuple


class SimilarityRepositoryImpl:
    """Repository for content and collaborative similarity assets exported offline."""

    def __init__(
        self,
        *,
        content_movie_ids: Any,
        content_genre_matrix: Any,
        content_feature_columns: list[str] | tuple[str, ...] | None,
        collaborative_item_ids: Any,
        collaborative_similarity_matrix: Any,
    ) -> None:
        self._content_movie_ids = content_movie_ids
        self._content_genre_matrix = content_genre_matrix
        self._content_feature_columns = tuple(str(col) for col in (content_feature_columns or []))
        self._collaborative_item_ids = collaborative_item_ids
        self._collaborative_similarity_matrix = collaborative_similarity_matrix

        self._content_index_by_movie_id = array_to_int_index(content_movie_ids)
        self._collaborative_index_by_movie_id = array_to_int_index(collaborative_item_ids)

        content_shape = shape_tuple(content_genre_matrix)
        cf_shape = shape_tuple(collaborative_similarity_matrix)
        content_movie_count = int(content_shape[0]) if content_shape and len(content_shape) >= 1 else len(self._content_index_by_movie_id)
        content_feature_count = (
            int(content_shape[1]) if content_shape and len(content_shape) >= 2 else len(self._content_feature_columns)
        )
        collaborative_item_count = int(cf_shape[0]) if cf_shape and len(cf_shape) >= 1 else len(self._collaborative_index_by_movie_id)

        self._summary = SimilarityAssetsSummary(
            has_content_assets=content_movie_ids is not None and content_genre_matrix is not None,
            has_collaborative_assets=collaborative_item_ids is not None and collaborative_similarity_matrix is not None,
            content_movie_count=content_movie_count,
            content_feature_count=content_feature_count,
            collaborative_item_count=collaborative_item_count,
            content_genre_matrix_shape=content_shape,
            collaborative_similarity_shape=cf_shape,
            content_feature_columns=self._content_feature_columns,
        )

    def get_summary(self) -> SimilarityAssetsSummary:
        return self._summary

    def get_content_feature_columns(self) -> list[str]:
        return list(self._content_feature_columns)

    def get_content_movie_ids(self) -> Any:
        return self._content_movie_ids

    def get_content_genre_matrix(self) -> Any:
        return self._content_genre_matrix

    def get_collaborative_item_ids(self) -> Any:
        return self._collaborative_item_ids

    def get_collaborative_similarity_matrix(self) -> Any:
        return self._collaborative_similarity_matrix

    def get_content_row_index(self, movie_id: int) -> Optional[int]:
        return self._content_index_by_movie_id.get(int(movie_id))

    def get_collaborative_row_index(self, movie_id: int) -> Optional[int]:
        return self._collaborative_index_by_movie_id.get(int(movie_id))

