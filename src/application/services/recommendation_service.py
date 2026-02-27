from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Optional, Sequence

from src.application.ports.repositories import RepositoryBundle, UserProfileRecord
from src.core.config import AppConfig
from src.domain.enums import FallbackReason, RecommendationMode
from src.domain.requests import RecommendationFilters, RecommendationRequest
from src.domain.responses import RecommendationItem, RecommendationResponse

from .explanation_service import ExplanationService
from .filter_service import FilterService
from .routing_service import RoutingDecision, RoutingService


def _dedupe_preserve_order(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        text = str(raw).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return tuple(out)


def _dedupe_ints(values: Sequence[int]) -> tuple[int, ...]:
    seen: set[int] = set()
    out: list[int] = []
    for raw in values:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return tuple(out)


@dataclass(frozen=True)
class _ModeResult:
    decision: RoutingDecision
    status_message: str
    warnings: tuple[str, ...]
    items: tuple[RecommendationItem, ...]
    debug: dict[str, Any]


class RecommendationService:
    """Application-layer orchestration for placeholder recommendation flows (Task 10)."""

    def __init__(
        self,
        *,
        repositories: RepositoryBundle,
        config: AppConfig,
        routing_service: RoutingService,
        explanation_service: ExplanationService,
        filter_service: FilterService,
    ) -> None:
        self._repositories = repositories
        self._config = config
        self._routing = routing_service
        self._explanations = explanation_service
        self._filters = filter_service

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        total_started = perf_counter()

        normalize_started = perf_counter()
        normalized = self._normalize_request(request)
        normalize_ms = round((perf_counter() - normalize_started) * 1000.0, 3)

        mode_started = perf_counter()
        if normalized.mode == RecommendationMode.SIMILAR_MOVIE:
            mode_result = self._recommend_similar_movie_placeholder(normalized)
        elif normalized.mode == RecommendationMode.NEW_USER:
            mode_result = self._recommend_new_user_placeholder(normalized)
        else:
            mode_result = self._recommend_returning_user_placeholder(normalized)
        mode_ms = round((perf_counter() - mode_started) * 1000.0, 3)

        filter_started = perf_counter()
        filter_result = self._filters.apply_shared_filters(mode_result.items, normalized.filters)
        final_items = tuple(filter_result.items[: normalized.top_n])
        warnings = tuple(list(mode_result.warnings) + list(filter_result.warnings))
        filter_ms = round((perf_counter() - filter_started) * 1000.0, 3)

        assemble_started = perf_counter()

        debug = dict(mode_result.debug)
        debug.setdefault("placeholder", True)
        debug["request_top_n"] = normalized.top_n
        debug["applied_filters"] = normalized.filters.as_debug_dict()
        debug["items_before_filters"] = len(mode_result.items)
        debug["items_after_filters"] = len(final_items)
        debug["filter_relaxation_applied"] = bool(filter_result.relaxation_applied)
        debug["filter_relaxation_steps"] = list(filter_result.relaxation_steps)
        debug["route"] = {
            "route_name": mode_result.decision.route_name,
            "trace": dict(mode_result.decision.trace),
        }
        debug["effective_limits"] = {
            "candidate_pool_multiplier": max(1, int(self._config.candidate_pool_multiplier)),
            "candidate_pool_cap": max(10, int(self._config.candidate_pool_cap)),
            "similar_scan_limit": max(100, int(self._config.similar_scan_limit)),
        }
        timings = debug.get("timings_ms") if isinstance(debug.get("timings_ms"), dict) else {}
        timings.update(
            {
                "normalize_request_ms": normalize_ms,
                "route_and_candidate_generation_ms": mode_ms,
                "filter_and_postprocess_ms": filter_ms,
                "assemble_response_ms": round((perf_counter() - assemble_started) * 1000.0, 3),
                "service_total_ms": round((perf_counter() - total_started) * 1000.0, 3),
            }
        )
        debug["timings_ms"] = timings

        return RecommendationResponse(
            ok=True,
            mode_requested=normalized.mode,
            mode_used=mode_result.decision.mode_used,
            fallback_used=mode_result.decision.fallback_used,
            fallback_reason=mode_result.decision.fallback_reason,
            status_message=mode_result.status_message,
            warnings=warnings,
            items=final_items,
            debug=debug,
        )

    def _resolve_candidate_limit(self, top_n: int) -> int:
        min_top_n = max(1, int(top_n))
        multiplier = max(1, int(self._config.candidate_pool_multiplier))
        pool_cap = max(min_top_n, int(self._config.candidate_pool_cap))
        target = max(min_top_n, min_top_n * multiplier)
        return min(target, pool_cap)

    def _normalize_request(self, request: RecommendationRequest) -> RecommendationRequest:
        top_n = int(request.top_n)
        top_n = max(self._config.min_top_n, min(top_n, self._config.max_top_n))

        liked_movie_ids = _dedupe_ints(request.liked_movie_ids)
        genre_preferences = _dedupe_preserve_order(request.genre_preferences)
        filter_genres = _dedupe_preserve_order(request.filters.genres)

        return RecommendationRequest(
            mode=request.mode,
            top_n=top_n,
            filters=RecommendationFilters(
                genres=filter_genres,
                year_min=request.filters.year_min,
                year_max=request.filters.year_max,
            ),
            user_id=request.user_id,
            liked_movie_ids=liked_movie_ids,
            genre_preferences=genre_preferences,
            source_movie_id=request.source_movie_id,
        )

    def _recommend_returning_user_placeholder(self, request: RecommendationRequest) -> _ModeResult:
        mode_started = perf_counter()
        user_id = request.user_id
        warnings: list[str] = []
        preferred_genres: tuple[str, ...] = ()
        seen_movie_ids: set[int] = set()

        profile: Optional[UserProfileRecord] = None
        if user_id is not None:
            profile = self._repositories.user_profiles.get_profile(user_id)
            if profile is None:
                warnings.append(self._explanations.warning_unknown_returning_user(user_id))
            else:
                preferred_genres = tuple(str(genre) for genre in profile.preferred_genres if str(genre))
                seen_movie_ids = {int(movie_id) for movie_id in profile.seen_movie_ids}
        else:
            warnings.append(self._explanations.warning_missing_returning_user_selection())

        decision = self._routing.route_returning_user(
            user_id=user_id,
            has_profile=profile is not None,
            has_preferred_genres=bool(preferred_genres),
            has_genre_candidates=None,
        )

        candidate_limit = self._resolve_candidate_limit(request.top_n)
        candidate_started = perf_counter()
        if not decision.fallback_used:
            items = self._genre_popularity_items(
                preferred_genres,
                top_n=candidate_limit,
                exclude_movie_ids=seen_movie_ids,
            )
            if not items:
                # Explicit fallback escalation if genre-popularity produces no usable rows.
                decision = self._routing.route_returning_user(
                    user_id=user_id,
                    has_profile=profile is not None,
                    has_preferred_genres=bool(preferred_genres),
                    has_genre_candidates=False,
                )

        if decision.fallback_used:
            items = self._top_global_popularity_items(
                top_n=candidate_limit,
                exclude_movie_ids=seen_movie_ids,
                scenario="returning_user_fallback",
            )
        candidate_ms = round((perf_counter() - candidate_started) * 1000.0, 3)

        status_message = self._explanations.returning_user_status(user_id=user_id, fallback_used=decision.fallback_used)

        return _ModeResult(
            decision=decision,
            status_message=status_message,
            warnings=tuple(warnings),
            items=tuple(items[:candidate_limit]),
            debug={
                "selected_user_id": user_id,
                "preferred_genres_from_profile": list(preferred_genres),
                "candidate_limit": candidate_limit,
                "timings_ms": {
                    "mode_candidate_generation_ms": candidate_ms,
                    "mode_total_ms": round((perf_counter() - mode_started) * 1000.0, 3),
                },
            },
        )

    def _recommend_new_user_placeholder(self, request: RecommendationRequest) -> _ModeResult:
        mode_started = perf_counter()
        selected_genres = tuple(str(genre) for genre in request.genre_preferences if str(genre).strip())
        liked_movie_ids = tuple(int(movie_id) for movie_id in request.liked_movie_ids)
        warnings: list[str] = []

        derived_genres: list[str] = []
        for movie_id in liked_movie_ids:
            for genre in self._repositories.movie_metadata.get_movie_genres(movie_id):
                if genre and genre not in derived_genres:
                    derived_genres.append(genre)

        effective_genres = list(selected_genres)
        for genre in derived_genres:
            if genre not in effective_genres:
                effective_genres.append(genre)

        exclude_movie_ids = set(liked_movie_ids)
        candidate_limit = self._resolve_candidate_limit(request.top_n)
        candidate_started = perf_counter()
        genre_items = self._genre_popularity_items(
            effective_genres,
            top_n=candidate_limit,
            exclude_movie_ids=exclude_movie_ids,
        )

        decision = self._routing.route_new_user(
            has_selected_genres=bool(selected_genres),
            has_liked_movies=bool(liked_movie_ids),
            has_effective_genres=bool(effective_genres),
            has_genre_candidates=bool(genre_items),
        )

        if decision.fallback_used:
            items = self._top_global_popularity_items(
                top_n=candidate_limit,
                exclude_movie_ids=exclude_movie_ids,
                scenario="new_user_fallback",
            )
            warnings.append(
                self._explanations.warning_new_user_weak_signal(
                    has_any_preferences=bool(selected_genres or liked_movie_ids),
                )
            )
        else:
            items = genre_items
        candidate_ms = round((perf_counter() - candidate_started) * 1000.0, 3)

        status_message = self._explanations.new_user_status(fallback_used=decision.fallback_used)

        return _ModeResult(
            decision=decision,
            status_message=status_message,
            warnings=tuple(warnings),
            items=tuple(items[:candidate_limit]),
            debug={
                "liked_movie_ids": list(liked_movie_ids),
                "genre_preferences": list(selected_genres),
                "derived_genres": derived_genres[:10],
                "effective_genres": effective_genres[:10],
                "candidate_limit": candidate_limit,
                "timings_ms": {
                    "mode_candidate_generation_ms": candidate_ms,
                    "mode_total_ms": round((perf_counter() - mode_started) * 1000.0, 3),
                },
            },
        )

    def _recommend_similar_movie_placeholder(self, request: RecommendationRequest) -> _ModeResult:
        mode_started = perf_counter()
        source_movie_id = request.source_movie_id
        warnings: list[str] = []

        source_record = self._repositories.movie_metadata.get_movie(source_movie_id) if source_movie_id is not None else None
        source_genres = set(source_record.genres_list) if source_record is not None else set()

        decision = self._routing.route_similar_movie(
            source_movie_id=source_movie_id,
            source_exists=source_record is not None,
            has_source_genres=bool(source_genres),
        )

        candidate_limit = self._resolve_candidate_limit(request.top_n)
        candidate_started = perf_counter()
        similarity_debug: dict[str, Any] = {}
        if decision.fallback_used:
            if decision.fallback_reason == FallbackReason.MISSING_SOURCE_MOVIE:
                warnings.append(self._explanations.warning_pick_source_movie())
                scenario = "similar_movie_missing_source"
            else:
                warnings.append(self._explanations.warning_source_missing_genres())
                scenario = "similar_movie_missing_genres"

            exclude_ids = {int(source_movie_id)} if source_movie_id is not None and decision.fallback_reason == FallbackReason.MISSING_SOURCE_GENRES else set()
            items = self._top_global_popularity_items(
                top_n=candidate_limit,
                exclude_movie_ids=exclude_ids,
                scenario=scenario,
            )
        else:
            items, similarity_debug = self._similar_genre_overlap_items(
                source_movie_id=source_movie_id if source_movie_id is not None else -1,
                source_title=source_record.title if source_record is not None else "selected title",
                source_genres=source_genres,
                top_n=candidate_limit,
            )
        candidate_ms = round((perf_counter() - candidate_started) * 1000.0, 3)

        status_message = self._explanations.similar_movie_status(
            source_title=source_record.title if source_record is not None else None,
            fallback_reason=decision.fallback_reason,
        )

        return _ModeResult(
            decision=decision,
            status_message=status_message,
            warnings=tuple(warnings),
            items=tuple(items[:candidate_limit]),
            debug={
                "selected_source_movie_id": source_movie_id,
                "candidate_limit": candidate_limit,
                "similarity_scan": similarity_debug,
                "timings_ms": {
                    "mode_candidate_generation_ms": candidate_ms,
                    "mode_total_ms": round((perf_counter() - mode_started) * 1000.0, 3),
                    "mode_ranking_ms": similarity_debug.get("ranking_ms"),
                },
            },
        )

    def _record_to_item(
        self,
        movie_id: int,
        *,
        score: Optional[float],
        reason: str,
        source_label: str,
    ) -> Optional[RecommendationItem]:
        record = self._repositories.movie_metadata.get_movie(int(movie_id))
        if record is None:
            return None
        return RecommendationItem(
            movie_id=record.movie_id,
            title=record.title,
            year=record.year,
            genres=record.genres,
            score=score,
            reason=reason,
            source_label=source_label,
        )

    def _top_global_popularity_items(
        self,
        *,
        top_n: int,
        exclude_movie_ids: Optional[set[int]] = None,
        scenario: str,
    ) -> list[RecommendationItem]:
        exclude = exclude_movie_ids or set()
        items: list[RecommendationItem] = []
        for row in self._repositories.global_popularity.top(limit=top_n, exclude_movie_ids=exclude):
            reason = self._explanations.global_popularity_reason(
                scenario=scenario,
                rating_count=row.rating_count,
            )
            item = self._record_to_item(
                row.movie_id,
                score=row.pop_score,
                reason=reason,
                source_label="global_popularity_placeholder",
            )
            if item is None:
                continue
            items.append(item)
            if len(items) >= top_n:
                break
        return items

    def _genre_popularity_items(
        self,
        selected_genres: Sequence[str],
        *,
        top_n: int,
        exclude_movie_ids: Optional[set[int]] = None,
    ) -> list[RecommendationItem]:
        normalized_genres = [str(genre) for genre in selected_genres if str(genre).strip()]
        if not normalized_genres:
            return []

        items: list[RecommendationItem] = []
        for row in self._repositories.genre_popularity.top_for_genres(
            normalized_genres,
            limit=top_n,
            exclude_movie_ids=exclude_movie_ids or set(),
        ):
            item = self._record_to_item(
                row.movie_id,
                score=row.genre_pop_score,
                reason=self._explanations.genre_popularity_reason(row.genre),
                source_label="genre_popularity_placeholder",
            )
            if item is None:
                continue
            items.append(item)
            if len(items) >= top_n:
                break
        return items

    def _similar_genre_overlap_items(
        self,
        *,
        source_movie_id: int,
        source_title: str,
        source_genres: set[str],
        top_n: int,
    ) -> tuple[list[RecommendationItem], dict[str, Any]]:
        candidate_started = perf_counter()
        scan_limit = max(int(top_n), int(self._config.similar_scan_limit))
        scanned = 0
        scored: list[tuple[int, float, list[str]]] = []
        for movie_id, genres_list in self._repositories.movie_metadata.iter_movie_genres():
            if scanned >= scan_limit:
                break
            scanned += 1
            if movie_id == source_movie_id:
                continue
            overlap = [genre for genre in genres_list if genre in source_genres]
            if not overlap:
                continue
            score = float(len(overlap)) + (0.1 / (1 + abs(len(genres_list) - len(source_genres))))
            scored.append((movie_id, score, overlap))
        candidate_ms = round((perf_counter() - candidate_started) * 1000.0, 3)

        ranking_started = perf_counter()
        scored.sort(key=lambda item: (-item[1], item[0]))

        items: list[RecommendationItem] = []
        for movie_id, score, overlap in scored[: top_n * 2]:
            item = self._record_to_item(
                movie_id,
                score=score,
                reason=self._explanations.similar_movie_reason(source_title=source_title, overlap_genres=overlap),
                source_label="similar_genre_overlap_placeholder",
            )
            if item is not None:
                items.append(item)
            if len(items) >= top_n:
                break
        ranking_ms = round((perf_counter() - ranking_started) * 1000.0, 3)
        return items, {
            "scan_limit": scan_limit,
            "scanned_movies": scanned,
            "scored_candidates": len(scored),
            "candidate_generation_ms": candidate_ms,
            "ranking_ms": ranking_ms,
        }
