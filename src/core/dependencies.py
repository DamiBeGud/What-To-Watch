from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Optional

from src.application.services import ApplicationServiceBundle, build_application_service_bundle
from src.core.config import AppConfig
from src.infrastructure.loaders.artifact_loader import ArtifactLoadError, load_runtime_artifacts
from src.infrastructure.loaders.startup_validator import (
    StartupValidationError,
    StartupValidationReport,
    validate_startup_artifacts,
)
from src.infrastructure.repositories import ArtifactRepositoryBundle, build_artifact_repository_bundle
from src.serving.api import ServingAPI


@dataclass
class AppDependencies:
    config: AppConfig
    serving_api: ServingAPI
    repository_bundle: Optional[ArtifactRepositoryBundle]
    service_bundle: Optional[ApplicationServiceBundle]
    startup_ready: bool
    setup_user_message: Optional[str]
    setup_developer_details: Optional[str]
    validation_report: Optional[dict[str, Any]]
    startup_timing_ms: dict[str, float]


def _report_to_dict(report: Optional[StartupValidationReport]) -> Optional[dict[str, Any]]:
    if report is None:
        return None
    return report.to_dict()


def initialize_app_dependencies(config: AppConfig) -> AppDependencies:
    startup_started = perf_counter()
    validation_report: Optional[StartupValidationReport] = None
    runtime_artifacts: Optional[dict[str, Any]] = None
    repository_bundle: Optional[ArtifactRepositoryBundle] = None
    service_bundle: Optional[ApplicationServiceBundle] = None
    setup_user_message: Optional[str] = None
    setup_developer_details: Optional[str] = None
    startup_timing_ms: dict[str, float] = {}

    stage_started = perf_counter()
    try:
        validation_report = validate_startup_artifacts(
            config.artifacts_dir,
            require_user_profiles=config.require_user_profiles,
        )
    except StartupValidationError as exc:
        startup_timing_ms["validation_ms"] = round((perf_counter() - stage_started) * 1000.0, 3)
        setup_user_message = (
            "Setup issue: required artifacts are missing or invalid. "
            "Run the offline artifact export/validation steps before starting the app."
        )
        setup_developer_details = str(exc)
    else:
        startup_timing_ms["validation_ms"] = round((perf_counter() - stage_started) * 1000.0, 3)
        try:
            stage_started = perf_counter()
            runtime_artifacts = load_runtime_artifacts(config.artifacts_dir)
            startup_timing_ms["runtime_artifact_load_ms"] = round((perf_counter() - stage_started) * 1000.0, 3)

            stage_started = perf_counter()
            repository_bundle = build_artifact_repository_bundle(
                runtime_artifacts,
                artifacts_dir=config.artifacts_dir,
            )
            startup_timing_ms["repository_bundle_build_ms"] = round((perf_counter() - stage_started) * 1000.0, 3)

            stage_started = perf_counter()
            service_bundle = build_application_service_bundle(
                repositories=repository_bundle,
                config=config,
            )
            startup_timing_ms["service_bundle_build_ms"] = round((perf_counter() - stage_started) * 1000.0, 3)
        except ArtifactLoadError as exc:
            if "runtime_artifact_load_ms" not in startup_timing_ms:
                startup_timing_ms["runtime_artifact_load_ms"] = round((perf_counter() - stage_started) * 1000.0, 3)
            setup_user_message = (
                "Setup issue: artifacts passed startup checks, but runtime loading failed. "
                "Check logs/details and regenerate artifacts if needed."
            )
            setup_developer_details = str(exc)
        except Exception as exc:  # pragma: no cover - defensive startup wiring wrapper
            stage_name = "repository_or_service_build_ms"
            if "repository_bundle_build_ms" not in startup_timing_ms:
                stage_name = "repository_bundle_build_ms"
            elif "service_bundle_build_ms" not in startup_timing_ms:
                stage_name = "service_bundle_build_ms"
            startup_timing_ms[stage_name] = round((perf_counter() - stage_started) * 1000.0, 3)
            setup_user_message = (
                "Setup issue: artifacts loaded, but application service wiring failed. "
                "Check logs/details and fix the service layer setup."
            )
            setup_developer_details = f"{type(exc).__name__}: {exc}"

    startup_timing_ms["total_startup_ms"] = round((perf_counter() - startup_started) * 1000.0, 3)

    stage_started = perf_counter()
    serving_api = ServingAPI(
        config=config,
        repositories=repository_bundle,
        services=service_bundle,
        validation_report=_report_to_dict(validation_report),
        startup_ready=(repository_bundle is not None and service_bundle is not None and setup_user_message is None),
        setup_user_message=setup_user_message,
        setup_developer_details=setup_developer_details,
        startup_timing_ms=dict(startup_timing_ms),
    )
    startup_timing_ms["serving_api_wiring_ms"] = round((perf_counter() - stage_started) * 1000.0, 3)

    return AppDependencies(
        config=config,
        serving_api=serving_api,
        repository_bundle=repository_bundle,
        service_bundle=service_bundle,
        startup_ready=serving_api.is_ready(),
        setup_user_message=setup_user_message,
        setup_developer_details=setup_developer_details,
        validation_report=_report_to_dict(validation_report),
        startup_timing_ms=startup_timing_ms,
    )
