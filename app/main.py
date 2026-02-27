from __future__ import annotations

import json
from typing import Any

import streamlit as st

from app.views.home_view import render_home_view
from src.core.config import AppConfig, load_app_config
from src.core.dependencies import AppDependencies, initialize_app_dependencies


@st.cache_resource(show_spinner="Initializing app dependencies and validating artifacts...")
def _get_app_dependencies_cached(config: AppConfig) -> AppDependencies:
    return initialize_app_dependencies(config)


@st.cache_data(show_spinner=False)
def _get_ui_options_cached(status_signature: str, _serving_api: Any) -> dict[str, Any]:
    # `_serving_api` is intentionally prefixed with `_` so Streamlit excludes it from cache hashing.
    # The signature string is derived from startup status / validation metadata to invalidate when artifacts change.
    _ = status_signature
    return _serving_api.get_ui_options()


def _build_status_signature(app_status: dict[str, Any]) -> str:
    serializable = {
        "startup_ready": app_status.get("startup_ready"),
        "validation_report": app_status.get("validation_report"),
        "artifacts_summary": app_status.get("artifacts_summary"),
        "setup_user_message": app_status.get("setup_user_message"),
        "startup_timing_ms": app_status.get("startup_timing_ms"),
    }
    return json.dumps(serializable, sort_keys=True, default=str)


def main() -> None:
    config = load_app_config()
    st.set_page_config(
        page_title=config.page_title,
        page_icon=config.page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    dependencies = _get_app_dependencies_cached(config)
    app_status = dependencies.serving_api.get_app_status()
    status_signature = _build_status_signature(app_status)
    ui_options = _get_ui_options_cached(status_signature, dependencies.serving_api)

    render_home_view(
        config=config,
        serving_api=dependencies.serving_api,
        app_status=app_status,
        ui_options=ui_options,
        status_signature=status_signature,
    )


if __name__ == "__main__":
    main()
