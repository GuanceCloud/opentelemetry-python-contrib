from opentelemetry.sdk.extension.profiling import bootstrap


class _FakeProfiler:
    started = 0
    stopped = 0

    def start(self) -> None:
        self.__class__.started += 1

    def stop(self, flush: bool = True) -> None:
        self.__class__.stopped += 1


def test_auto_start_singleton(monkeypatch):
    monkeypatch.setenv("OTEL_PYTHON_PROFILING_ENABLED", "true")
    monkeypatch.setattr(bootstrap, "Profiler", _FakeProfiler)
    bootstrap._profiler = None
    _FakeProfiler.started = 0

    bootstrap.auto_start()
    bootstrap.auto_start()

    assert _FakeProfiler.started == 1
    bootstrap.stop_profiler()
    assert _FakeProfiler.stopped == 1


def test_auto_start_ignores_unset_enable_flag(monkeypatch):
    monkeypatch.delenv("OTEL_PYTHON_PROFILING_ENABLED", raising=False)
    monkeypatch.setattr(bootstrap, "Profiler", _FakeProfiler)
    bootstrap._profiler = None
    _FakeProfiler.started = 0
    _FakeProfiler.stopped = 0

    bootstrap.auto_start()

    assert _FakeProfiler.started == 0
    assert _FakeProfiler.stopped == 0
