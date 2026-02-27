from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .enums import RecommendationMode


@dataclass(frozen=True)
class RecommendationFilters:
    genres: tuple[str, ...] = ()
    year_min: Optional[int] = None
    year_max: Optional[int] = None

    def as_debug_dict(self) -> dict[str, object]:
        year_range: tuple[Optional[int], Optional[int]] | tuple[()] = ()
        if self.year_min is not None or self.year_max is not None:
            year_range = (self.year_min, self.year_max)
        return {
            "genres": list(self.genres),
            "year_range": list(year_range) if year_range else [],
        }


@dataclass(frozen=True)
class RecommendationRequest:
    mode: RecommendationMode
    top_n: int
    filters: RecommendationFilters = field(default_factory=RecommendationFilters)
    user_id: Optional[int] = None
    liked_movie_ids: tuple[int, ...] = ()
    genre_preferences: tuple[str, ...] = ()
    source_movie_id: Optional[int] = None

