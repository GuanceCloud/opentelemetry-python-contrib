from threading import get_ident

from opentelemetry.sdk.extension.profiling.context_bridge import ContextBridge
from opentelemetry.sdk.trace import TracerProvider


def test_context_bridge_tracks_active_span():
    bridge = ContextBridge()
    tracer = TracerProvider().get_tracer("test")

    bridge.start()
    try:
        with tracer.start_as_current_span("span") as span:
            span_context = bridge.span_context_for_thread(get_ident())
            assert span_context.trace_id == span.get_span_context().trace_id
            assert span_context.span_id == span.get_span_context().span_id

        assert not bridge.span_context_for_thread(get_ident()).is_valid
    finally:
        bridge.stop()
