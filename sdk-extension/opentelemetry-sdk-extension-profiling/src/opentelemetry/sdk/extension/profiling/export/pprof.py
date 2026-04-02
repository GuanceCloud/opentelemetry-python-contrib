from __future__ import annotations

import os
from itertools import count

from opentelemetry.sdk.extension.profiling.environment_variables import (
    OTEL_PYTHON_PROFILING_PPROF_PATH,
)
from opentelemetry.sdk.extension.profiling.export.result import (
    ProfileExportResult,
)


class PPROFProfileExporter:
    def __init__(self, *, directory: str | None = None) -> None:
        self._directory = directory or os.environ.get(
            OTEL_PYTHON_PROFILING_PPROF_PATH, "otel-profiles"
        )
        os.makedirs(os.path.dirname(self._directory) or ".", exist_ok=True)
        self._counter = count(0)
        self._pid = os.getpid()

    def export(self, payload: bytes) -> ProfileExportResult:
        filename = (
            f"{self._directory}.{self._pid}.{next(self._counter)}.pprof"
        )
        with open(filename, "wb") as handle:
            handle.write(payload)
        return ProfileExportResult.SUCCESS

    def shutdown(self) -> None:
        return None
