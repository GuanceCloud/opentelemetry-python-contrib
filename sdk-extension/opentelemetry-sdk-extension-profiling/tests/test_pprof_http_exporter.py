from __future__ import annotations

from unittest.mock import Mock

from opentelemetry.sdk.extension.profiling.export.pprof_http import (
    PPROFHTTPExporter,
)
from opentelemetry.sdk.resources import Resource


def test_pprof_http_exporter_posts_multipart_payload(
    monkeypatch, tmp_path
):
    session = Mock()
    session.post.return_value = Mock(status_code=202, text="ok")
    monkeypatch.setenv(
        "OTEL_PYTHON_PROFILING_PPROF_HEADERS",
        "X-API-Key:api-key",
    )
    monkeypatch.setenv(
        "OTEL_PYTHON_PROFILING_PPROF_UPLOAD_URL",
        "http://agent:8126/profiling/v1/input",
    )
    exporter = PPROFHTTPExporter(
        session=session,
        pprof_path=str(tmp_path / "prof"),
    )
    payload = b"foo"
    resource = Resource.create(
        {
            "service.name": "svc",
            "service.version": "1.2.3",
            "deployment.environment.name": "prod",
        }
    )

    result = exporter.export(
        payload,
        resource=resource,
        start_time_unix_nano=1_700_000_000_000_000_000,
        end_time_unix_nano=1_700_000_060_000_000_000,
    )

    assert result.name == "SUCCESS"
    session.post.assert_called_once()
    kwargs = session.post.call_args.kwargs
    assert kwargs["url"] == "http://agent:8126/profiling/v1/input"
    assert kwargs["headers"]["X-API-Key"] == "api-key"
    assert kwargs["headers"]["Content-Type"].startswith(
        "multipart/form-data; boundary="
    )
    body = kwargs["data"]
    assert b'filename="event.json"' in body
    assert b'filename="auto.pprof"' in body
    assert b'"family": "python"' in body
    assert b"service:svc" in body
    assert b"env:prod" in body
    assert b"version:1.2.3" in body
    assert payload in body
    files = list(tmp_path.glob("prof*.pprof"))
    assert files


def test_pprof_http_exporter_handles_failure(monkeypatch, tmp_path):
    session = Mock()
    session.post.side_effect = Exception("boom")
    exporter = PPROFHTTPExporter(
        session=session,
        pprof_path=str(tmp_path / "prof"),
    )

    result = exporter.export(b"bar")

    assert result.name == "FAILURE"
    files = list(tmp_path.glob("prof*.pprof"))
    assert files
