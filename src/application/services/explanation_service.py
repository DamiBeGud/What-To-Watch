from __future__ import annotations

from typing import Optional, Sequence

from src.domain.enums import FallbackReason


class ExplanationService:
    """Centralizes plain-language reason and status text formatting for recommendation responses."""

    def genre_popularity_reason(self, genre: str) -> str:
        genre_label = str(genre or "selected genre")
        return f"Popular in genre '{genre_label}' (placeholder ranking for Task 10 service layer)"

    def global_popularity_reason(self, *, scenario: str, rating_count: Optional[int]) -> str:
        count_label = rating_count if rating_count is not None else "n/a"
        if scenario == "returning_user_fallback":
            return f"Popular overall (fallback for returning-user placeholder mode; count={count_label})"
        if scenario == "new_user_fallback":
            return f"Popular overall (cold-start fallback placeholder; count={count_label})"
        if scenario == "similar_movie_missing_source":
            return f"Popular overall (placeholder shown until a source title is selected; count={count_label})"
        if scenario == "similar_movie_missing_genres":
            return f"Popular overall (source movie has limited metadata; count={count_label})"
        return f"Popular overall (placeholder ranking; count={count_label})"

    def similar_movie_reason(self, *, source_title: str, overlap_genres: Sequence[str]) -> str:
        shown = ", ".join(str(genre) for genre in list(overlap_genres)[:2]) or "genre overlap"
        return f"Similar to '{source_title}' (shared genres: {shown})"

    def returning_user_status(self, *, user_id: Optional[int], fallback_used: bool) -> str:
        if user_id is not None and not fallback_used:
            return "Returning-user mode (placeholder): using user profile genres from exported `user_profiles_train`."
        if user_id is not None and fallback_used:
            return "Returning-user mode fallback: user profile signal was unavailable/weak, so global popular picks are shown."
        return "Returning-user mode fallback: no user selected yet, showing global popular picks."

    def new_user_status(self, *, fallback_used: bool) -> str:
        if not fallback_used:
            return "New-user mode (placeholder): using genre-aware popularity seeded by your selected genres/titles."
        return "New-user mode fallback: showing global popular picks while preference signal is weak."

    def similar_movie_status(self, *, source_title: Optional[str], fallback_reason: Optional[FallbackReason]) -> str:
        if fallback_reason == FallbackReason.MISSING_SOURCE_MOVIE:
            return "Similar-movie mode placeholder: select a title to see title-to-title examples."
        if fallback_reason == FallbackReason.MISSING_SOURCE_GENRES:
            return "Similar-movie mode fallback: source metadata was too limited for genre-overlap placeholder ranking."
        source_label = source_title or "the selected title"
        return f"Similar-movie mode (placeholder): showing genre-overlap examples for '{source_label}'."

    def warning_missing_returning_user_selection(self) -> str:
        return "No returning-user ID selected. Showing fallback picks."

    def warning_unknown_returning_user(self, user_id: int) -> str:
        return f"User ID {user_id} is not in the exported user profile artifact. Showing fallback picks."

    def warning_new_user_weak_signal(self, *, has_any_preferences: bool) -> str:
        if not has_any_preferences:
            return "Not enough preferences selected yet for personalized candidates. Showing global popular picks."
        return "Selected preferences did not yield enough genre-popularity candidates. Falling back to global popular picks."

    def warning_pick_source_movie(self) -> str:
        return "Pick a source movie to generate similar-movie results."

    def warning_source_missing_genres(self) -> str:
        return "Source movie has no genre metadata; using global fallback placeholder results."

