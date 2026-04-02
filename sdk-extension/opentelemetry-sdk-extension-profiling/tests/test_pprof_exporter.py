from __future__ import annotations

from pathlib import Path

from opentelemetry.sdk.extension.profiling.export.pprof import (
    PPROFProfileExporter,
)


def test_pprof_exporter_writes_profile(tmp_path: Path):
    exporter = PPROFProfileExporter(directory=str(tmp_path / "prof"))
    payload = b"pprof-data"

    result = exporter.export(payload)

    files = list(tmp_path.glob("prof*.pprof"))
    assert files
    assert files[0].read_bytes() == payload
    assert result.name == "SUCCESS"
