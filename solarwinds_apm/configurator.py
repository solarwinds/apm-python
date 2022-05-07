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
from opentelemetry.sdk.trace import (
    sampling,
    TracerProvider
)
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from solarwinds_apm import DEFAULT_SW_TRACES_EXPORTER
from solarwinds_apm.extension.oboe import Reporter
from solarwinds_apm.response_propagator import SolarWindsTraceResponsePropagator

logger = logging.getLogger(__name__)

class SolarWindsConfigurator(_OTelSDKConfigurator):
    """OpenTelemetry Configurator for initializing SolarWinds-reporting SDK components"""

    # Cannot set as env default because not part of OTel Python _KNOWN_SAMPLERS
    # https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-sdk/src/opentelemetry/sdk/trace/sampling.py#L364-L380
    _DEFAULT_SW_TRACES_SAMPLER = "solarwinds_sampler"

    def _configure(self, **kwargs):
        """Configure OTel sampler, exporter, propagator, response propagator"""
        reporter = self._initialize_solarwinds_reporter()
        self._configure_sampler()
        self._configure_exporter(reporter)
        self._configure_propagator()
        self._configure_response_propagator()

    def _configure_sampler(self):
        """Always configure SolarWinds OTel sampler"""
        try:
            sampler = load_entry_point(
                "solarwinds_apm",
                "opentelemetry_traces_sampler",
                self._DEFAULT_SW_TRACES_SAMPLER
            )()
        except:
            logger.exception(
                "Failed to load configured sampler {}".format(
                    self._DEFAULT_SW_TRACES_SAMPLER
                )
            )
            raise
        trace.set_tracer_provider(
            TracerProvider(sampler=sampler)
        )

    def _configure_exporter(self, reporter=None):
        """Configure SolarWinds or env-specified OTel span exporter.
        Initialization of SolarWinds exporter requires a liboboe reporter."""
        exporter = None
        environ_exporter_name = environ.get(OTEL_TRACES_EXPORTER)

        if environ_exporter_name == DEFAULT_SW_TRACES_EXPORTER:
            try:
                exporter = load_entry_point(
                    "solarwinds_apm",
                    "opentelemetry_traces_exporter",
                    environ_exporter_name
                )(reporter)
            except:
                logger.exception(
                    "Failed to load configured exporter {} with reporter".format(
                        environ_exporter_name
                    )
                )
                raise
        else:
            try:
                exporter = next(
                    iter_entry_points(
                        "opentelemetry_traces_exporter",
                        environ_exporter_name
                    )
                ).load()()
            except:
                logger.exception(
                    "Failed to load configured exporter {}".format(
                        environ_exporter_name
                    )
                )
                raise
        span_processor = BatchSpanProcessor(exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)

    def _configure_propagator(self):
        """Configure CompositePropagator with SolarWinds and other propagators"""
        propagators = []
        environ_propagators_names = environ.get(OTEL_PROPAGATORS).split(",")
        for propagator_name in environ_propagators_names:
            try:
                propagators.append(
                    next(
                        iter_entry_points("opentelemetry_propagator", propagator_name)
                    ).load()()
                )
            except Exception:
                logger.exception(
                    "Failed to load configured propagator {}".format(
                        propagator_name
                    )
                )
                raise
        set_global_textmap(CompositePropagator(propagators))

    def _configure_response_propagator(self):
        # Set global HTTP response propagator
        set_global_response_propagator(SolarWindsTraceResponsePropagator())

    def _initialize_solarwinds_reporter(self) -> Reporter:
        """Initialize SolarWinds reporter used by sampler and exporter. This establishes collector and sampling settings in a background thread."""
        log_level = environ.get('SOLARWINDS_DEBUG_LEVEL', 3)
        try:
            log_level = int(log_level)
        except ValueError:
            log_level = 3
        # TODO make some of these customizable
        return Reporter(
            hostname_alias='',
            log_level=log_level,
            log_file_path='',
            max_transactions=-1,
            max_flush_wait_time=-1,
            events_flush_interval=-1,
            max_request_size_bytes=-1,
            reporter='ssl',
            host=environ.get('SOLARWINDS_COLLECTOR', ''),
            service_key=environ.get('SOLARWINDS_SERVICE_KEY', ''),
            trusted_path='',
            buffer_size=-1,
            trace_metrics=-1,
            histogram_precision=-1,
            token_bucket_capacity=-1,
            token_bucket_rate=-1,
            file_single=0,
            ec2_metadata_timeout=1000,
            grpc_proxy='',
            stdout_clear_nonblocking=0,
            is_grpc_clean_hack_enabled=False,
            w3c_trace_format=1,
        )
