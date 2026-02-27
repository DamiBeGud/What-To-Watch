from __future__ import annotations

from typing import Any

import streamlit as st

from app.state.session_state import SessionKeys


def _label_map_from_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for row in rows:
        label = str(row.get("label") or row.get("title") or row.get("movieId"))
        mapping[label] = row
    return mapping


def render_mode_specific_inputs(
    *,
    mode: str,
    ui_options: dict[str, Any],
    mode_context: dict[str, Any],
) -> dict[str, Any]:
    if mode == "returning_user":
        return _render_returning_user_inputs(ui_options)
    if mode == "new_user":
        return _render_new_user_inputs(ui_options, mode_context)
    if mode == "similar_movie":
        return _render_similar_movie_inputs(mode_context)
    st.warning("Unknown mode selection. Defaulting to Returning User controls.")
    return _render_returning_user_inputs(ui_options)


def _render_returning_user_inputs(ui_options: dict[str, Any]) -> dict[str, Any]:
    st.markdown("### Returning User Input")
    known_user_ids = ui_options.get("known_user_ids") or []
    if known_user_ids:
        current_user_id = st.session_state.get(SessionKeys.RETURNING_USER_ID)
        if current_user_id not in known_user_ids:
            st.session_state[SessionKeys.RETURNING_USER_ID] = known_user_ids[0]
        st.selectbox(
            "Demo user ID (from exported user profile artifact)",
            options=known_user_ids,
            key=SessionKeys.RETURNING_USER_ID,
            index=0,
            help="Uses the compact `user_profiles_train` artifact exported in Task 7.",
        )
    else:
        st.caption("No known user IDs are available yet from the user profile artifact.")

    st.text_input(
        "Manual user ID (optional override)",
        key=SessionKeys.RETURNING_USER_ID_MANUAL,
        help="If set, this overrides the selected demo user ID.",
        placeholder="e.g. 1",
    )
    return {
        "selected_user_id": st.session_state.get(SessionKeys.RETURNING_USER_ID),
        "manual_user_id": st.session_state.get(SessionKeys.RETURNING_USER_ID_MANUAL),
    }


def _render_new_user_inputs(ui_options: dict[str, Any], mode_context: dict[str, Any]) -> dict[str, Any]:
    st.markdown("### New User / Cold Start Input")
    st.text_input(
        "Search liked titles (optional)",
        key=SessionKeys.NEW_USER_TITLE_QUERY,
        placeholder="Type a movie title...",
        help="Pick a few titles if possible so the app can produce stronger recommendations.",
    )

    search_results = list(mode_context.get("search_results") or [])
    if bool(mode_context.get("no_title_match")):
        st.caption("No title matches yet. Try a broader title or pick genre preferences below.")

    label_map = _label_map_from_rows(search_results)
    labels = list(label_map.keys())
    selected_labels = st.session_state.get(SessionKeys.NEW_USER_LIKED_LABELS, []) or []
    filtered_selected_labels = [str(label) for label in selected_labels if str(label) in label_map]
    if filtered_selected_labels != list(selected_labels):
        st.session_state[SessionKeys.NEW_USER_LIKED_LABELS] = filtered_selected_labels

    st.multiselect(
        "Liked titles",
        options=labels,
        key=SessionKeys.NEW_USER_LIKED_LABELS,
        help="Selections are kept in session state across reruns.",
    )

    genre_options = ui_options.get("genres") or []
    st.multiselect(
        "Preferred genres (optional)",
        options=genre_options,
        key=SessionKeys.NEW_USER_GENRES,
    )

    selected_labels = st.session_state.get(SessionKeys.NEW_USER_LIKED_LABELS, []) or []
    liked_movie_ids: list[int] = []
    for label in selected_labels:
        row = label_map.get(str(label))
        if row is None:
            continue
        movie_id = row.get("movieId")
        if isinstance(movie_id, int):
            liked_movie_ids.append(movie_id)

    return {
        "liked_movie_ids": liked_movie_ids,
        "liked_title_labels": [str(label) for label in selected_labels],
        "genre_preferences": list(st.session_state.get(SessionKeys.NEW_USER_GENRES, [])),
        "title_query": str(mode_context.get("title_query") or ""),
        "search_match_count": int(mode_context.get("search_match_count") or 0),
    }


def _render_similar_movie_inputs(mode_context: dict[str, Any]) -> dict[str, Any]:
    st.markdown("### Similar Movie Input")
    st.text_input(
        "Search source title",
        key=SessionKeys.SIMILAR_TITLE_QUERY,
        placeholder="Type a movie title...",
        help="Choose a source title and the app will return similar recommendations.",
    )

    search_results = list(mode_context.get("search_results") or [])
    if bool(mode_context.get("no_title_match")):
        st.caption("No source title matches yet. Try a shorter or less specific search.")

    label_map = _label_map_from_rows(search_results)
    options = ["<Select a source movie>"] + list(label_map.keys())
    current_value = st.session_state.get(SessionKeys.SIMILAR_SOURCE_LABEL)
    if current_value not in options:
        st.session_state[SessionKeys.SIMILAR_SOURCE_LABEL] = options[0]

    st.selectbox(
        "Source movie",
        options=options,
        key=SessionKeys.SIMILAR_SOURCE_LABEL,
        help="If no source title is selected, the app will explain and show a fallback list.",
    )

    selected_label = st.session_state.get(SessionKeys.SIMILAR_SOURCE_LABEL)
    source_movie_id = None
    if selected_label and selected_label != options[0]:
        row = label_map.get(str(selected_label))
        if isinstance(row, dict) and isinstance(row.get("movieId"), int):
            source_movie_id = int(row["movieId"])

    return {
        "source_movie_id": source_movie_id,
        "source_movie_label": None if selected_label == options[0] else selected_label,
        "title_query": str(mode_context.get("title_query") or ""),
        "search_match_count": int(mode_context.get("search_match_count") or 0),
    }
