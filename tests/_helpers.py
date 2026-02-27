from __future__ import annotations

import shutil
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from src.core.config import AppConfig
from src.core.dependencies import AppDependencies, initialize_app_dependencies


def runtime_dependencies_available() -> tuple[bool, str]:
    try:
        import numpy  # noqa: F401
        import pandas  # noqa: F401
    except ModuleNotFoundError as exc:
        return False, str(exc)
    return True, ""


def ensure_runtime_dependencies_or_skip(testcase: unittest.TestCase) -> None:
    ok, reason = runtime_dependencies_available()
    if not ok:
        testcase.skipTest(f"Runtime dependencies unavailable for integration/smoke tests: {reason}")


def build_dependencies_or_skip(
    testcase: unittest.TestCase,
    *,
    artifacts_dir: str = "artifacts",
) -> AppDependencies:
    ensure_runtime_dependencies_or_skip(testcase)
    dependencies = initialize_app_dependencies(
        AppConfig(
            artifacts_dir=artifacts_dir,
            debug_mode_default=True,
            require_user_profiles=True,
        )
    )
    if not dependencies.startup_ready:
        testcase.skipTest(
            "Dependencies did not initialize to ready state for this environment: "
            f"{dependencies.setup_user_message} | {dependencies.setup_developer_details}"
        )
    return dependencies


@contextmanager
def temporary_artifacts_copy(source_dir: str = "artifacts") -> Iterator[Path]:
    with TemporaryDirectory(prefix="task13_artifacts_") as tmp:
        src = Path(source_dir)
        dst = Path(tmp) / "artifacts"
        shutil.copytree(src, dst)
        yield dst
