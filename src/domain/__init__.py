"""Domain request/response contracts for the recommendation app."""

from .enums import FallbackReason, RecommendationExecutionMode, RecommendationMode
from .requests import RecommendationFilters, RecommendationRequest
from .responses import RecommendationItem, RecommendationResponse

__all__ = [
    "FallbackReason",
    "RecommendationExecutionMode",
    "RecommendationFilters",
    "RecommendationItem",
    "RecommendationMode",
    "RecommendationRequest",
    "RecommendationResponse",
]

