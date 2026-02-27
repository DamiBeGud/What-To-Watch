from __future__ import annotations

from typing import Any, Optional

from src.application.ports.repositories import UserProfileRecord

from ._base import coerce_list, safe_float, safe_int


def _coerce_int_tuple(values: Any) -> tuple[int, ...]:
    out: list[int] = []
    for raw in coerce_list(values):
        coerced = safe_int(raw)
        if coerced is None:
            continue
        out.append(coerced)
    return tuple(out)


def _coerce_str_tuple(values: Any) -> tuple[str, ...]:
    out: list[str] = []
    for raw in coerce_list(values):
        text = str(raw).strip()
        if not text:
            continue
        out.append(text)
    return tuple(out)


class UserProfileRepositoryImpl:
    """Repository for compact exported user-profile artifacts used by returning-user mode."""

    def __init__(self, user_profiles_df: Any, *, source_path: Optional[str]) -> None:
        self._source_path = source_path
        profiles_by_user_id: dict[int, UserProfileRecord] = {}

        if user_profiles_df is not None:
            for row in user_profiles_df.itertuples(index=False):
                user_id = safe_int(getattr(row, "userId", None))
                if user_id is None:
                    continue
                profiles_by_user_id[user_id] = UserProfileRecord(
                    user_id=user_id,
                    train_interaction_count=safe_int(getattr(row, "train_interaction_count", None)),
                    positive_interaction_count=safe_int(getattr(row, "positive_interaction_count", None)),
                    train_mean_rating=safe_float(getattr(row, "train_mean_rating", None)),
                    seen_movie_ids=_coerce_int_tuple(getattr(row, "seen_movie_ids", None)),
                    positive_seed_movie_ids=_coerce_int_tuple(getattr(row, "positive_seed_movie_ids", None)),
                    preferred_genres=_coerce_str_tuple(getattr(row, "preferred_genres", None)),
                )

        self._profiles_by_user_id = profiles_by_user_id
        self._known_user_ids = sorted(profiles_by_user_id.keys())

    def count_profiles(self) -> int:
        return len(self._profiles_by_user_id)

    def get_source_path(self) -> Optional[str]:
        return self._source_path

    def known_user_ids(self, *, limit: Optional[int] = None) -> list[int]:
        if limit is None:
            return list(self._known_user_ids)
        return list(self._known_user_ids[: max(0, int(limit))])

    def get_profile(self, user_id: int) -> Optional[UserProfileRecord]:
        return self._profiles_by_user_id.get(int(user_id))

