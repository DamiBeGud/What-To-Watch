from __future__ import annotations

from typing import Any

import streamlit as st

from app.state.session_state import SessionKeys
from src.core.config import AppConfig


def render_shared_filters(ui_options: dict[str, Any], config: AppConfig) -> dict[str, Any]:
    top_n_bounds = ui_options.get("top_n_bounds") or {}
    min_top_n = int(top_n_bounds.get("min", config.min_top_n))
    max_top_n = int(top_n_bounds.get("max", config.max_top_n))

    st.markdown("### Shared Filters")
    st.slider(
        "Top-N results",
        min_value=min_top_n,
        max_value=max_top_n,
        key=SessionKeys.TOP_N,
        help="Task 8 placeholder UI: this controls how many cards the scaffold renders.",
    )

    available_genres = ui_options.get("genres") or []
    st.multiselect(
        "Genres",
        options=available_genres,
        key=SessionKeys.FILTER_GENRES,
        help="Shared genre filter applied after placeholder candidate generation.",
    )

    year_min = ui_options.get("year_min")
    year_max = ui_options.get("year_max")
    if isinstance(year_min, int) and isinstance(year_max, int) and year_min <= year_max:
        st.slider(
            "Year range",
            min_value=year_min,
            max_value=year_max,
            key=SessionKeys.FILTER_YEAR_RANGE,
            help="Shared year filter for all modes.",
        )
    else:
        st.caption("Year filter unavailable until movie metadata is loaded.")

    return {
        "top_n": st.session_state.get(SessionKeys.TOP_N, config.default_top_n),
        "genres": list(st.session_state.get(SessionKeys.FILTER_GENRES, [])),
        "year_range": tuple(st.session_state.get(SessionKeys.FILTER_YEAR_RANGE, ())),
    }

