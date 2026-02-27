from __future__ import annotations

from time import perf_counter
from typing import Any, Optional

from src.application.ports.repositories import RepositoryBundle
from src.application.services import ApplicationServiceBundle
from src.core.config import AppConfig
from src.domain.enums import RecommendationMode
from src.domain.requests import RecommendationFilters, RecommendationRequest


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        if value != value:  # NaN check
            return None
    except Exception:
        pass
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_int_tuple(value: Any) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    out: list[int] = []
    seen: set[int] = set()
    for raw in value:
        coerced = _safe_int(raw)
        if coerced is None or coerced in seen:
            continue
        seen.add(coerced)
        out.append(coerced)
    return tuple(out)


def _coerce_str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    out: list[str] = []
    seen: set[str] = set()
    for raw in value:
        text = str(raw).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return tuple(out)


def _parse_mode(value: Any, *, default_mode: str) -> RecommendationMode:
    raw = str(value or default_mode)
    try:
        return RecommendationMode(raw)
    except ValueError:
        try:
            return RecommendationMode(default_mode)
        except ValueError:
            return RecommendationMode.RETURNING_USER


class ServingAPI:
    """
    Thin facade for the Streamlit UI.

    Task 10 refactors routing, fallback, explanation, search, and post-filter behavior into the application
    service layer. This facade preserves the Task 8/9 UI contract (`get_app_status`, `get_ui_options`,
    `search_titles`, `recommend`) and adapts UI dictionaries to domain DTOs.
    """

    MODES: tuple[str, ...] = tuple(mode.value for mode in RecommendationMode)

    def __init__(
        self,
        *,
        config: AppConfig,
        repositories: Optional[RepositoryBundle],
        services: Optional[ApplicationServiceBundle],
        validation_report: Optional[dict[str, Any]],
        startup_ready: bool,
        setup_user_message: Optional[str],
        setup_developer_details: Optional[str],
        startup_timing_ms: Optional[dict[str, float]] = None,
    ) -> None:
        self._config = config
        self._repositories = repositories
        self._services = services
        self._validation_report = validation_report
        self._startup_ready = startup_ready
        self._setup_user_message = setup_user_message
        self._setup_developer_details = setup_developer_details
        self._startup_timing_ms = dict(startup_timing_ms or {})

    def is_ready(self) -> bool:
        return bool(self._startup_ready and self._repositories is not None and self._services is not None)

    def get_app_status(self) -> dict[str, Any]:
        movie_count = 0
        user_profile_count = 0
        user_profiles_path = None
        selected_params: dict[str, Any] = {}
        manifest_entry_count = 0
        similarity_summary: dict[str, Any] | None = None

        if self._repositories is not None:
            movie_count = self._repositories.movie_metadata.count_movies()
            user_profile_count = self._repositories.user_profiles.count_profiles()
            user_profiles_path = self._repositories.user_profiles.get_source_path()
            selected_params = self._repositories.artifact_manifest.get_selected_params()
            manifest_entry_count = len(self._repositories.artifact_manifest.get_manifest_entries())
            sim = self._repositories.similarity.get_summary()
            similarity_summary = {
                "has_content_assets": sim.has_content_assets,
                "has_collaborative_assets": sim.has_collaborative_assets,
                "content_movie_count": sim.content_movie_count,
                "content_feature_count": sim.content_feature_count,
                "collaborative_item_count": sim.collaborative_item_count,
                "content_genre_matrix_shape": list(sim.content_genre_matrix_shape) if sim.content_genre_matrix_shape else None,
                "collaborative_similarity_shape": (
                    list(sim.collaborative_similarity_shape) if sim.collaborative_similarity_shape else None
                ),
            }

        artifacts_summary: dict[str, Any] = {
            "artifacts_dir": self._config.artifacts_dir,
            "has_runtime_artifacts": self._repositories is not None,
            "has_application_services": self._services is not None,
            "movie_count": movie_count,
            "known_user_profiles": user_profile_count,
            "manifest_entries": manifest_entry_count,
            "performance_limits": {
                "candidate_pool_multiplier": max(1, int(self._config.candidate_pool_multiplier)),
                "candidate_pool_cap": max(10, int(self._config.candidate_pool_cap)),
                "similar_scan_limit": max(100, int(self._config.similar_scan_limit)),
            },
        }
        if self._repositories is not None:
            artifacts_summary["user_profiles_path"] = user_profiles_path
            artifacts_summary["selected_params"] = selected_params
            artifacts_summary["similarity_assets"] = similarity_summary

        return {
            "startup_ready": self.is_ready(),
            "setup_user_message": self._setup_user_message,
            "setup_developer_details": self._setup_developer_details,
            "validation_report": self._validation_report,
            "artifacts_summary": artifacts_summary,
            "startup_timing_ms": dict(self._startup_timing_ms),
        }

    def get_ui_options(self) -> dict[str, Any]:
        if self._services is None:
            return {
                "available_modes": list(self.MODES),
                "genres": [],
                "year_min": None,
                "year_max": None,
                "known_user_ids": [],
                "title_search_seed": [],
                "top_n_bounds": {
                    "min": self._config.min_top_n,
                    "max": self._config.max_top_n,
                    "default": self._config.default_top_n,
                },
            }
        return self._services.search_service.get_ui_options()

    def search_titles(self, query: str, limit: Optional[int] = None) -> list[dict[str, Any]]:
        if self._services is None:
            return []
        return self._services.search_service.search_titles(query, limit=limit)

    def recommend(self, request: dict[str, Any]) -> dict[str, Any]:
        started = perf_counter()
        if not self.is_ready() or self._services is None:
            total_ms = round((perf_counter() - started) * 1000.0, 3)
            return {
                "ok": False,
                "mode_requested": request.get("mode"),
                "mode_used": None,
                "fallback_used": False,
                "fallback_reason": None,
                "status_message": "Setup issue: the app could not load its artifact bundle.",
                "warnings": [self._setup_user_message] if self._setup_user_message else [],
                "items": [],
                "request_echo": request,
                "debug": {
                    "startup_ready": False,
                    "timings_ms": {
                        "api_total_ms": total_ms,
                    },
                    "startup_timing_ms": dict(self._startup_timing_ms),
                },
            }

        parse_started = perf_counter()
        domain_request = self._to_domain_request(request)
        parse_ms = round((perf_counter() - parse_started) * 1000.0, 3)

        service_started = perf_counter()
        domain_response = self._services.recommendation_service.recommend(domain_request)
        service_ms = round((perf_counter() - service_started) * 1000.0, 3)

        payload = domain_response.to_ui_dict()
        payload["request_echo"] = request
        total_ms = round((perf_counter() - started) * 1000.0, 3)

        debug_payload = payload.get("debug") if isinstance(payload.get("debug"), dict) else {}
        debug_timings = debug_payload.get("timings_ms") if isinstance(debug_payload.get("timings_ms"), dict) else {}
        debug_timings.update(
            {
                "api_request_adapter_ms": parse_ms,
                "api_service_call_ms": service_ms,
                "api_total_ms": total_ms,
            }
        )
        debug_payload["timings_ms"] = debug_timings
        debug_payload.setdefault("startup_timing_ms", dict(self._startup_timing_ms))
        debug_payload.setdefault(
            "performance_limits",
            {
                "candidate_pool_multiplier": max(1, int(self._config.candidate_pool_multiplier)),
                "candidate_pool_cap": max(10, int(self._config.candidate_pool_cap)),
                "similar_scan_limit": max(100, int(self._config.similar_scan_limit)),
            },
        )
        payload["debug"] = debug_payload
        return payload

    def _to_domain_request(self, request: dict[str, Any]) -> RecommendationRequest:
        mode = _parse_mode(request.get("mode"), default_mode=self._config.default_mode)
        top_n = _safe_int(request.get("top_n"))
        if top_n is None:
            top_n = self._config.default_top_n

        filters_payload = request.get("filters") or {}
        year_min = None
        year_max = None
        year_range = filters_payload.get("year_range") if isinstance(filters_payload, dict) else None
        if isinstance(year_range, (list, tuple)) and len(year_range) == 2:
            year_min = _safe_int(year_range[0])
            year_max = _safe_int(year_range[1])

        filters = RecommendationFilters(
            genres=_coerce_str_tuple(filters_payload.get("genres") if isinstance(filters_payload, dict) else None),
            year_min=year_min,
            year_max=year_max,
        )

        return RecommendationRequest(
            mode=mode,
            top_n=int(top_n),
            filters=filters,
            user_id=_safe_int(request.get("user_id")),
            liked_movie_ids=_coerce_int_tuple(request.get("liked_movie_ids")),
            genre_preferences=_coerce_str_tuple(request.get("genre_preferences")),
            source_movie_id=_safe_int(request.get("source_movie_id")),
        )
