import tracemalloc

from opentelemetry.sdk.extension.profiling.collector.memory import (
    MemoryCollector,
)


def _allocate_memory():
    return [("x" * 2048) + str(index) for index in range(512)]


def test_memory_collector_captures_heap_samples():
    collector = MemoryCollector(
        max_frames=8,
        capture_interval=0.0,
        top_stats=50,
    )
    allocations = None

    collector.start()
    try:
        allocations = _allocate_memory()
        samples = collector.capture()
    finally:
        collector.stop()

    assert allocations is not None
    bytes_samples = [
        sample for sample in samples if sample.sample_type == "memory.heap.bytes"
    ]
    object_samples = [
        sample
        for sample in samples
        if sample.sample_type == "memory.heap.objects"
    ]

    assert bytes_samples
    assert object_samples

    target_bytes_samples = [
        sample
        for sample in bytes_samples
        if sample.frames
        and sample.frames[0].filename.endswith("test_memory_collector.py")
    ]
    assert target_bytes_samples

    sample = target_bytes_samples[0]
    attributes = {attribute.key: attribute.value for attribute in sample.attributes}

    assert sample.thread_id == 0
    assert sample.thread_name == "process"
    assert sample.value > 0
    assert sample.sample_unit == "bytes"
    assert sample.frames[0].function.startswith("test_memory_collector.py:")
    assert attributes["memory.kind"] == "heap"
    assert attributes["memory.source"] == "tracemalloc"


def test_memory_collector_respects_capture_interval():
    collector = MemoryCollector(
        max_frames=8,
        capture_interval=60.0,
        top_stats=20,
    )
    allocations = None

    collector.start()
    try:
        allocations = _allocate_memory()
        first_capture = collector.capture()
        second_capture = collector.capture()
    finally:
        collector.stop()

    assert allocations is not None
    assert first_capture
    assert second_capture == []


def test_memory_collector_does_not_stop_existing_tracemalloc():
    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start(8)

    collector = MemoryCollector(
        max_frames=8,
        capture_interval=0.0,
        top_stats=10,
    )
    try:
        collector.start()
        collector.stop()
        assert tracemalloc.is_tracing()
    finally:
        if not was_tracing and tracemalloc.is_tracing():
            tracemalloc.stop()
