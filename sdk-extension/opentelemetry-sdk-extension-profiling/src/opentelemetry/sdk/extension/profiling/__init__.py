from opentelemetry.sdk.extension.profiling.bootstrap import (
    auto_start,
    get_profiler,
    stop_profiler,
)
from opentelemetry.sdk.extension.profiling.runtime import Profiler
from opentelemetry.sdk.extension.profiling.version import __version__

__all__ = [
    "Profiler",
    "__version__",
    "auto_start",
    "get_profiler",
    "stop_profiler",
]
