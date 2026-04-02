import asyncio
from threading import Event, Thread
from time import monotonic, sleep

from opentelemetry.sdk.extension.profiling.collector.stack import (
    StackCollector,
)
from opentelemetry.sdk.extension.profiling.context_bridge import ContextBridge
from opentelemetry.sdk.trace import TracerProvider


def test_context_bridge_tracks_asyncio_callback_context():
    bridge = ContextBridge()
    tracer = TracerProvider().get_tracer("test")
    started = Event()
    done = Event()
    captured = {}

    def runner():
        async def busy():
            with tracer.start_as_current_span("async-span") as span:
                captured["span_context"] = span.get_span_context()
                started.set()
                deadline = monotonic() + 0.3
                while monotonic() < deadline:
                    pass
            done.set()

        asyncio.run(busy())

    bridge.start()
    thread = Thread(target=runner, name="asyncio-worker")
    thread.start()
    started.wait(timeout=5)
    try:
        collector = StackCollector(context_bridge=bridge, max_frames=64)
        matched = []
        deadline = monotonic() + 1.0
        while monotonic() < deadline and not matched:
            samples = collector.capture()
            matched = [
                sample
                for sample in samples
                if sample.thread_name == "asyncio-worker"
                and sample.trace_id == captured["span_context"].trace_id
            ]
            if not matched:
                sleep(0.01)

        assert matched
        assert matched[0].span_id == captured["span_context"].span_id
    finally:
        done.wait(timeout=5)
        thread.join(timeout=5)
        bridge.stop()
