"""Module to initialize OpenTelemetry SDK components to work with SolarWinds backend"""

import logging
from os import environ
from pkg_resources import iter_entry_points

from opentelemetry import trace
from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER
)
from opentelemetry.instrumentation.propagators import set_global_response_propagator
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk._configuration import _OTelSDKConfigurator
from opentelemetry.sdk.environment_variables import OTEL_TRACES_SAMPLER
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from solarwinds_observability.distro import SolarWindsDistro
from solarwinds_observability.response_propagator import SolarWindsTraceResponsePropagator

logger = logging.getLogger(__name__)

class SolarWindsConfigurator(_OTelSDKConfigurator):
    """OpenTelemetry Configurator for initializing SolarWinds-reporting SDK components"""

    def _configure(self, **kwargs):
        # If default_traces_sampler is configured then hook up
        # Else let OTel Python get_from_env_or_default
        environ_sampler = environ.get(OTEL_TRACES_SAMPLER)
        if environ_sampler == SolarWindsDistro.default_sw_traces_sampler():
            try:
                sampler = next(
                    iter_entry_points(
                        "opentelemetry_traces_sampler",
                        environ_sampler
                    )).load()()
            except:
                logger.exception(
                    "Failed to load configured sampler `%s`", environ_sampler
                )
                raise
            trace.set_tracer_provider(
                TracerProvider(sampler=sampler))
        else:
            trace.set_tracer_provider()

        environ_exporter = environ.get(OTEL_TRACES_EXPORTER)
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

        # Init and set CompositePropagator globally, like OTel API
        environ_propagators = environ.get(OTEL_PROPAGATORS).split(",")
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
