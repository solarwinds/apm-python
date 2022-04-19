"""Module to configure OpenTelemetry agent to work with SolarWinds backend"""

import logging
from os import environ
from pkg_resources import iter_entry_points

from opentelemetry import trace
from opentelemetry.environment_variables import OTEL_PROPAGATORS, OTEL_TRACES_EXPORTER
from opentelemetry.instrumentation.distro import BaseDistro
from opentelemetry.instrumentation.propagators import set_global_response_propagator
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry_distro_solarwinds.response_propagator import SolarWindsTraceResponsePropagator
from opentelemetry_distro_solarwinds.sampler import ParentBasedSwSampler

logger = logging.getLogger(__name__)

class SolarWindsDistro(BaseDistro):
    """SolarWinds custom distro for OpenTelemetry agents."""

    _DEFAULT_OTEL_EXPORTER = "solarwinds_exporter"
    _DEFAULT_OTEL_PROPAGATORS = [
        "tracecontext",
        "baggage",
        "solarwinds_propagator",
    ]

    def _configure(self, **kwargs):
        # Automatically use custom SolarWinds sampler
        trace.set_tracer_provider(
            TracerProvider(sampler=ParentBasedSwSampler()))

        # Customize Exporter else default to SolarWindsSpanExporter
        environ_exporter = environ.get(
            OTEL_TRACES_EXPORTER,
            self._DEFAULT_OTEL_EXPORTER
        )
        try:
            exporter = next(
                iter_entry_points(
                    "opentelemetry_traces_exporter",
                    environ_exporter
                )).load()()
        except:
            logger.exception(
                "Failed to load configured exporter `%s`", environ_exporter
            )
            raise

        span_exporter = BatchSpanProcessor(exporter)
        trace.get_tracer_provider().add_span_processor(span_exporter)

        # Configure context propagators to always include
        # tracecontext,baggage,solarwinds -- first and in that order
        # -- plus any others specified by env var
        environ_propagators = environ.get(
            OTEL_PROPAGATORS,
            ",".join(self._DEFAULT_OTEL_PROPAGATORS)
        ).split(",")
        if environ_propagators != self._DEFAULT_OTEL_PROPAGATORS:
            for default in self._DEFAULT_OTEL_PROPAGATORS:
                while default in environ_propagators:
                    environ_propagators.remove(default)
            environ_propagators = self._DEFAULT_OTEL_PROPAGATORS + environ_propagators
        environ[OTEL_PROPAGATORS] = ",".join(environ_propagators)

        # Init and set CompositePropagator globally, like OTel API
        propagators = []
        for propagator in environ_propagators:
            try:
                propagators.append(
                    next(
                        iter_entry_points("opentelemetry_propagator", propagator)
                    ).load()()
                )
            except Exception:
                logger.exception(
                    "Failed to load configured propagator `%s`", propagator
                )
                raise
        set_global_textmap(CompositePropagator(propagators))

        # Set global HTTP response propagator
        set_global_response_propagator(SolarWindsTraceResponsePropagator())