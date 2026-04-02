from __future__ import annotations

import sys
from os import environ

from opentelemetry.instrumentation import auto_instrumentation
from opentelemetry.instrumentation.auto_instrumentation import _load
from opentelemetry.sdk.extension.profiling import bootstrap
from opentelemetry.sdk.extension.profiling import (
    environment_variables as profiling_environment_variables,
)


class _FakeEntryPoint:
    def __init__(self, name: str, group: str, loaded) -> None:  # noqa: ANN001
        self.name = name
        self.group = group
        self._loaded = loaded
        loaded_name = getattr(loaded, "__name__", type(loaded).__name__)
        loaded_module = getattr(loaded, "__module__", type(loaded).__module__)
        self.value = f"{loaded_module}:{loaded_name}"

    def load(self):  # noqa: ANN201
        return self._loaded


class _FakeDistro:
    def __init__(self) -> None:
        self.configured = 0

    def configure(self, **kwargs) -> None:  # noqa: ANN003
        del kwargs
        self.configured += 1


class _FakeProfiler:
    started = 0
    stopped = 0

    def start(self) -> None:
        self.__class__.started += 1

    def stop(self, flush: bool = True) -> None:
        del flush
        self.__class__.stopped += 1


def test_initialize_loads_profiling_pre_instrument(monkeypatch):
    distro = _FakeDistro()

    def fake_entry_points(*, group):  # noqa: ANN202
        if group == "opentelemetry_pre_instrument":
            return [
                _FakeEntryPoint(
                    "profiling", group, bootstrap.auto_start
                )
            ]
        return []

    monkeypatch.setenv("OTEL_PYTHON_PROFILING_ENABLED", "true")
    monkeypatch.setattr(auto_instrumentation, "_load_distro", lambda: distro)
    monkeypatch.setattr(
        auto_instrumentation, "_load_configurators", lambda: None
    )
    monkeypatch.setattr(_load, "entry_points", fake_entry_points)
    monkeypatch.setattr(bootstrap, "Profiler", _FakeProfiler)

    bootstrap._profiler = None
    _FakeProfiler.started = 0
    _FakeProfiler.stopped = 0

    auto_instrumentation.initialize(swallow_exceptions=False)

    assert distro.configured == 1
    assert _FakeProfiler.started == 1
    assert bootstrap.get_profiler() is not None

    bootstrap.stop_profiler()
    assert _FakeProfiler.stopped == 1


def test_run_registers_profiling_environment_variable_arguments(monkeypatch):
    captured = {}

    def fake_entry_points(*, group):  # noqa: ANN202
        if group == "opentelemetry_environment_variables":
            return [
                _FakeEntryPoint(
                    "profiling",
                    group,
                    profiling_environment_variables,
                )
            ]
        return []

    def fake_execl(executable, *args) -> None:  # noqa: ANN001
        captured["executable"] = executable
        captured["args"] = args

    monkeypatch.setattr(auto_instrumentation, "entry_points", fake_entry_points)
    monkeypatch.setattr(auto_instrumentation, "which", lambda command: command)
    monkeypatch.setattr(auto_instrumentation, "execl", fake_execl)
    monkeypatch.delenv("OTEL_PYTHON_PROFILING_ENABLED", raising=False)
    monkeypatch.delenv("OTEL_PYTHON_PROFILING_LOCK_ENABLED", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "instrument",
            "--profiling_enabled",
            "true",
            "--profiling_lock_enabled",
            "true",
            "python",
            "-c",
            "pass",
        ],
    )

    auto_instrumentation.run()

    assert captured["executable"] == "python"
    assert captured["args"] == ("python", "-c", "pass")
    assert (
        profiling_environment_variables.OTEL_PYTHON_PROFILING_ENABLED
        in environ
    )
    assert (
        profiling_environment_variables.OTEL_PYTHON_PROFILING_LOCK_ENABLED
        in environ
    )
    assert (
        environ[
            profiling_environment_variables.OTEL_PYTHON_PROFILING_ENABLED
        ]
        == "true"
    )
    assert (
        environ[
            profiling_environment_variables.OTEL_PYTHON_PROFILING_LOCK_ENABLED
        ]
        == "true"
    )
