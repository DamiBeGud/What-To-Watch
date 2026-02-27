from __future__ import annotations

from enum import Enum


class RecommendationMode(str, Enum):
    RETURNING_USER = "returning_user"
    NEW_USER = "new_user"
    SIMILAR_MOVIE = "similar_movie"


class RecommendationExecutionMode(str, Enum):
    RETURNING_USER = "returning_user"
    NEW_USER = "new_user"
    SIMILAR_MOVIE = "similar_movie"
    COLD_START_FALLBACK = "cold_start_fallback"


class FallbackReason(str, Enum):
    MISSING_OR_WEAK_USER_PROFILE = "missing_or_weak_user_profile"
    INSUFFICIENT_PREFERENCE_SIGNAL = "insufficient_preference_signal"
    MISSING_SOURCE_MOVIE = "missing_source_movie"
    MISSING_SOURCE_GENRES = "missing_source_genres"
    REPOSITORIES_UNAVAILABLE = "repositories_unavailable"

