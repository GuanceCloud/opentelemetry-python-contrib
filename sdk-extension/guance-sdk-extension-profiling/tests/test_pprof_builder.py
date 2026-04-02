from __future__ import annotations

import gzip
from time import time_ns

from opentelemetry.sdk.extension.profiling.collector.base import (
    CapturedAttribute,
    CapturedFrame,
    CapturedSample,
)
from opentelemetry.sdk.extension.profiling.export import pprof_pb2
from opentelemetry.sdk.extension.profiling.model.pprof_builder import (
    CompatiblePprofProfileBuilder,
    PprofProfileBuilder,
)
from opentelemetry.sdk.resources import Resource


def test_pprof_builder_produces_gzip_encoded_profile():
    builder = PprofProfileBuilder()
    now = time_ns()
    frame = CapturedFrame(function="leaf", filename="/tmp/app.py", lineno=10)
    sample = CapturedSample(
        timestamp_unix_nano=now,
        thread_id=1,
        thread_name="main",
        frames=(frame,),
        sample_type="samples",
        sample_unit="nanoseconds",
        value=42,
    )

    payload = builder.build(samples=[sample], sample_period_ns=1000)
    profile = pprof_pb2.Profile()
    profile.ParseFromString(gzip.decompress(payload))

    assert profile.sample
    assert profile.sample[0].value == [42]
    assert profile.period == 1000


def test_compatible_pprof_builder_produces_legacy_python_layout():
    builder = CompatiblePprofProfileBuilder()
    now = time_ns()
    frame = CapturedFrame(function="leaf", filename="/tmp/app.py", lineno=10)
    samples = [
        CapturedSample(
            timestamp_unix_nano=now,
            thread_id=1,
            thread_name="main",
            frames=(frame,),
        ),
        CapturedSample(
            timestamp_unix_nano=now + 1,
            thread_id=2,
            thread_name="worker",
            frames=(frame,),
            sample_type="exceptions",
            sample_unit="count",
            attributes=(
                CapturedAttribute(
                    key="exception.message",
                    value="boom",
                ),
            ),
        ),
        CapturedSample(
            timestamp_unix_nano=now + 2,
            thread_id=3,
            thread_name="memory",
            frames=(frame,),
            value=2048,
            sample_type="memory.heap.bytes",
            sample_unit="bytes",
        ),
        CapturedSample(
            timestamp_unix_nano=now + 3,
            thread_id=4,
            thread_name="lock",
            frames=(frame,),
            value=123,
            sample_type="lock.acquire.duration",
            sample_unit="nanoseconds",
        ),
    ]

    payload = builder.build(
        samples=samples,
        resource=Resource.create({"service.name": "svc"}),
        sample_period_ns=1000,
    )
    profile = pprof_pb2.Profile()
    profile.ParseFromString(gzip.decompress(payload))

    string_table = list(profile.string_table)
    sample_types = [
        (
            string_table[sample_type.type],
            string_table[sample_type.unit],
        )
        for sample_type in profile.sample_type
    ]
    assert sample_types == [
        ("cpu-samples", "count"),
        ("cpu-time", "nanoseconds"),
        ("wall-time", "nanoseconds"),
        ("exception-samples", "count"),
        ("lock-acquire", "count"),
        ("lock-acquire-wait", "nanoseconds"),
        ("lock-release", "count"),
        ("lock-release-hold", "nanoseconds"),
        ("alloc-samples", "count"),
        ("alloc-space", "bytes"),
        ("heap-space", "bytes"),
    ]
    assert string_table[profile.period_type.type] == "time"
    assert string_table[profile.period_type.unit] == "nanoseconds"
    assert len(profile.mapping) == 1
    assert string_table[profile.mapping[0].filename] == "svc"
    assert profile.sample[0].value == [1, 1000, 1000, 0, 0, 0, 0, 0, 0, 0, 0]
    assert profile.sample[1].value == [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
    assert profile.sample[2].value == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2048]
    assert profile.sample[3].value == [0, 0, 0, 0, 1, 123, 0, 0, 0, 0, 0]
    labels = {
        string_table[label.key]: string_table[label.str]
        for label in profile.sample[1].label
        if label.str
    }
    assert labels["thread id"] == "2"
    assert labels["exception message"] == "boom"
