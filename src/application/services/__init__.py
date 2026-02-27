from __future__ import annotations

from dataclasses import dataclass

from src.application.ports.repositories import RepositoryBundle
from src.core.config import AppConfig

from .explanation_service import ExplanationService
from .filter_service import FilterService
from .recommendation_service import RecommendationService
from .routing_service import RoutingService
from .search_service import SearchService


@dataclass(frozen=True)
class ApplicationServiceBundle:
    search_service: SearchService
    filter_service: FilterService
    explanation_service: ExplanationService
    routing_service: RoutingService
    recommendation_service: RecommendationService


def build_application_service_bundle(
    *,
    repositories: RepositoryBundle,
    config: AppConfig,
) -> ApplicationServiceBundle:
    search_service = SearchService(repositories=repositories, config=config)
    filter_service = FilterService()
    explanation_service = ExplanationService()
    routing_service = RoutingService()
    recommendation_service = RecommendationService(
        repositories=repositories,
        config=config,
        routing_service=routing_service,
        explanation_service=explanation_service,
        filter_service=filter_service,
    )
    return ApplicationServiceBundle(
        search_service=search_service,
        filter_service=filter_service,
        explanation_service=explanation_service,
        routing_service=routing_service,
        recommendation_service=recommendation_service,
    )


__all__ = [
    "ApplicationServiceBundle",
    "ExplanationService",
    "FilterService",
    "RecommendationService",
    "RoutingService",
    "SearchService",
    "build_application_service_bundle",
]

