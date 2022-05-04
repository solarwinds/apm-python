"""Module to initialize OpenTelemetry SDK components to work with SolarWinds backend"""

import logging
from os import environ
from pkg_resources import (
    iter_entry_points,
    load_entry_point
)

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

from solarwinds_apm.distro import SolarWindsDistro
from solarwinds_apm.response_propagator import SolarWindsTraceResponsePropagator

logger = logging.getLogger(__name__)

class SolarWindsConfigurator(_OTelSDKConfigurator):
    """OpenTelemetry Configurator for initializing SolarWinds-reporting SDK components"""

    # Cannot set as env default because not part of OTel Python _KNOWN_SAMPLERS
    # https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-sdk/src/opentelemetry/sdk/trace/sampling.py#L364-L380
    _DEFAULT_SW_TRACES_SAMPLER = "solarwinds_sampler"

    def _configure(self, **kwargs):
        environ_sampler = environ.get(
            OTEL_TRACES_SAMPLER,
            self._DEFAULT_SW_TRACES_SAMPLER,
        )
        try:
            sampler = load_entry_point(
                "solarwinds_apm",
                "opentelemetry_traces_sampler",
                environ_sampler
            )()
        except:
            logger.exception(
                "Failed to load configured sampler `%s`", environ_sampler
            )
            raise
        trace.set_tracer_provider(
            TracerProvider(sampler=sampler))

        environ_exporter = environ.get(OTEL_TRACES_EXPORTER)
        try:
            exporter = load_entry_point(
                "solarwinds_apm",
                "opentelemetry_traces_exporter",
                environ_exporter
            )()
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
