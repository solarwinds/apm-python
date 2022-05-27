"""Module to configure OpenTelemetry to work with SolarWinds backend"""

import logging
from os import environ

from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER
)
from opentelemetry.instrumentation.distro import BaseDistro

from solarwinds_apm import DEFAULT_SW_TRACES_EXPORTER


class SolarWindsDistro(BaseDistro):
    """OpenTelemetry Distro for SolarWinds reporting environment"""

    _TRACECONTEXT_PROPAGATOR = "tracecontext"
    _SW_PROPAGATOR = "solarwinds_propagator"
    _DEFAULT_SW_PROPAGATORS = [
        _TRACECONTEXT_PROPAGATOR,
        "baggage",
        _SW_PROPAGATOR,
    ]

    def _configure(self, **kwargs):
        """Configure OTel exporter and propagators"""
        environ.setdefault(OTEL_TRACES_EXPORTER, DEFAULT_SW_TRACES_EXPORTER)
        
        environ_propagators = environ.get(
            OTEL_PROPAGATORS,
            ",".join(self._DEFAULT_SW_PROPAGATORS)
        ).split(",")
        # If not using the default propagators,
        # can any arbitrary list BUT
        # (1) must include tracecontext and solarwinds_propagator
        # (2) tracecontext must be before solarwinds_propagator
        if environ_propagators != self._DEFAULT_SW_PROPAGATORS:
            if not self._TRACECONTEXT_PROPAGATOR in environ_propagators or \
                not self._SW_PROPAGATOR in environ_propagators:
                raise ValueError("Must include tracecontext and solarwinds_propagator in OTEL_PROPAGATORS to use SolarWinds Observability.")

            if environ_propagators.index(self._SW_PROPAGATOR) \
                < environ_propagators.index(self._TRACECONTEXT_PROPAGATOR):
                raise ValueError("tracecontext must be before solarwinds_propagator in OTEL_PROPAGATORS to use SolarWinds Observability.")
        environ[OTEL_PROPAGATORS] = ",".join(environ_propagators)
