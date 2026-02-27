from __future__ import annotations

from typing import Any, Optional


MODE_LABELS = {
    "returning_user": "Returning User",
    "new_user": "New User / Cold Start",
    "similar_movie": "Similar Movie",
    "cold_start_fallback": "Cold-Start Fallback",
}

FALLBACK_REASON_LABELS = {
    "missing_or_weak_user_profile": "The selected user profile did not provide enough signal.",
    "insufficient_preference_signal": "The selected preferences were too weak for strong personalization.",
    "missing_source_movie": "No source movie was selected.",
    "missing_source_genres": "The source movie is missing enough genre metadata.",
    "repositories_unavailable": "Required recommendation repositories are not available.",
}


def _as_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_warning_list(raw_warnings: Any) -> list[str]:
    if not isinstance(raw_warnings, list):
        return []
    normalized: list[str] = []
    seen: set[str] = set()
    for warning in raw_warnings:
        text = str(warning).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _build_fallback_summary(*, fallback_used: bool, fallback_reason: Optional[str]) -> Optional[str]:
    if not fallback_used:
        return None
    if fallback_reason:
        reason_text = FALLBACK_REASON_LABELS.get(fallback_reason, fallback_reason.replace("_", " "))
        return f"Fallback used: {reason_text}"
    return "Fallback used: the app switched to a safer recommendation path."


def _derive_empty_state(
    *,
    ok: bool,
    status_message: str,
    mode_used: str,
    fallback_reason: Optional[str],
    warnings: list[str],
    debug: dict[str, Any],
) -> dict[str, str]:
    if not ok:
        return {
            "kind": "error",
            "message": status_message or "The recommendation request could not be completed.",
            "action": "Check setup details in the debug panel or bootstrap report.",
        }

    lowered_warnings = " ".join(warnings).lower()
    if "no title matches" in lowered_warnings or "no matching source title" in lowered_warnings:
        return {
            "kind": "no_title_match",
            "message": "No matching title was found for the current search.",
            "action": "Try a shorter title query or adjust the spelling.",
        }

    if mode_used == "similar_movie" and fallback_reason == "missing_source_movie":
        return {
            "kind": "no_source_selected",
            "message": "A source movie is required for similar-movie recommendations.",
            "action": "Search for a title and select it before running recommendations.",
        }

    if fallback_reason == "insufficient_preference_signal":
        return {
            "kind": "insufficient_preferences",
            "message": "Not enough preferences were available to generate targeted recommendations.",
            "action": "Add liked titles or genre preferences, then run the request again.",
        }

    before_count = _as_int(debug.get("items_before_filters")) or 0
    after_count = _as_int(debug.get("items_after_filters")) or 0
    if before_count > 0 and after_count == 0:
        return {
            "kind": "empty_after_filters",
            "message": "No recommendations remained after filters were applied.",
            "action": "Widen genres or year range to see more results.",
        }

    return {
        "kind": "empty",
        "message": "No recommendations are available for this request yet.",
        "action": "Try a different mode or provide additional input.",
    }


def present_recommendation_response(response: dict[str, Any]) -> dict[str, Any]:
    raw_items = response.get("items") or []
    cards: list[dict[str, Any]] = []
    missing_metadata_count = 0

    for rank, item in enumerate(raw_items, start=1):
        title = str(item.get("title") or "").strip() or "Unknown title"
        year = _as_int(item.get("year"))
        genres = str(item.get("genres") or "").strip() or "(no genres listed)"
        reason = str(item.get("reason") or "").strip() or "Recommended based on your selected mode."

        metadata_notes: list[str] = []
        if title == "Unknown title":
            metadata_notes.append("Title metadata unavailable.")
        if year is None:
            metadata_notes.append("Year metadata unavailable.")
        if genres == "(no genres listed)":
            metadata_notes.append("Genre metadata unavailable.")

        if metadata_notes:
            missing_metadata_count += 1

        poster_url = str(item.get("poster_url") or "").strip()
        cards.append(
            {
                "rank": rank,
                "movieId": item.get("movieId"),
                "title": title,
                "year": year,
                "genres": genres,
                "reason": reason,
                "score": item.get("score"),
                "source_label": item.get("source_label"),
                "poster_url": poster_url,
                "poster_placeholder": "Poster unavailable in this demo artifact bundle.",
                "metadata_notes": "; ".join(metadata_notes) if metadata_notes else "",
            }
        )

    warnings = _normalize_warning_list(response.get("warnings") or [])
    mode_used = str(response.get("mode_used") or response.get("mode_requested") or "unknown")
    fallback_used = bool(response.get("fallback_used"))
    fallback_reason_raw = response.get("fallback_reason")
    fallback_reason = str(fallback_reason_raw) if fallback_reason_raw else None
    status_message = str(response.get("status_message") or "Ready.")
    ok = bool(response.get("ok", True))
    debug = response.get("debug") if isinstance(response.get("debug"), dict) else {}

    metadata_notice = None
    if missing_metadata_count > 0:
        metadata_notice = (
            f"{missing_metadata_count} recommendation card(s) had missing metadata. "
            "Placeholders are shown so results remain visible."
        )

    empty_state = None
    if not cards:
        empty_state = _derive_empty_state(
            ok=ok,
            status_message=status_message,
            mode_used=mode_used,
            fallback_reason=fallback_reason,
            warnings=warnings,
            debug=debug,
        )

    return {
        "ok": ok,
        "status_message": status_message,
        "warnings": warnings,
        "mode_used": mode_used,
        "mode_label": MODE_LABELS.get(mode_used, mode_used.replace("_", " ").title()),
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "fallback_summary": _build_fallback_summary(
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        ),
        "cards": cards,
        "metadata_notice": metadata_notice,
        "empty_state": empty_state,
        "debug": debug,
    }
