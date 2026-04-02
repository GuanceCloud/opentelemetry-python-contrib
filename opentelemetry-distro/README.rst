OpenTelemetry Distro
====================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opentelemetry-distro.svg
   :target: https://pypi.org/project/opentelemetry-distro/

Installation
------------

::

    pip install opentelemetry-distro

To install the distro with Python profiling support:

::

    pip install opentelemetry-distro[profiling]

This package provides entrypoints to configure OpenTelemetry.

Profiling
---------

The ``profiling`` extra installs the
``guance-sdk-extension-profiling`` package, which registers an
``opentelemetry_pre_instrument`` entry point. Enable it for
``opentelemetry-instrument`` with:

::

    export OTEL_PROFILING_ENABLED=true
    opentelemetry-instrument python app.py

When ``OTEL_PROFILING_PPROF_UPLOAD_URL`` is configured and
``OTEL_PROFILING_EXPORTER`` is unset, profiling defaults to a
legacy-compatible ``pprof`` upload layout. Explicit
``OTEL_PROFILING_*`` settings take precedence.

References
----------

* `OpenTelemetry Project <https://opentelemetry.io/>`_
* `Example using opentelemetry-distro <https://opentelemetry.io/docs/instrumentation/python/distro/>`_
