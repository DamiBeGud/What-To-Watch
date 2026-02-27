from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from src.core.config import AppConfig


class SessionKeys:
    MODE = "ui_mode"
    TOP_N = "filter_top_n"
    FILTER_GENRES = "filter_genres"
    FILTER_YEAR_RANGE = "filter_year_range"

    RETURNING_USER_ID = "returning_user_id_select"
    RETURNING_USER_ID_MANUAL = "returning_user_id_manual"

    NEW_USER_TITLE_QUERY = "new_user_title_query"
    NEW_USER_LIKED_LABELS = "new_user_liked_title_labels"
    NEW_USER_GENRES = "new_user_genres"

    SIMILAR_TITLE_QUERY = "similar_title_query"
    SIMILAR_SOURCE_LABEL = "similar_source_label"

    LAST_REQUEST = "last_request_payload"
    LAST_RESPONSE = "last_response_payload"
    LAST_CONTROLLER_WARNINGS = "last_controller_warnings"
    DEBUG_ENABLED = "debug_enabled"


def _set_default_if_missing(key: str, value: Any) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


def ensure_session_state(config: AppConfig, ui_options: dict[str, Any]) -> None:
    available_modes = ui_options.get("available_modes") or []
    default_mode = config.default_mode if config.default_mode in available_modes else "returning_user"
    _set_default_if_missing(SessionKeys.MODE, default_mode)
    if st.session_state.get(SessionKeys.MODE) not in available_modes and available_modes:
        st.session_state[SessionKeys.MODE] = available_modes[0]

    top_n_bounds = ui_options.get("top_n_bounds") or {}
    min_top_n = int(top_n_bounds.get("min", config.min_top_n))
    max_top_n = int(top_n_bounds.get("max", config.max_top_n))
    default_top_n = int(top_n_bounds.get("default", config.default_top_n))
    default_top_n = max(min_top_n, min(default_top_n, max_top_n))
    _set_default_if_missing(SessionKeys.TOP_N, default_top_n)
    try:
        current_top_n = int(st.session_state.get(SessionKeys.TOP_N, default_top_n))
    except (TypeError, ValueError):
        current_top_n = default_top_n
    st.session_state[SessionKeys.TOP_N] = max(min_top_n, min(current_top_n, max_top_n))

    _set_default_if_missing(SessionKeys.FILTER_GENRES, [])

    year_min = ui_options.get("year_min")
    year_max = ui_options.get("year_max")
    if isinstance(year_min, int) and isinstance(year_max, int) and year_min <= year_max:
        year_default = (year_min, year_max)
    else:
        year_default = (1980, 2020)
    _set_default_if_missing(SessionKeys.FILTER_YEAR_RANGE, year_default)
    current_year_range = st.session_state.get(SessionKeys.FILTER_YEAR_RANGE, year_default)
    if (
        isinstance(current_year_range, (list, tuple))
        and len(current_year_range) == 2
        and isinstance(year_default, tuple)
        and len(year_default) == 2
    ):
        try:
            low = max(int(year_default[0]), min(int(current_year_range[0]), int(year_default[1])))
            high = max(low, min(int(current_year_range[1]), int(year_default[1])))
            st.session_state[SessionKeys.FILTER_YEAR_RANGE] = (low, high)
        except (TypeError, ValueError):
            st.session_state[SessionKeys.FILTER_YEAR_RANGE] = year_default

    known_user_ids = ui_options.get("known_user_ids") or []
    default_user_id = known_user_ids[0] if known_user_ids else None
    _set_default_if_missing(SessionKeys.RETURNING_USER_ID, default_user_id)
    if known_user_ids and st.session_state.get(SessionKeys.RETURNING_USER_ID) not in known_user_ids:
        st.session_state[SessionKeys.RETURNING_USER_ID] = known_user_ids[0]
    _set_default_if_missing(SessionKeys.RETURNING_USER_ID_MANUAL, "")

    _set_default_if_missing(SessionKeys.NEW_USER_TITLE_QUERY, "")
    _set_default_if_missing(SessionKeys.NEW_USER_LIKED_LABELS, [])
    _set_default_if_missing(SessionKeys.NEW_USER_GENRES, [])

    _set_default_if_missing(SessionKeys.SIMILAR_TITLE_QUERY, "")
    _set_default_if_missing(SessionKeys.SIMILAR_SOURCE_LABEL, None)

    _set_default_if_missing(SessionKeys.LAST_REQUEST, None)
    _set_default_if_missing(SessionKeys.LAST_RESPONSE, None)
    _set_default_if_missing(SessionKeys.LAST_CONTROLLER_WARNINGS, [])
    _set_default_if_missing(SessionKeys.DEBUG_ENABLED, bool(config.debug_mode_default))


def get_current_mode() -> str:
    return str(st.session_state.get(SessionKeys.MODE, "returning_user"))


def get_shared_filters() -> dict[str, Any]:
    return {
        "top_n": st.session_state.get(SessionKeys.TOP_N),
        "genres": list(st.session_state.get(SessionKeys.FILTER_GENRES, [])),
        "year_range": tuple(st.session_state.get(SessionKeys.FILTER_YEAR_RANGE, ())),
    }


def store_last_request_response(
    request: Optional[dict[str, Any]],
    response: Optional[dict[str, Any]],
    *,
    controller_warnings: Optional[list[str]] = None,
) -> None:
    st.session_state[SessionKeys.LAST_REQUEST] = request
    st.session_state[SessionKeys.LAST_RESPONSE] = response
    st.session_state[SessionKeys.LAST_CONTROLLER_WARNINGS] = controller_warnings or []


def get_last_request() -> Optional[dict[str, Any]]:
    payload = st.session_state.get(SessionKeys.LAST_REQUEST)
    return payload if isinstance(payload, dict) else None


def get_last_response() -> Optional[dict[str, Any]]:
    payload = st.session_state.get(SessionKeys.LAST_RESPONSE)
    return payload if isinstance(payload, dict) else None


def get_last_controller_warnings() -> list[str]:
    warnings = st.session_state.get(SessionKeys.LAST_CONTROLLER_WARNINGS, [])
    return [str(item) for item in warnings] if isinstance(warnings, list) else []


def clear_last_response() -> None:
    store_last_request_response(None, None, controller_warnings=[])
