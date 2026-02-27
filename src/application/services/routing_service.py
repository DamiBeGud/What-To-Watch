from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.domain.enums import FallbackReason, RecommendationExecutionMode, RecommendationMode


@dataclass(frozen=True)
class RoutingDecision:
    mode_requested: RecommendationMode
    mode_used: RecommendationExecutionMode
    fallback_used: bool
    fallback_reason: Optional[FallbackReason]
    route_name: str
    trace: dict[str, Any] = field(default_factory=dict)


class RoutingService:
    """Encapsulates explicit mode routing and fallback escalation decisions."""

    def route_returning_user(
        self,
        *,
        user_id: Optional[int],
        has_profile: bool,
        has_preferred_genres: bool,
        has_genre_candidates: Optional[bool] = None,
    ) -> RoutingDecision:
        trace = {
            "mode_requested": RecommendationMode.RETURNING_USER.value,
            "selected_user_id": user_id,
            "has_profile": bool(has_profile),
            "has_preferred_genres": bool(has_preferred_genres),
        }
        if has_genre_candidates is not None:
            trace["has_genre_candidates"] = bool(has_genre_candidates)

        if has_profile and has_preferred_genres and has_genre_candidates is not False:
            return RoutingDecision(
                mode_requested=RecommendationMode.RETURNING_USER,
                mode_used=RecommendationExecutionMode.RETURNING_USER,
                fallback_used=False,
                fallback_reason=None,
                route_name="returning_user_genre_popularity_placeholder",
                trace=trace,
            )
        return RoutingDecision(
            mode_requested=RecommendationMode.RETURNING_USER,
            mode_used=RecommendationExecutionMode.COLD_START_FALLBACK,
            fallback_used=True,
            fallback_reason=FallbackReason.MISSING_OR_WEAK_USER_PROFILE,
            route_name="returning_user_global_popularity_fallback_placeholder",
            trace=trace,
        )

    def route_new_user(
        self,
        *,
        has_selected_genres: bool,
        has_liked_movies: bool,
        has_effective_genres: bool,
        has_genre_candidates: bool,
    ) -> RoutingDecision:
        trace = {
            "mode_requested": RecommendationMode.NEW_USER.value,
            "has_selected_genres": bool(has_selected_genres),
            "has_liked_movies": bool(has_liked_movies),
            "has_effective_genres": bool(has_effective_genres),
            "has_genre_candidates": bool(has_genre_candidates),
        }
        if has_effective_genres and has_genre_candidates:
            return RoutingDecision(
                mode_requested=RecommendationMode.NEW_USER,
                mode_used=RecommendationExecutionMode.NEW_USER,
                fallback_used=False,
                fallback_reason=None,
                route_name="new_user_genre_popularity_placeholder",
                trace=trace,
            )
        return RoutingDecision(
            mode_requested=RecommendationMode.NEW_USER,
            mode_used=RecommendationExecutionMode.COLD_START_FALLBACK,
            fallback_used=True,
            fallback_reason=FallbackReason.INSUFFICIENT_PREFERENCE_SIGNAL,
            route_name="new_user_global_popularity_fallback_placeholder",
            trace=trace,
        )

    def route_similar_movie(
        self,
        *,
        source_movie_id: Optional[int],
        source_exists: bool,
        has_source_genres: bool,
    ) -> RoutingDecision:
        trace = {
            "mode_requested": RecommendationMode.SIMILAR_MOVIE.value,
            "selected_source_movie_id": source_movie_id,
            "source_exists": bool(source_exists),
            "has_source_genres": bool(has_source_genres),
        }
        if source_movie_id is None or not source_exists:
            return RoutingDecision(
                mode_requested=RecommendationMode.SIMILAR_MOVIE,
                mode_used=RecommendationExecutionMode.SIMILAR_MOVIE,
                fallback_used=True,
                fallback_reason=FallbackReason.MISSING_SOURCE_MOVIE,
                route_name="similar_movie_global_popularity_fallback_missing_source",
                trace=trace,
            )
        if not has_source_genres:
            return RoutingDecision(
                mode_requested=RecommendationMode.SIMILAR_MOVIE,
                mode_used=RecommendationExecutionMode.SIMILAR_MOVIE,
                fallback_used=True,
                fallback_reason=FallbackReason.MISSING_SOURCE_GENRES,
                route_name="similar_movie_global_popularity_fallback_missing_genres",
                trace=trace,
            )
        return RoutingDecision(
            mode_requested=RecommendationMode.SIMILAR_MOVIE,
            mode_used=RecommendationExecutionMode.SIMILAR_MOVIE,
            fallback_used=False,
            fallback_reason=None,
            route_name="similar_movie_genre_overlap_placeholder",
            trace=trace,
        )
