from threading import Event, Thread

from opentelemetry.sdk.extension.profiling.collector.stack import (
    StackCollector,
)
from opentelemetry.sdk.extension.profiling.context_bridge import ContextBridge
from opentelemetry.sdk.trace import TracerProvider


def test_stack_collector_captures_background_thread_trace_context():
    bridge = ContextBridge()
    tracer = TracerProvider().get_tracer("test")
    ready = Event()
    finished = Event()
    captured = {}

    def worker():
        with tracer.start_as_current_span("worker-span") as span:
            captured["span_context"] = span.get_span_context()
            ready.set()
            finished.wait()

    bridge.start()
    thread = Thread(target=worker, name="worker-thread")
    thread.start()
    ready.wait(timeout=5)
    try:
        collector = StackCollector(context_bridge=bridge, max_frames=16)
        samples = collector.capture()
        matched = [
            sample for sample in samples if sample.thread_name == "worker-thread"
        ]
        assert matched
        assert matched[0].trace_id == captured["span_context"].trace_id
        assert matched[0].span_id == captured["span_context"].span_id
    finally:
        finished.set()
        thread.join(timeout=5)
        bridge.stop()
