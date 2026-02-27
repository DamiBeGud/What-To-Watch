from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict


def _get_env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class AppConfig:
    artifacts_dir: str = "artifacts"
    page_title: str = "Movie Recommendation App"
    page_icon: str = "🎬"
    default_mode: str = "returning_user"
    default_top_n: int = 10
    min_top_n: int = 5
    max_top_n: int = 30
    title_search_limit: int = 25
    user_select_limit: int = 500
    debug_mode_default: bool = False
    require_user_profiles: bool = True
    candidate_pool_multiplier: int = 3
    candidate_pool_cap: int = 300
    similar_scan_limit: int = 25000

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "artifacts_dir": self.artifacts_dir,
            "page_title": self.page_title,
            "default_mode": self.default_mode,
            "default_top_n": self.default_top_n,
            "min_top_n": self.min_top_n,
            "max_top_n": self.max_top_n,
            "title_search_limit": self.title_search_limit,
            "user_select_limit": self.user_select_limit,
            "debug_mode_default": self.debug_mode_default,
            "require_user_profiles": self.require_user_profiles,
            "candidate_pool_multiplier": self.candidate_pool_multiplier,
            "candidate_pool_cap": self.candidate_pool_cap,
            "similar_scan_limit": self.similar_scan_limit,
        }


def load_app_config() -> AppConfig:
    return AppConfig(
        artifacts_dir=os.getenv("ARTIFACTS_DIR", "artifacts"),
        page_title=os.getenv("APP_PAGE_TITLE", "Movie Recommendation App"),
        page_icon=os.getenv("APP_PAGE_ICON", "🎬"),
        default_mode=os.getenv("APP_DEFAULT_MODE", "returning_user"),
        default_top_n=_get_env_int("APP_DEFAULT_TOP_N", 10),
        min_top_n=_get_env_int("APP_MIN_TOP_N", 5),
        max_top_n=_get_env_int("APP_MAX_TOP_N", 30),
        title_search_limit=_get_env_int("APP_TITLE_SEARCH_LIMIT", 25),
        user_select_limit=_get_env_int("APP_USER_SELECT_LIMIT", 500),
        debug_mode_default=_get_env_bool("APP_DEBUG_MODE", False),
        require_user_profiles=_get_env_bool("APP_REQUIRE_USER_PROFILES", True),
        candidate_pool_multiplier=_get_env_int("APP_CANDIDATE_POOL_MULTIPLIER", 3),
        candidate_pool_cap=_get_env_int("APP_CANDIDATE_POOL_CAP", 300),
        similar_scan_limit=_get_env_int("APP_SIMILAR_SCAN_LIMIT", 25000),
    )
