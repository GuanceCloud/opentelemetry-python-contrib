# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import logging
from os import environ
from threading import Lock

from opentelemetry.sdk.extension.profiling.environment_variables import (
    OTEL_PROFILING_ENABLED,
)
from opentelemetry.sdk.extension.profiling.runtime import Profiler

_logger = logging.getLogger(__name__)
_bootstrap_lock = Lock()
_profiler: Profiler | None = None


def auto_start() -> None:
    enabled = _profiling_enabled()
    if not enabled:
        return
    global _profiler
    with _bootstrap_lock:
        if _profiler is not None:
            return
        try:
            _profiler = Profiler()
            _profiler.start()
        except Exception:
            _logger.exception("Failed to auto start OpenTelemetry profiling")
            _profiler = None


def get_profiler() -> Profiler | None:
    return _profiler


def stop_profiler(flush: bool = True) -> None:
    global _profiler
    with _bootstrap_lock:
        if _profiler is None:
            return
        _profiler.stop(flush=flush)
        _profiler = None


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


def _profiling_enabled() -> bool:
    return _parse_bool(environ.get(OTEL_PROFILING_ENABLED, "false"))
