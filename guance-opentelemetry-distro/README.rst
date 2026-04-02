Guance OpenTelemetry Distro
===========================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/guance-opentelemetry-distro.svg
   :target: https://pypi.org/project/guance-opentelemetry-distro/

Installation
------------

::

    pip install guance-opentelemetry-distro

To install the distro with Python profiling support:

::

    pip install guance-opentelemetry-distro[profiling]

This package provides entrypoints to configure OpenTelemetry.

Command Line
------------

The package also installs a ``gtrace`` command as a shorthand for
auto-instrumented launches:

::

    gtrace uvicorn fastapi-demo:app --host 127.0.0.1 --port 18082

Profiling
---------

The ``profiling`` extra installs the
``opentelemetry-sdk-extension-profiling`` package, which registers an
``opentelemetry_pre_instrument`` entry point. Enable it with:

::

    export OTEL_PROFILING_ENABLED=true
    gtrace python app.py

When ``OTEL_PROFILING_PPROF_UPLOAD_URL`` is configured and
``OTEL_PROFILING_EXPORTER`` is unset, profiling defaults to a
legacy-compatible ``pprof`` upload layout. Explicit
``OTEL_PROFILING_*`` settings take precedence.

References
----------

* `OpenTelemetry Project <https://opentelemetry.io/>`_
* `Example using guance-opentelemetry-distro <https://opentelemetry.io/docs/instrumentation/python/distro/>`_
