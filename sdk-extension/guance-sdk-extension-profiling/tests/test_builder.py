from opentelemetry.sdk.extension.profiling.collector.base import (
    CapturedAttribute,
    CapturedFrame,
    CapturedSample,
)
from opentelemetry.sdk.extension.profiling.model.builder import (
    ProfilesRequestBuilder,
)
from opentelemetry.sdk.resources import Resource


def test_profiles_request_builder_aggregates_duplicate_samples():
    builder = ProfilesRequestBuilder()
    resource = Resource.create({"service.name": "svc"})
    frames = (
        CapturedFrame(
            function="leaf",
            filename="/tmp/app.py",
            lineno=10,
        ),
        CapturedFrame(
            function="root",
            filename="/tmp/app.py",
            lineno=1,
        ),
    )
    samples = [
        CapturedSample(
            timestamp_unix_nano=100,
            thread_id=1,
            thread_name="worker",
            frames=frames,
        ),
        CapturedSample(
            timestamp_unix_nano=200,
            thread_id=1,
            thread_name="worker",
            frames=frames,
        ),
    ]

    request = builder.build(samples, resource, sample_period_ns=10_000_000)

    assert len(request.resource_profiles) == 1
    profile = request.resource_profiles[0].scope_profiles[0].profiles[0]
    assert len(profile.samples) == 1
    assert list(profile.samples[0].values) == [1, 1]
    assert list(profile.samples[0].timestamps_unix_nano) == [100, 200]
    assert "leaf" in request.dictionary.string_table
    assert "thread.name" in request.dictionary.string_table


def test_profiles_request_builder_splits_distinct_profile_types():
    builder = ProfilesRequestBuilder()
    resource = Resource.create({"service.name": "svc"})
    frames = (
        CapturedFrame(
            function="leaf",
            filename="/tmp/app.py",
            lineno=10,
        ),
    )
    samples = [
        CapturedSample(
            timestamp_unix_nano=100,
            thread_id=1,
            thread_name="worker",
            frames=frames,
        ),
        CapturedSample(
            timestamp_unix_nano=200,
            thread_id=1,
            thread_name="worker",
            frames=frames,
            value=123,
            sample_type="exceptions",
            period_type="exceptions",
            period_unit="count",
            period=100,
            attributes=(
                CapturedAttribute(
                    key="exception.type",
                    value="builtins.ValueError",
                ),
            ),
        ),
    ]

    request = builder.build(samples, resource, sample_period_ns=10_000_000)

    profiles = request.resource_profiles[0].scope_profiles[0].profiles
    assert len(profiles) == 2

    string_table = request.dictionary.string_table
    profile_types = {
        string_table[profile.sample_type.type_strindex] for profile in profiles
    }
    assert profile_types == {"samples", "exceptions"}
    assert "exception.type" in string_table
    exception_profile = next(
        profile
        for profile in profiles
        if string_table[profile.sample_type.type_strindex] == "exceptions"
    )
    assert list(exception_profile.samples[0].values) == [123]
