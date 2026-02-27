from __future__ import annotations

from typing import Any, Dict


def present_setup_issue(app_status: dict[str, Any]) -> dict[str, Any]:
    validation_report = app_status.get("validation_report") or {}
    report_notes = validation_report.get("notes") if isinstance(validation_report, dict) else []
    report_warnings = validation_report.get("warnings") if isinstance(validation_report, dict) else []
    return {
        "title": "Setup Issue",
        "user_message": app_status.get("setup_user_message")
        or "The app could not initialize its serving artifacts.",
        "developer_details": app_status.get("setup_developer_details"),
        "notes": [str(note) for note in (report_notes or [])],
        "warnings": [str(w) for w in (report_warnings or [])],
    }


def present_runtime_exception(exc: Exception) -> dict[str, Any]:
    return {
        "title": "Runtime Error",
        "user_message": "The UI request could not be completed. Try again or check the developer details.",
        "developer_details": "{}: {}".format(type(exc).__name__, exc),
        "notes": [],
        "warnings": [],
    }

