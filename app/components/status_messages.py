from __future__ import annotations

from typing import Any

import streamlit as st


def render_setup_issue_panel(presented_issue: dict[str, Any]) -> None:
    st.error(presented_issue.get("user_message") or "Setup issue.")
    notes = presented_issue.get("notes") or []
    warnings = presented_issue.get("warnings") or []
    if notes:
        for note in notes:
            st.caption("Note: {}".format(note))
    if warnings:
        for warning in warnings:
            st.warning(str(warning))
    developer_details = presented_issue.get("developer_details")
    if developer_details:
        with st.expander("Developer Details", expanded=False):
            st.code(str(developer_details))


def render_response_status(presented_response: dict[str, Any]) -> None:
    if not presented_response:
        return

    ok = bool(presented_response.get("ok", True))
    status_message = presented_response.get("status_message") or "Ready."
    fallback_used = bool(presented_response.get("fallback_used"))
    mode_used = presented_response.get("mode_label") or presented_response.get("mode_used") or "unknown"

    if not ok:
        st.error(status_message)
    elif fallback_used:
        st.warning(status_message)
    else:
        st.info(status_message)

    st.caption("Mode used: {}".format(mode_used))

    fallback_summary = presented_response.get("fallback_summary")
    if fallback_summary:
        st.caption(str(fallback_summary))
    fallback_reason = presented_response.get("fallback_reason")
    if fallback_reason and not fallback_summary:
        st.caption("Fallback reason: {}".format(fallback_reason))

    for warning in presented_response.get("warnings") or []:
        st.warning(str(warning))

    metadata_notice = presented_response.get("metadata_notice")
    if metadata_notice:
        st.info(str(metadata_notice))

    empty_state = presented_response.get("empty_state")
    if isinstance(empty_state, dict):
        message = str(empty_state.get("message") or "No recommendations are available for the current request.")
        kind = str(empty_state.get("kind") or "empty")
        action = str(empty_state.get("action") or "").strip()

        if kind in {"error", "setup_error"}:
            st.error(message)
        elif kind in {"warning", "empty_after_filters", "insufficient_preferences", "no_source_selected"}:
            st.warning(message)
        else:
            st.info(message)
        if action:
            st.caption(action)


def render_empty_results_hint() -> None:
    st.info(
        "No recommendation request has run yet. Choose a mode, set inputs, then click `Generate Recommendations`."
    )
