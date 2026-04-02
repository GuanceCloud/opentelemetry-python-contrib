from __future__ import annotations

from opentelemetry.sdk.extension.profiling.export import (
    CompatiblePPROFExporter,
)
from opentelemetry.sdk.extension.profiling.export.pprof import (
    PPROFProfileExporter,
)
from opentelemetry.sdk.extension.profiling.model.pprof_builder import (
    CompatiblePprofProfileBuilder,
    PprofProfileBuilder,
)
from opentelemetry.sdk.extension.profiling.runtime import Profiler


def test_runtime_defaults_to_compatible_exporter_for_env_fallback(
    monkeypatch,
):
    monkeypatch.delenv("OTEL_PROFILING_EXPORTER", raising=False)
    monkeypatch.setenv(
        "OTEL_PROFILING_PPROF_UPLOAD_URL",
        "http://collector:9529/profiling/v1/input",
    )

    exporter = Profiler._create_exporter_from_env()

    assert isinstance(exporter, CompatiblePPROFExporter)
    exporter.shutdown()


def test_runtime_explicit_otlp_exporter_overrides_env_fallback(
    monkeypatch,
):
    sentinel = object()
    monkeypatch.setenv("OTEL_PROFILING_EXPORTER", "otlp")
    monkeypatch.setenv(
        "OTEL_PROFILING_PPROF_UPLOAD_URL",
        "http://collector:9529/profiling/v1/input",
    )
    monkeypatch.setattr(
        "opentelemetry.sdk.extension.profiling.runtime.create_otlp_profile_exporter",
        lambda: sentinel,
    )

    exporter = Profiler._create_exporter_from_env()

    assert exporter is sentinel


def test_runtime_uses_compatible_pprof_builder_for_http_exporter(tmp_path):
    profiler = Profiler(
        exporter=CompatiblePPROFExporter(pprof_path=str(tmp_path / "prof"))
    )

    try:
        assert isinstance(profiler._builder, CompatiblePprofProfileBuilder)
    finally:
        profiler._exporter.shutdown()


def test_runtime_uses_standard_pprof_builder_for_file_exporter(tmp_path):
    profiler = Profiler(
        exporter=PPROFProfileExporter(directory=str(tmp_path / "prof"))
    )

    try:
        assert isinstance(profiler._builder, PprofProfileBuilder)
        assert not isinstance(profiler._builder, CompatiblePprofProfileBuilder)
    finally:
        profiler._exporter.shutdown()
