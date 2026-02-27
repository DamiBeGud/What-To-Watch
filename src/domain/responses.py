from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .enums import FallbackReason, RecommendationExecutionMode, RecommendationMode


@dataclass(frozen=True)
class RecommendationItem:
    movie_id: int
    title: str
    year: Optional[int]
    genres: str
    score: Optional[float]
    reason: str
    source_label: str

    def to_ui_dict(self) -> dict[str, Any]:
        return {
            "movieId": self.movie_id,
            "title": self.title,
            "year": self.year,
            "genres": self.genres,
            "score": self.score,
            "reason": self.reason,
            "source_label": self.source_label,
        }


@dataclass(frozen=True)
class RecommendationResponse:
    ok: bool
    mode_requested: RecommendationMode
    mode_used: RecommendationExecutionMode
    fallback_used: bool
    fallback_reason: Optional[FallbackReason]
    status_message: str
    warnings: tuple[str, ...] = ()
    items: tuple[RecommendationItem, ...] = ()
    debug: dict[str, Any] = field(default_factory=dict)

    def to_ui_dict(self) -> dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "mode_requested": self.mode_requested.value,
            "mode_used": self.mode_used.value,
            "fallback_used": bool(self.fallback_used),
            "fallback_reason": self.fallback_reason.value if self.fallback_reason is not None else None,
            "status_message": self.status_message,
            "warnings": [str(w) for w in self.warnings],
            "items": [item.to_ui_dict() for item in self.items],
            "debug": dict(self.debug),
        }

