
import pytest

from opentelemetry.sdk.extension.profiling.collector.exception import (
    HAS_MONITORING,
    ExceptionCollector,
)
from opentelemetry.sdk.extension.profiling.context_bridge import ContextBridge
from opentelemetry.sdk.trace import TracerProvider


def _raise_and_handle() -> None:
    raise ValueError("boom")


@pytest.mark.skipif(not HAS_MONITORING, reason="sys.monitoring unavailable")
def test_exception_collector_captures_handled_exception():
    bridge = ContextBridge()
    tracer = TracerProvider().get_tracer("test")
    collector = ExceptionCollector(
        context_bridge=bridge,
        sampling_interval=1,
        collect_message=True,
    )

    bridge.start()
    collector.start()
    try:
        with tracer.start_as_current_span("span") as span:
            try:
                _raise_and_handle()
            except ValueError:
                pass

        samples = collector.capture()
    finally:
        collector.stop()
        bridge.stop()

    assert len(samples) == 1
    sample = samples[0]
    attributes = {attribute.key: attribute.value for attribute in sample.attributes}

    assert sample.sample_type == "exceptions"
    assert sample.period_type == "exceptions"
    assert sample.period == 1
    assert sample.trace_id == span.get_span_context().trace_id
    assert sample.span_id == span.get_span_context().span_id
    assert sample.frames[0].function == "_raise_and_handle"
    assert attributes["exception.type"] == "builtins.ValueError"
    assert attributes["exception.message"] == "boom"
    assert attributes["exception.escaped"] is False


@pytest.mark.skipif(not HAS_MONITORING, reason="sys.monitoring unavailable")
def test_exception_collector_truncates_unprintable_message():
    bridge = ContextBridge()
    collector = ExceptionCollector(
        context_bridge=bridge,
        sampling_interval=1,
        collect_message=True,
    )

    class BrokenException(RuntimeError):
        def __str__(self) -> str:
            raise ValueError("broken __str__")

    bridge.start()
    collector.start()
    try:
        try:
            raise BrokenException()
        except BrokenException:
            pass

        samples = collector.capture()
    finally:
        collector.stop()
        bridge.stop()

    assert len(samples) == 1
    attributes = {
        attribute.key: attribute.value for attribute in samples[0].attributes
    }
    assert attributes["exception.message"] == "<unprintable exception>"
