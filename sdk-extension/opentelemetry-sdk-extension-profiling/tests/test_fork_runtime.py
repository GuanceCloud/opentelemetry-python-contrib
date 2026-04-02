from __future__ import annotations

import asyncio.events
import os
import threading

import pytest

import opentelemetry.context as context_api
from opentelemetry.sdk.extension.profiling.collector.lock import (
    ThreadingLockCollector,
)
from opentelemetry.sdk.extension.profiling.context_bridge import ContextBridge
from opentelemetry.sdk.extension.profiling.runtime import Profiler


class _NoopExporter:
    def export(self, request) -> None:  # noqa: ANN001
        del request

    def shutdown(self) -> None:
        return None


class _FakeContextBridge:
    def __init__(self) -> None:
        self.start_calls = 0
        self.stop_calls = 0
        self.reset_calls = 0

    def start(self) -> None:
        self.start_calls += 1

    def stop(self) -> None:
        self.stop_calls += 1

    def reset_after_fork(self) -> None:
        self.reset_calls += 1


class _FakeCollector:
    def __init__(self) -> None:
        self.start_calls = 0
        self.stop_calls = 0
        self.reset_calls = 0

    def start(self) -> None:
        self.start_calls += 1

    def stop(self) -> None:
        self.stop_calls += 1

    def capture(self) -> list:
        return []

    def reset_after_fork(self) -> None:
        self.reset_calls += 1


class _FakeScheduler:
    def __init__(self) -> None:
        self.start_calls = 0
        self.stop_calls = 0
        self.join_calls = 0
        self.reset_calls = 0

    def start(self) -> None:
        self.start_calls += 1

    def stop(self) -> None:
        self.stop_calls += 1

    def join(self) -> None:
        self.join_calls += 1

    def reset_after_fork(self) -> None:
        self.reset_calls += 1


def test_context_bridge_reset_after_fork_restores_original_hooks():
    bridge = ContextBridge()
    original_attach = context_api.attach
    original_detach = context_api.detach
    original_handle_run = asyncio.events.Handle._run

    bridge.start()
    assert context_api.attach is not original_attach
    assert context_api.detach is not original_detach
    assert asyncio.events.Handle._run is not original_handle_run

    bridge.reset_after_fork()

    assert context_api.attach is original_attach
    assert context_api.detach is original_detach
    assert asyncio.events.Handle._run is original_handle_run
    assert not bridge._started


def test_threading_lock_collector_reset_after_fork_restores_lock_factory():
    collector = ThreadingLockCollector(ContextBridge())
    original_lock_factory = threading.Lock

    collector.start()
    assert threading.Lock is not original_lock_factory

    collector.reset_after_fork()

    assert threading.Lock is original_lock_factory
    assert not collector._started


@pytest.mark.skipif(
    not hasattr(os, "fork"),
    reason="fork is not available on this platform",
)
def test_profiler_restarts_in_child_process_after_fork():
    profiler = Profiler(
        exporter=_NoopExporter(),
        sample_interval=3600.0,
        export_interval=3600.0,
    )
    fake_context_bridge = _FakeContextBridge()
    fake_collector = _FakeCollector()
    fake_scheduler = _FakeScheduler()
    profiler._context_bridge = fake_context_bridge
    profiler._collectors = [fake_collector]
    profiler._scheduler = fake_scheduler

    profiler.start()

    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        payload = "|".join(
            [
                str(int(profiler._started)),
                str(int(profiler.__class__._active_instance is profiler)),
                str(fake_context_bridge.start_calls),
                str(fake_context_bridge.reset_calls),
                str(fake_collector.start_calls),
                str(fake_collector.reset_calls),
                str(fake_scheduler.start_calls),
                str(fake_scheduler.reset_calls),
                str(len(profiler._active_collectors)),
            ]
        )
        os.write(write_fd, payload.encode("utf-8"))
        os.close(write_fd)
        profiler.stop(flush=False)
        os._exit(0)

    os.close(write_fd)
    payload = os.read(read_fd, 512).decode("utf-8")
    os.close(read_fd)
    _, status = os.waitpid(pid, 0)
    profiler.stop(flush=False)

    (
        started,
        active_is_self,
        context_start_calls,
        context_reset_calls,
        collector_start_calls,
        collector_reset_calls,
        scheduler_start_calls,
        scheduler_reset_calls,
        active_collectors,
    ) = (int(value) for value in payload.split("|"))

    assert os.WIFEXITED(status)
    assert os.WEXITSTATUS(status) == 0
    assert started == 1
    assert active_is_self == 1
    assert context_start_calls == 2
    assert context_reset_calls == 1
    assert collector_start_calls == 2
    assert collector_reset_calls == 1
    assert scheduler_start_calls == 2
    assert scheduler_reset_calls == 1
    assert active_collectors == 1
