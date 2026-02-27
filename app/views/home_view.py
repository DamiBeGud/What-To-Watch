from __future__ import annotations

from time import perf_counter
from typing import Any

import streamlit as st

from app.components.filters import render_shared_filters
from app.components.recommendation_cards import render_recommendation_cards
from app.components.search_box import render_mode_specific_inputs
from app.components.status_messages import (
    render_empty_results_hint,
    render_response_status,
    render_setup_issue_panel,
)
from app.controllers.ui_actions import execute_recommendation_action, prepare_mode_input_context
from app.presenters.error_presenter import present_runtime_exception, present_setup_issue
from app.presenters.recommendation_presenter import present_recommendation_response
from app.state import session_state
from app.state.session_state import SessionKeys
from src.core.config import AppConfig
from src.serving.api import ServingAPI


MODE_LABELS = {
    "returning_user": "Returning User",
    "new_user": "New User / Cold Start",
    "similar_movie": "Similar Movie",
}


def render_home_view(
    *,
    config: AppConfig,
    serving_api: ServingAPI,
    app_status: dict[str, Any],
    ui_options: dict[str, Any],
    status_signature: str,
) -> None:
    session_state.ensure_session_state(config, ui_options)

    st.title(config.page_title)
    st.caption(
        "Task 11 integration: requests flow through controller -> service facade -> presenter, with clear "
        "mode/fallback context and explicit edge-case messaging."
    )

    with st.sidebar:
        st.header("Controls")
        available_modes = ui_options.get("available_modes") or ["returning_user", "new_user", "similar_movie"]
        current_mode = session_state.get_current_mode()
        if current_mode not in available_modes:
            current_mode = available_modes[0]
            st.session_state[SessionKeys.MODE] = current_mode

        current_index = available_modes.index(current_mode) if current_mode in available_modes else 0
        st.selectbox(
            "Mode",
            options=available_modes,
            index=current_index,
            key=SessionKeys.MODE,
            format_func=lambda mode: MODE_LABELS.get(str(mode), str(mode)),
            help="Choose an intent first, then complete the mode-specific input fields.",
        )

        selected_mode = str(st.session_state.get(SessionKeys.MODE))
        mode_input_context = prepare_mode_input_context(
            mode=selected_mode,
            serving_api=serving_api,
            ui_options=ui_options,
            config=config,
            status_signature=status_signature,
        )

        shared_filters = render_shared_filters(ui_options, config)
        mode_inputs = render_mode_specific_inputs(
            mode=selected_mode,
            ui_options=ui_options,
            mode_context=mode_input_context,
        )

        generate_clicked = st.button(
            "Generate Recommendations",
            type="primary",
            use_container_width=True,
            help="Runs the selected mode and renders recommendation cards with explanations.",
        )
        clear_clicked = st.button("Clear Last Result", use_container_width=True)

        st.toggle(
            "Show Debug Panel",
            key=SessionKeys.DEBUG_ENABLED,
            help="Displays request/response context, mode trace, and startup metadata.",
        )

    if clear_clicked:
        session_state.clear_last_response()

    st.markdown("### Status & Explanations")
    if not bool(app_status.get("startup_ready")):
        render_setup_issue_panel(present_setup_issue(app_status))
        _render_bootstrap_summary(app_status)
        return

    if generate_clicked:
        try:
            request, response, controller_warnings = execute_recommendation_action(
                mode=str(st.session_state.get(SessionKeys.MODE)),
                shared_filters=shared_filters,
                mode_inputs=mode_inputs,
                config=config,
                serving_api=serving_api,
                mode_context=mode_input_context,
            )
            session_state.store_last_request_response(
                request,
                response,
                controller_warnings=controller_warnings,
            )
        except Exception as exc:  # pragma: no cover - UI defensive handling
            session_state.store_last_request_response(
                None,
                {
                    "ok": False,
                    "status_message": "The request could not be completed.",
                    "warnings": [],
                    "items": [],
                    "mode_used": st.session_state.get(SessionKeys.MODE),
                    "fallback_used": False,
                    "fallback_reason": None,
                    "debug": {},
                },
                controller_warnings=[],
            )
            render_setup_issue_panel(present_runtime_exception(exc))

    last_response = session_state.get_last_response()
    if last_response is None:
        render_empty_results_hint()
        _render_bootstrap_summary(app_status)
        return

    response_for_presenter = dict(last_response)
    merged_warnings = list(last_response.get("warnings") or []) + session_state.get_last_controller_warnings()
    response_for_presenter["warnings"] = merged_warnings

    render_started = perf_counter()
    presenter_started = perf_counter()
    presented = present_recommendation_response(response_for_presenter)
    presenter_ms = round((perf_counter() - presenter_started) * 1000.0, 3)

    status_started = perf_counter()
    render_response_status(presented)
    status_render_ms = round((perf_counter() - status_started) * 1000.0, 3)

    card_render_ms = 0.0
    card_started = perf_counter()
    cards = presented.get("cards") or []
    if cards:
        render_recommendation_cards(cards)
    card_render_ms = round((perf_counter() - card_started) * 1000.0, 3)

    debug_payload = presented.get("debug") if isinstance(presented.get("debug"), dict) else {}
    timings = debug_payload.get("timings_ms") if isinstance(debug_payload.get("timings_ms"), dict) else {}
    timings.update(
        {
            "ui_presenter_formatting_ms": presenter_ms,
            "ui_status_render_ms": status_render_ms,
            "ui_cards_render_ms": card_render_ms,
            "ui_render_total_ms": round((perf_counter() - render_started) * 1000.0, 3),
        }
    )
    debug_payload["timings_ms"] = timings
    presented["debug"] = debug_payload

    _render_last_request_summary()
    _render_bootstrap_summary(app_status)
    _render_debug_panel(app_status, presented)


