from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from src.infrastructure.loaders.artifact_loader import ArtifactLoadError, PROVENANCE_FILENAME, read_json_file


class ArtifactManifestRepositoryImpl:
    """Repository exposing manifest, selected params, and provenance metadata."""

    def __init__(
        self,
        *,
        artifacts_dir: str,
        manifest_entries: list[dict[str, Any]],
        selected_params: dict[str, Any],
        provenance: Optional[dict[str, Any]] = None,
    ) -> None:
        self._artifacts_dir = str(artifacts_dir)
        self._manifest_entries = [dict(entry) for entry in manifest_entries]
        self._selected_params = dict(selected_params)
        self._provenance = dict(provenance) if isinstance(provenance, dict) else None

    @classmethod
    def from_runtime_artifacts(cls, runtime_artifacts: dict[str, Any], *, artifacts_dir: str) -> "ArtifactManifestRepositoryImpl":
        provenance: Optional[dict[str, Any]] = None
        provenance_path = Path(artifacts_dir) / PROVENANCE_FILENAME
        try:
            raw = read_json_file(provenance_path)
        except ArtifactLoadError:
            raw = None
        if isinstance(raw, dict):
            provenance = raw

        manifest_entries = runtime_artifacts.get("manifest") or []
        selected_params = runtime_artifacts.get("selected_params") or {}
        return cls(
            artifacts_dir=artifacts_dir,
            manifest_entries=manifest_entries,
            selected_params=selected_params,
            provenance=provenance,
        )

    def get_artifacts_dir(self) -> str:
        return self._artifacts_dir

    def get_manifest_entries(self) -> list[dict[str, Any]]:
        return [dict(entry) for entry in self._manifest_entries]

    def get_selected_params(self) -> dict[str, Any]:
        return dict(self._selected_params)

    def get_provenance(self) -> Optional[dict[str, Any]]:
        return dict(self._provenance) if isinstance(self._provenance, dict) else None

