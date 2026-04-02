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

import sys
import threading
from time import time_ns

from opentelemetry.sdk.extension.profiling.collector.base import (
    CapturedFrame,
    CapturedSample,
)
from opentelemetry.sdk.extension.profiling.context_bridge import ContextBridge
from opentelemetry.trace import INVALID_SPAN_CONTEXT


class StackCollector:
    def __init__(
        self,
        context_bridge: ContextBridge,
        max_frames: int = 64,
        include_trace_context: bool = True,
    ) -> None:
        self._context_bridge = context_bridge
        self._max_frames = max_frames
        self._include_trace_context = include_trace_context

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def capture(self) -> list[CapturedSample]:
        current_thread_id = threading.current_thread().ident
        active_threads = {
            thread.ident: thread.name
            for thread in threading.enumerate()
            if thread.ident is not None
        }
        timestamp_unix_nano = time_ns()
        samples: list[CapturedSample] = []

        for thread_id, frame in sys._current_frames().items():
            if thread_id == current_thread_id:
                continue

            frames: list[CapturedFrame] = []
            current = frame
            while current is not None and len(frames) < self._max_frames:
                code = current.f_code
                frames.append(
                    CapturedFrame(
                        function=code.co_name,
                        filename=code.co_filename,
                        lineno=current.f_lineno,
                    )
                )
                current = current.f_back

            if not frames:
                continue

            span_context = INVALID_SPAN_CONTEXT
            span_metadata = None
            if self._include_trace_context:
                span_metadata = self._context_bridge.span_metadata_for_thread(
                    thread_id
                )
                if span_metadata is not None:
                    span_context = span_metadata.span_context

            samples.append(
                CapturedSample(
                    timestamp_unix_nano=timestamp_unix_nano,
                    thread_id=thread_id,
                    thread_name=active_threads.get(
                        thread_id, f"thread-{thread_id}"
                    ),
                    frames=tuple(frames),
                    trace_id=span_context.trace_id,
                    span_id=span_context.span_id,
                    local_root_span_id=(
                        span_metadata.local_root_span_id
                        if span_metadata is not None
                        else span_context.span_id
                    ),
                    trace_type=(
                        span_metadata.trace_type if span_metadata else None
                    ),
                    trace_endpoint=(
                        span_metadata.trace_endpoint
                        if span_metadata
                        else None
                    ),
                    class_name=(
                        span_metadata.class_name if span_metadata else None
                    ),
                )
            )

        return samples
