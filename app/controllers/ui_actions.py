from __future__ import annotations

from time import perf_counter
from typing import Any

import streamlit as st

from app.controllers.request_parser import build_recommendation_request
from app.state.session_state import SessionKeys
from src.core.config import AppConfig
from src.serving.api import ServingAPI


def _query_text(key: str) -> str:
    return str(st.session_state.get(key, "") or "").strip()


@st.cache_data(show_spinner=False)
def _search_titles_cached(
    status_signature: str,
    mode: str,
    query: str,
    limit: int,
    _serving_api: ServingAPI,
) -> list[dict[str, Any]]:
    # `status_signature` invalidates this cache when artifact/runtime status changes.
    # `_serving_api` is prefixed so Streamlit excludes it from hashing.
    _ = (status_signature, mode)
    return _serving_api.search_titles(query, limit=limit)


def prepare_mode_input_context(
    *,
    mode: str,
    serving_api: ServingAPI,
    ui_options: dict[str, Any],
    config: AppConfig,
    status_signature: str,
) -> dict[str, Any]:
    started = perf_counter()
    max_items = max(config.title_search_limit, 40)

    if mode == "new_user":
        query = _query_text(SessionKeys.NEW_USER_TITLE_QUERY)
        if query:
            search_results = _search_titles_cached(
                status_signature=status_signature,
                mode=mode,
                query=query,
                limit=max_items,
                _serving_api=serving_api,
            )
        else:
            search_results = list(ui_options.get("title_search_seed") or [])[:max_items]
        return {
            "title_query": query,
            "search_results": search_results,
            "search_match_count": len(search_results),
            "no_title_match": bool(query and not search_results),
            "timings_ms": {
                "mode_input_context_ms": round((perf_counter() - started) * 1000.0, 3),
            },
            "cache": {
                "title_search_cache": bool(query),
            },
        }

    if mode == "similar_movie":
        query = _query_text(SessionKeys.SIMILAR_TITLE_QUERY)
        if query:
            search_results = _search_titles_cached(
                status_signature=status_signature,
                mode=mode,
                query=query,
                limit=max_items,
                _serving_api=serving_api,
            )
        else:
            search_results = list(ui_options.get("title_search_seed") or [])[:max_items]
        return {
            "title_query": query,
            "search_results": search_results,
            "search_match_count": len(search_results),
            "no_title_match": bool(query and not search_results),
            "timings_ms": {
                "mode_input_context_ms": round((perf_counter() - started) * 1000.0, 3),
            },
            "cache": {
                "title_search_cache": bool(query),
            },
        }

    return {
        "timings_ms": {
            "mode_input_context_ms": round((perf_counter() - started) * 1000.0, 3),
        }
    }


def execute_recommendation_action(
    *,
    mode: str,
    shared_filters: dict[str, Any],
    mode_inputs: dict[str, Any],
    config: AppConfig,
    serving_api: ServingAPI,
    mode_context: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    action_started = perf_counter()

    request_build_started = perf_counter()
    request, controller_warnings = build_recommendation_request(
        mode=mode,
        shared_filters=shared_filters,
        mode_inputs=mode_inputs,
        config=config,
    )
    request_build_ms = round((perf_counter() - request_build_started) * 1000.0, 3)

    service_call_started = perf_counter()
    response = serving_api.recommend(request)
    service_call_ms = round((perf_counter() - service_call_started) * 1000.0, 3)

    debug_payload = response.get("debug") if isinstance(response.get("debug"), dict) else {}
    timings = debug_payload.get("timings_ms") if isinstance(debug_payload.get("timings_ms"), dict) else {}
    timings.update(
        {
            "ui_request_parse_validation_ms": request_build_ms,
            "ui_facade_call_ms": service_call_ms,
            "ui_action_total_ms": round((perf_counter() - action_started) * 1000.0, 3),
        }
    )

    mode_context_timings = mode_context.get("timings_ms") if isinstance(mode_context.get("timings_ms"), dict) else {}
    if "mode_input_context_ms" in mode_context_timings:
        timings["ui_mode_input_context_ms"] = mode_context_timings["mode_input_context_ms"]
    debug_payload["timings_ms"] = timings

    cache_info = mode_context.get("cache") if isinstance(mode_context.get("cache"), dict) else {}
    if cache_info:
        debug_payload["ui_cache"] = cache_info
    response["debug"] = debug_payload
    return request, response, controller_warnings