def _render_last_request_summary() -> None:
    last_request = session_state.get_last_request()
    if not last_request:
        return
    with st.expander("Last Request Context", expanded=False):
        st.json(last_request)


def _render_bootstrap_summary(app_status: dict[str, Any]) -> None:
    artifacts_summary = app_status.get("artifacts_summary") or {}
    with st.expander("Bootstrap Summary", expanded=False):
        st.json(artifacts_summary)
        validation_report = app_status.get("validation_report")
        if validation_report:
            st.caption("Startup validation report")
            st.json(validation_report)


def _render_debug_panel(app_status: dict[str, Any], presented_response: dict[str, Any]) -> None:
    if not bool(st.session_state.get(SessionKeys.DEBUG_ENABLED, False)):
        return
    with st.expander("Debug Panel", expanded=True):
        st.write("Startup ready:", bool(app_status.get("startup_ready")))
        st.write("Mode used:", presented_response.get("mode_used"))
        st.write("Fallback used:", bool(presented_response.get("fallback_used")))
        st.write("Fallback reason:", presented_response.get("fallback_reason"))
        st.write("Cards rendered:", len(presented_response.get("cards") or []))
        startup_timing = app_status.get("startup_timing_ms")
        if isinstance(startup_timing, dict) and startup_timing:
            st.caption("Startup timing (ms)")
            st.json(startup_timing)

        last_request = session_state.get_last_request()
        if last_request:
            st.caption("Last request payload")
            st.json(last_request)

        last_response = session_state.get_last_response()
        if last_response:
            st.caption("Last raw response payload")
            st.json(last_response)

        debug_payload = presented_response.get("debug") or {}
        timings = debug_payload.get("timings_ms") if isinstance(debug_payload.get("timings_ms"), dict) else {}
        if timings:
            st.caption("Request timing breakdown (ms)")
            st.json(timings)

        limits = debug_payload.get("effective_limits") or debug_payload.get("performance_limits")
        if isinstance(limits, dict) and limits:
            st.caption("Effective performance limits")
            st.json(limits)

        if debug_payload:
            st.caption("Response debug payload")
            st.json(debug_payload)
