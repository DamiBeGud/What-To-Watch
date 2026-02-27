from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from src.domain.requests import RecommendationFilters
from src.domain.responses import RecommendationItem


@dataclass(frozen=True)
class FilterApplicationResult:
    items: tuple[RecommendationItem, ...]
    warnings: tuple[str, ...]
    relaxation_applied: bool
    relaxation_steps: tuple[str, ...]


class FilterService:
    """Applies shared post-ranking filters with controlled relaxation to keep results usable."""

    _relaxation_warning = (
        "No results matched all selected filters, so the UI scaffold relaxed filters to keep the list non-empty."
    )

    def apply_shared_filters(
        self,
        items: Sequence[RecommendationItem],
        filters: RecommendationFilters,
    ) -> FilterApplicationResult:
        if not items:
            return FilterApplicationResult(items=tuple(items), warnings=(), relaxation_applied=False, relaxation_steps=("noop_empty",))

        selected_genres = {str(genre).strip() for genre in filters.genres if str(genre).strip()}
        has_year_filter = filters.year_min is not None and filters.year_max is not None
        has_any_filter = bool(selected_genres or has_year_filter)

        filtered_all = tuple(
            item
            for item in items
            if self._passes(item, selected_genres=selected_genres, filters=filters, apply_genres=True, apply_years=True)
        )
        if filtered_all:
            return FilterApplicationResult(
                items=filtered_all,
                warnings=(),
                relaxation_applied=False,
                relaxation_steps=("strict",),
            )

        warnings: list[str] = []
        if has_any_filter:
            warnings.append(self._relaxation_warning)

        filtered_genres_only = tuple(
            item
            for item in items
            if self._passes(item, selected_genres=selected_genres, filters=filters, apply_genres=True, apply_years=False)
        )
        if filtered_genres_only:
            return FilterApplicationResult(
                items=filtered_genres_only,
                warnings=tuple(warnings),
                relaxation_applied=has_any_filter,
                relaxation_steps=("strict", "relax_years"),
            )

        filtered_none = tuple(
            item
            for item in items
            if self._passes(item, selected_genres=selected_genres, filters=filters, apply_genres=False, apply_years=False)
        )
        return FilterApplicationResult(
            items=filtered_none,
            warnings=tuple(warnings),
            relaxation_applied=has_any_filter,
            relaxation_steps=("strict", "relax_years", "relax_genres"),
        )

    def _passes(
        self,
        item: RecommendationItem,
        *,
        selected_genres: set[str],
        filters: RecommendationFilters,
        apply_genres: bool,
        apply_years: bool,
    ) -> bool:
        if apply_genres and selected_genres:
            item_genres = {part.strip() for part in str(item.genres or "").split("|") if part.strip()}
            if not item_genres.intersection(selected_genres):
                return False

        if apply_years and filters.year_min is not None and filters.year_max is not None:
            if item.year is None or item.year < filters.year_min or item.year > filters.year_max:
                return False

        return True
