from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Thread

import grpc

from opentelemetry.proto.collector.profiles.v1development.profiles_service_pb2 import (
    ExportProfilesServiceRequest,
    ExportProfilesServiceResponse,
)
from opentelemetry.proto.collector.profiles.v1development.profiles_service_pb2_grpc import (
    ProfilesServiceServicer,
    add_ProfilesServiceServicer_to_server,
)
from opentelemetry.sdk.extension.profiling.collector.base import (
    CapturedFrame,
    CapturedSample,
)
from opentelemetry.sdk.extension.profiling.export.grpc import (
    OTLPProfileExporter,
)
from opentelemetry.sdk.extension.profiling.export.http import (
    OTLPHTTPProfileExporter,
)
from opentelemetry.sdk.extension.profiling.export.result import (
    ProfileExportResult,
)
from opentelemetry.sdk.extension.profiling.model.builder import (
    ProfilesRequestBuilder,
)
from opentelemetry.sdk.resources import Resource


def test_otlp_http_profile_exporter_exports_request():
    received = {}
    ready = Event()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            received["path"] = self.path
            received["request"] = ExportProfilesServiceRequest.FromString(body)
            self.send_response(200)
            self.end_headers()
            ready.set()

        def log_message(self, format: str, *args) -> None:  # noqa: A002
            return None

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        request = _build_request()
        exporter = OTLPHTTPProfileExporter(
            endpoint=(
                f"http://127.0.0.1:{server.server_address[1]}"
                "/v1development/profiles"
            )
        )
        result = exporter.export(request)
        assert result is ProfileExportResult.SUCCESS
        ready.wait(timeout=5)
        assert received["path"] == "/v1development/profiles"
        _assert_exported_request(received["request"])
        exporter.shutdown()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_otlp_grpc_profile_exporter_exports_request():
    received = {}
    ready = Event()

    class Servicer(ProfilesServiceServicer):
        def Export(self, request, context):  # noqa: N802
            received["request"] = request
            ready.set()
            return ExportProfilesServiceResponse()

    server = grpc.server(ThreadPoolExecutor(max_workers=1))
    add_ProfilesServiceServicer_to_server(Servicer(), server)
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()

    try:
        request = _build_request()
        exporter = OTLPProfileExporter(
            endpoint=f"http://127.0.0.1:{port}",
            insecure=True,
        )
        result = exporter.export(request)
        assert result is ProfileExportResult.SUCCESS
        ready.wait(timeout=5)
        _assert_exported_request(received["request"])
        exporter.shutdown()
    finally:
        server.stop(None)


def _build_request() -> ExportProfilesServiceRequest:
    builder = ProfilesRequestBuilder()
    return builder.build(
        samples=[
            CapturedSample(
                timestamp_unix_nano=100,
                thread_id=1,
                thread_name="worker",
                frames=(
                    CapturedFrame(
                        function="leaf",
                        filename="/tmp/app.py",
                        lineno=10,
                    ),
                ),
            )
        ],
        resource=Resource.create({"service.name": "svc"}),
        sample_period_ns=10_000_000,
    )


def _assert_exported_request(request: ExportProfilesServiceRequest) -> None:
    assert len(request.resource_profiles) == 1
    resource_profiles = request.resource_profiles[0]
    assert resource_profiles.resource.attributes
    assert len(resource_profiles.scope_profiles) == 1
    assert len(resource_profiles.scope_profiles[0].profiles) == 1
