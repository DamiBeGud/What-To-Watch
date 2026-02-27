from __future__ import annotations

from typing import Any, Collection, Optional, Sequence

from src.application.ports.repositories import GenrePopularityEntry

from ._base import safe_float, safe_int, safe_str


def _descending_score_key(value: Optional[float]) -> tuple[bool, float]:
    if value is None:
        return (True, 0.0)
    return (False, -float(value))


def _descending_count_key(value: Optional[int]) -> tuple[bool, int]:
    if value is None:
        return (True, 0)
    return (False, -int(value))


class GenrePopularityRepositoryImpl:
    """Repository for genre-aware popularity rows with merged multi-genre retrieval."""

    def __init__(self, genre_popularity_df: Any) -> None:
        rows_by_genre: dict[str, list[GenrePopularityEntry]] = {}
        total_rows = 0
        if genre_popularity_df is not None:
            for row in genre_popularity_df.itertuples(index=False):
                movie_id = safe_int(getattr(row, "movieId", None))
                if movie_id is None:
                    continue
                genre = safe_str(getattr(row, "genre", None), default="").strip()
                if not genre:
                    continue
                entry = GenrePopularityEntry(
                    genre=genre,
                    movie_id=movie_id,
                    rating_count=safe_int(getattr(row, "rating_count", None)),
                    mean_rating=safe_float(getattr(row, "mean_rating", None)),
                    genre_pop_score=safe_float(getattr(row, "genre_pop_score", None)),
                )
                rows_by_genre.setdefault(genre, []).append(entry)
                total_rows += 1

        for genre_rows in rows_by_genre.values():
            genre_rows.sort(
                key=lambda item: (
                    _descending_score_key(item.genre_pop_score),
                    _descending_count_key(item.rating_count),
                    item.movie_id,
                )
            )

        self._rows_by_genre = rows_by_genre
        self._total_rows = total_rows

    def count_rows(self) -> int:
        return self._total_rows

    def available_genres(self) -> list[str]:
        return sorted(self._rows_by_genre.keys())

    def top_for_genres(
        self,
        genres: Sequence[str],
        *,
        limit: int,
        exclude_movie_ids: Optional[Collection[int]] = None,
    ) -> list[GenrePopularityEntry]:
        max_items = max(0, int(limit))
        if max_items == 0:
            return []

        normalized_genres = {str(genre).strip() for genre in genres if str(genre).strip()}
        if not normalized_genres:
            return []

        exclude = {int(movie_id) for movie_id in (exclude_movie_ids or [])}
        candidates: list[GenrePopularityEntry] = []
        for genre in normalized_genres:
            candidates.extend(self._rows_by_genre.get(genre, []))

        candidates.sort(
            key=lambda item: (
                _descending_score_key(item.genre_pop_score),
                _descending_count_key(item.rating_count),
                item.movie_id,
            )
        )

        out: list[GenrePopularityEntry] = []
        seen_movie_ids: set[int] = set()
        for row in candidates:
            if row.movie_id in exclude or row.movie_id in seen_movie_ids:
                continue
            seen_movie_ids.add(row.movie_id)
            out.append(row)
            if len(out) >= max_items:
                break
        return out
