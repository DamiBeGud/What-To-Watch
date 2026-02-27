from __future__ import annotations

from typing import Any, Collection, Optional

from src.application.ports.repositories import GlobalPopularityEntry

from ._base import safe_float, safe_int


def _descending_score_key(value: Optional[float]) -> tuple[bool, float]:
    if value is None:
        return (True, 0.0)
    return (False, -float(value))


def _descending_count_key(value: Optional[int]) -> tuple[bool, int]:
    if value is None:
        return (True, 0)
    return (False, -int(value))


class GlobalPopularityRepositoryImpl:
    """Repository for global popularity fallback rows exported in Task 7."""

    def __init__(self, global_popularity_df: Any) -> None:
        rows: list[GlobalPopularityEntry] = []
        if global_popularity_df is not None:
            for row in global_popularity_df.itertuples(index=False):
                movie_id = safe_int(getattr(row, "movieId", None))
                if movie_id is None:
                    continue
                rows.append(
                    GlobalPopularityEntry(
                        movie_id=movie_id,
                        rating_count=safe_int(getattr(row, "rating_count", None)),
                        mean_rating=safe_float(getattr(row, "mean_rating", None)),
                        pop_weighted_rating=safe_float(getattr(row, "pop_weighted_rating", None)),
                        pop_score=safe_float(getattr(row, "pop_score", None)),
                    )
                )
        rows.sort(
            key=lambda item: (
                _descending_score_key(item.pop_score),
                _descending_count_key(item.rating_count),
                item.movie_id,
            )
        )
        self._rows = rows

    def count_rows(self) -> int:
        return len(self._rows)

    def top(
        self,
        *,
        limit: int,
        exclude_movie_ids: Optional[Collection[int]] = None,
    ) -> list[GlobalPopularityEntry]:
        max_items = max(0, int(limit))
        if max_items == 0:
            return []
        exclude = {int(movie_id) for movie_id in (exclude_movie_ids or [])}
        out: list[GlobalPopularityEntry] = []
        for row in self._rows:
            if row.movie_id in exclude:
                continue
            out.append(row)
            if len(out) >= max_items:
                break
        return out
