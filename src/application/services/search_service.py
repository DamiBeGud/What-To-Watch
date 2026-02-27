from __future__ import annotations

from typing import Any, Optional

from src.application.ports.repositories import RepositoryBundle
from src.core.config import AppConfig
from src.domain.enums import RecommendationMode


class SearchService:
    """Repository-backed title search/disambiguation and UI option helpers."""

    def __init__(self, *, repositories: RepositoryBundle, config: AppConfig) -> None:
        self._repositories = repositories
        self._config = config

    def get_ui_options(self) -> dict[str, Any]:
        metadata_repo = self._repositories.movie_metadata
        user_repo = self._repositories.user_profiles
        year_min, year_max = metadata_repo.get_year_bounds()
        return {
            "available_modes": [mode.value for mode in RecommendationMode],
            "genres": metadata_repo.list_genres(),
            "year_min": year_min,
            "year_max": year_max,
            "known_user_ids": user_repo.known_user_ids(limit=self._config.user_select_limit),
            "title_search_seed": metadata_repo.get_title_search_seed(limit=min(300, metadata_repo.count_movies())),
            "top_n_bounds": {
                "min": self._config.min_top_n,
                "max": self._config.max_top_n,
                "default": self._config.default_top_n,
            },
        }

    def search_titles(self, query: str, *, limit: Optional[int] = None) -> list[dict[str, Any]]:
        max_items = int(limit or self._config.title_search_limit)
        return self._repositories.movie_metadata.search_titles(query, limit=max_items)

    def lookup_exact_title_candidates(self, title_text: str) -> list[dict[str, Any]]:
        return self._repositories.movie_metadata.lookup_by_normalized_title(title_text)

