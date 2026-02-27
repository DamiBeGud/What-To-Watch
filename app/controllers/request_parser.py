from __future__ import annotations

from typing import Any, Optional, Tuple

from src.core.config import AppConfig


def _safe_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_int_list(values: Any) -> list[int]:
    if not isinstance(values, list):
        return []
    out: list[int] = []
    seen: set[int] = set()
    for value in values:
        coerced = _safe_int(value)
        if coerced is None or coerced in seen:
            continue
        seen.add(coerced)
        out.append(coerced)
    return out


def _coerce_str_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _parse_year_range(raw_year_range: Any) -> tuple[int, int] | tuple[()]:
    if not isinstance(raw_year_range, (list, tuple)) or len(raw_year_range) != 2:
        return ()
    year_low = _safe_int(raw_year_range[0])
    year_high = _safe_int(raw_year_range[1])
    if year_low is None or year_high is None:
        return ()
    if year_low > year_high:
        year_low, year_high = year_high, year_low
    return (year_low, year_high)


def _normalize_mode(mode: str, *, config: AppConfig) -> tuple[str, list[str]]:
    warnings: list[str] = []
    mode_value = str(mode or config.default_mode)
    if mode_value not in {"returning_user", "new_user", "similar_movie"}:
        mode_value = config.default_mode
        if mode_value not in {"returning_user", "new_user", "similar_movie"}:
            mode_value = "returning_user"
        warnings.append("Unknown mode received, so the request was routed to returning-user mode.")
    return mode_value, warnings


def build_recommendation_request(
    *,
    mode: str,
    shared_filters: dict[str, Any],
    mode_inputs: dict[str, Any],
    config: AppConfig,
) -> Tuple[dict[str, Any], list[str]]:
    top_n = _safe_int(shared_filters.get("top_n"))
    if top_n is None:
        top_n = config.default_top_n
    top_n = max(config.min_top_n, min(top_n, config.max_top_n))

    mode_value, warnings = _normalize_mode(mode, config=config)
    filters = {
        "genres": _coerce_str_list(shared_filters.get("genres") or []),
        "year_range": _parse_year_range(shared_filters.get("year_range")),
    }
    if filters["year_range"] and filters["year_range"][0] == filters["year_range"][1]:
        warnings.append("Year filter is set to a single year, which may narrow results significantly.")

    request: dict[str, Any] = {
        "mode": mode_value,
        "top_n": top_n,
        "filters": filters,
    }

    if mode_value == "returning_user":
        manual_user_raw = str(mode_inputs.get("manual_user_id") or "").strip()
        manual_user_id = _safe_int(mode_inputs.get("manual_user_id"))
        selected_user_id = _safe_int(mode_inputs.get("selected_user_id"))
        if manual_user_raw and manual_user_id is None:
            warnings.append("Manual user ID was not valid, so the selected demo user was used instead.")

        user_id = manual_user_id if manual_user_id is not None else selected_user_id
        request["user_id"] = user_id

        if manual_user_id is not None and selected_user_id is not None and manual_user_id != selected_user_id:
            warnings.append("Manual user ID override applied for this request.")
        if user_id is None:
            warnings.append("No returning-user profile was selected, so fallback recommendations will be used.")

    elif mode_value == "new_user":
        liked_movie_ids = _coerce_int_list(mode_inputs.get("liked_movie_ids"))
        genre_preferences = _coerce_str_list(mode_inputs.get("genre_preferences"))
        search_query = str(mode_inputs.get("title_query") or "").strip()
        search_match_count = _safe_int(mode_inputs.get("search_match_count"))
        search_match_count = search_match_count if search_match_count is not None else 0

        request["liked_movie_ids"] = liked_movie_ids
        request["genre_preferences"] = genre_preferences

        if search_query and search_match_count == 0:
            warnings.append("No title matches were found for your search. Try another spelling or broader title text.")
        if not liked_movie_ids and not genre_preferences:
            warnings.append(
                "Add a few liked titles or genres for stronger recommendations. The app will otherwise use fallback picks."
            )

    elif mode_value == "similar_movie":
        source_movie_id = _safe_int(mode_inputs.get("source_movie_id"))
        search_query = str(mode_inputs.get("title_query") or "").strip()
        search_match_count = _safe_int(mode_inputs.get("search_match_count"))
        search_match_count = search_match_count if search_match_count is not None else 0

        request["source_movie_id"] = source_movie_id
        if search_query and search_match_count == 0:
            warnings.append("No matching source title was found. Try a different spelling or shorter query.")
        if source_movie_id is None:
            warnings.append("Select a source title to run similar-movie recommendations.")

    return request, warnings
