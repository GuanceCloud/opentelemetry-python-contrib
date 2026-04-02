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

from os import environ
from typing import Dict, Optional, Tuple, Union
from typing import Sequence as TypingSequence

from grpc import ChannelCredentials, Compression

from opentelemetry.exporter.otlp.proto.grpc.exporter import (
    OTLPExporterMixin,
    _get_credentials,
    environ_to_compression,
)
from opentelemetry.proto.collector.profiles.v1development.profiles_service_pb2 import (
    ExportProfilesServiceRequest,
)
from opentelemetry.proto.collector.profiles.v1development.profiles_service_pb2_grpc import (
    ProfilesServiceStub,
)
from opentelemetry.sdk.environment_variables import (
    _OTEL_PYTHON_EXPORTER_OTLP_GRPC_CREDENTIAL_PROVIDER,
    OTEL_EXPORTER_OTLP_CERTIFICATE,
    OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE,
    OTEL_EXPORTER_OTLP_CLIENT_KEY,
    OTEL_EXPORTER_OTLP_ENDPOINT,
    OTEL_EXPORTER_OTLP_HEADERS,
    OTEL_EXPORTER_OTLP_PROTOCOL,
    OTEL_EXPORTER_OTLP_TIMEOUT,
)
from opentelemetry.sdk.extension.profiling.environment_variables import (
    OTEL_EXPORTER_OTLP_PROFILES_CERTIFICATE,
    OTEL_EXPORTER_OTLP_PROFILES_CLIENT_CERTIFICATE,
    OTEL_EXPORTER_OTLP_PROFILES_CLIENT_KEY,
    OTEL_EXPORTER_OTLP_PROFILES_COMPRESSION,
    OTEL_EXPORTER_OTLP_PROFILES_ENDPOINT,
    OTEL_EXPORTER_OTLP_PROFILES_HEADERS,
    OTEL_EXPORTER_OTLP_PROFILES_INSECURE,
    OTEL_EXPORTER_OTLP_PROFILES_PROTOCOL,
    OTEL_EXPORTER_OTLP_PROFILES_TIMEOUT,
)
from opentelemetry.sdk.extension.profiling.export.result import (
    ProfileExportResult,
)


class OTLPProfileExporter(
    OTLPExporterMixin[
        ExportProfilesServiceRequest,
        ExportProfilesServiceRequest,
        ProfileExportResult,
        ProfilesServiceStub,
    ]
):
    def __init__(
        self,
        endpoint: Optional[str] = None,
        insecure: Optional[bool] = None,
        credentials: Optional[ChannelCredentials] = None,
        headers: Optional[
            Union[TypingSequence[Tuple[str, str]], Dict[str, str], str]
        ] = None,
        timeout: Optional[float] = None,
        compression: Optional[Compression] = None,
        channel_options: Optional[Tuple[Tuple[str, str]]] = None,
    ) -> None:
        insecure_profiles = environ.get(OTEL_EXPORTER_OTLP_PROFILES_INSECURE)
        if insecure is None and insecure_profiles is not None:
            insecure = insecure_profiles.lower() == "true"

        if (
            not insecure
            and environ.get(OTEL_EXPORTER_OTLP_PROFILES_CERTIFICATE)
            is not None
        ):
            credentials = _get_credentials(
                credentials,
                _OTEL_PYTHON_EXPORTER_OTLP_GRPC_CREDENTIAL_PROVIDER,
                OTEL_EXPORTER_OTLP_PROFILES_CERTIFICATE,
                OTEL_EXPORTER_OTLP_PROFILES_CLIENT_KEY,
                OTEL_EXPORTER_OTLP_PROFILES_CLIENT_CERTIFICATE,
            )
        elif (
            not insecure
            and environ.get(OTEL_EXPORTER_OTLP_CERTIFICATE) is not None
        ):
            credentials = _get_credentials(
                credentials,
                _OTEL_PYTHON_EXPORTER_OTLP_GRPC_CREDENTIAL_PROVIDER,
                OTEL_EXPORTER_OTLP_CERTIFICATE,
                OTEL_EXPORTER_OTLP_CLIENT_KEY,
                OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE,
            )

        environ_timeout = environ.get(
            OTEL_EXPORTER_OTLP_PROFILES_TIMEOUT,
            environ.get(OTEL_EXPORTER_OTLP_TIMEOUT),
        )
        parsed_timeout = (
            float(environ_timeout) if environ_timeout is not None else None
        )

        parsed_compression = (
            environ_to_compression(OTEL_EXPORTER_OTLP_PROFILES_COMPRESSION)
            if compression is None
            else compression
        )

        protocol = environ.get(
            OTEL_EXPORTER_OTLP_PROFILES_PROTOCOL,
            environ.get(OTEL_EXPORTER_OTLP_PROTOCOL, "grpc"),
        )
        if protocol != "grpc":
            raise ValueError(
                f"Unsupported OTLP profiles gRPC protocol: {protocol}"
            )

        OTLPExporterMixin.__init__(
            self,
            stub=ProfilesServiceStub,
            result=ProfileExportResult,
            endpoint=endpoint
            or environ.get(OTEL_EXPORTER_OTLP_PROFILES_ENDPOINT)
            or environ.get(OTEL_EXPORTER_OTLP_ENDPOINT),
            insecure=insecure,
            credentials=credentials,
            headers=headers
            or environ.get(OTEL_EXPORTER_OTLP_PROFILES_HEADERS)
            or environ.get(OTEL_EXPORTER_OTLP_HEADERS),
            timeout=timeout or parsed_timeout,
            compression=parsed_compression,
            channel_options=channel_options,
        )

    def _translate_data(
        self, data: ExportProfilesServiceRequest
    ) -> ExportProfilesServiceRequest:
        return data

    def export(
        self, request: ExportProfilesServiceRequest
    ) -> ProfileExportResult:
        return self._export(request)

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    @property
    def _exporting(self) -> str:
        return "profiles"
