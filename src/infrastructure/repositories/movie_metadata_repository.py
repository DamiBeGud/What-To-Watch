from __future__ import annotations

from typing import Any, Iterable, Optional

from src.application.ports.repositories import MovieMetadataRecord

from ._base import safe_int, safe_str
from .lookups import MetadataLookups, build_metadata_lookups, normalize_title, split_genres


class MovieMetadataRepositoryImpl:
    """Artifact-backed metadata repository with centralized title/search lookups."""

    def __init__(self, movie_metadata_df: Any) -> None:
        self._movie_metadata_df = movie_metadata_df
        records = list(self._iter_records_from_df(movie_metadata_df))
        self._lookups: MetadataLookups = build_metadata_lookups(records)

    def _iter_records_from_df(self, movie_metadata_df: Any) -> Iterable[MovieMetadataRecord]:
        if movie_metadata_df is None:
            return []
        records: list[MovieMetadataRecord] = []
        for row in movie_metadata_df.itertuples(index=False):
            movie_id = safe_int(getattr(row, "movieId", None))
            if movie_id is None:
                continue
            title = safe_str(getattr(row, "title", None), default=f"Movie {movie_id}")
            year = safe_int(getattr(row, "year", None))
            genres = safe_str(getattr(row, "genres", None), default="(no genres listed)")
            genres_list = split_genres(genres)
            records.append(
                MovieMetadataRecord(
                    movie_id=movie_id,
                    title=title,
                    year=year,
                    genres=genres,
                    genres_list=genres_list,
                )
            )
        return records

    def count_movies(self) -> int:
        return len(self._lookups.records_by_id)

    def get_movie(self, movie_id: int) -> Optional[MovieMetadataRecord]:
        return self._lookups.records_by_id.get(int(movie_id))

    def get_movie_label(self, movie_id: int) -> str:
        record = self.get_movie(int(movie_id))
        if record is None:
            return f"Movie {int(movie_id)}"
        if record.year is not None:
            return f"{record.title} ({record.year}) [{record.movie_id}]"
        return f"{record.title} [{record.movie_id}]"

    def get_movie_genres(self, movie_id: int) -> tuple[str, ...]:
        return self._lookups.genres_by_movie_id.get(int(movie_id), tuple())

    def iter_movie_genres(self) -> Iterable[tuple[int, tuple[str, ...]]]:
        return self._lookups.genres_by_movie_id.items()

    def list_genres(self) -> list[str]:
        return list(self._lookups.genre_values)

    def get_year_bounds(self) -> tuple[Optional[int], Optional[int]]:
        return (self._lookups.year_min, self._lookups.year_max)

    def lookup_by_normalized_title(self, normalized_title: str) -> list[dict[str, Any]]:
        key = normalize_title(normalized_title)
        return [dict(row) for row in self._lookups.normalized_title_lookup.get(key, [])]

    def get_title_search_seed(self, *, limit: int) -> list[dict[str, Any]]:
        max_items = max(0, int(limit))
        if max_items == 0:
            return []
        return [dict(row) for row in self._lookups.search_rows[:max_items]]

    def search_titles(self, query: str, *, limit: int) -> list[dict[str, Any]]:
        rows = self._lookups.search_rows
        if not rows:
            return []

        max_items = max(0, int(limit))
        if max_items == 0:
            return []

        query_norm = normalize_title(query)
        if not query_norm:
            return [dict(row) for row in rows[:max_items]]

        starts_with: list[dict[str, Any]] = []
        contains: list[dict[str, Any]] = []
        for row in rows:
            title_norm = str(row.get("title_norm", ""))
            if title_norm.startswith(query_norm):
                starts_with.append(dict(row))
            elif query_norm in title_norm:
                contains.append(dict(row))
            if len(starts_with) + len(contains) >= max_items * 4:
                # Bound work during typing (same intent as the Task 8 placeholder implementation).
                continue

        return (starts_with + contains)[:max_items]

