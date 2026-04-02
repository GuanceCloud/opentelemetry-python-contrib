Guance OpenTelemetry Distro
===========================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/guance-opentelemetry-distro.svg
   :target: https://pypi.org/project/guance-opentelemetry-distro/

Installation
------------

::

    pip install guance-opentelemetry-distro

This package provides entrypoints to configure OpenTelemetry.

Command Line
------------

The package also installs a ``gtrace`` command as a shorthand for
auto-instrumented launches:

::

    gtrace uvicorn fastapi-demo:app --host 127.0.0.1 --port 18082

Profiling
---------

The base package installs the ``guance-sdk-extension-profiling``
package, which registers an ``opentelemetry_pre_instrument`` entry
point. Enable it with:

::

    export OTEL_PROFILING_ENABLED=true
    gtrace python app.py

When ``OTEL_PROFILING_PPROF_UPLOAD_URL`` is configured and
``OTEL_PROFILING_EXPORTER`` is unset, profiling defaults to a
legacy-compatible ``pprof`` upload layout. Explicit
``OTEL_PROFILING_*`` settings take precedence.

Common profiling parameters:

* ``OTEL_PROFILING_ENABLED``
* ``OTEL_PROFILING_EXPORTER`` (``otlp`` or ``pprof``)
* ``OTEL_PROFILING_SAMPLE_INTERVAL``
* ``OTEL_PROFILING_EXPORT_INTERVAL``
* ``OTEL_PROFILING_MAX_FRAMES``
* ``OTEL_PROFILING_EXCEPTION_ENABLED``
* ``OTEL_PROFILING_EXCEPTION_SAMPLING_INTERVAL``
* ``OTEL_PROFILING_EXCEPTION_COLLECT_MESSAGE``
* ``OTEL_PROFILING_LOCK_ENABLED``
* ``OTEL_PROFILING_MEMORY_ENABLED``
* ``OTEL_PROFILING_MEMORY_INTERVAL``
* ``OTEL_PROFILING_MEMORY_TOP_STATS``
* ``OTEL_PROFILING_PPROF_PATH``
* ``OTEL_PROFILING_PPROF_UPLOAD_URL``
* ``OTEL_PROFILING_PPROF_HEADERS``
* ``OTEL_EXPORTER_OTLP_PROFILES_PROTOCOL``
* ``OTEL_EXPORTER_OTLP_PROFILES_ENDPOINT``
* ``OTEL_EXPORTER_OTLP_PROFILES_HEADERS``

Example:

::

    export OTEL_PROFILING_ENABLED=true
    export OTEL_PROFILING_EXCEPTION_ENABLED=true
    export OTEL_PROFILING_LOCK_ENABLED=true
    export OTEL_PROFILING_MEMORY_ENABLED=true
    export OTEL_PROFILING_PPROF_UPLOAD_URL=http://localhost:9529/profiling/v1/input
    gtrace python app.py

References
----------

* `OpenTelemetry Project <https://opentelemetry.io/>`_
* `Example using guance-opentelemetry-distro <https://opentelemetry.io/docs/instrumentation/python/distro/>`_
