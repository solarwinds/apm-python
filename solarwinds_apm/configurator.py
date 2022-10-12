"""Module to initialize OpenTelemetry SDK components and liboboe to work with SolarWinds backend"""

import logging
from os import environ
from pkg_resources import (
    iter_entry_points,
    load_entry_point
)
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER
)
from opentelemetry.instrumentation.propagators import set_global_response_propagator
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk._configuration import _OTelSDKConfigurator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from solarwinds_apm.apm_constants import (
    INTL_SWO_DEFAULT_PROPAGATORS,
    INTL_SWO_DEFAULT_TRACES_EXPORTER,
    INTL_SWO_SUPPORT_EMAIL,
)
from solarwinds_apm import apm_logging
from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager
from solarwinds_apm.response_propagator import SolarWindsTraceResponsePropagator
from solarwinds_apm.inbound_metrics_processor import SolarWindsInboundMetricsSpanProcessor

if TYPE_CHECKING:
    from solarwinds_apm.extension.oboe import Reporter

solarwinds_apm_logger = apm_logging.logger
logger = logging.getLogger(__name__)

class SolarWindsConfigurator(_OTelSDKConfigurator):
    """OpenTelemetry Configurator for initializing APM logger and SolarWinds-reporting SDK components"""

    # Cannot set as env default because not part of OTel Python _KNOWN_SAMPLERS
    # https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-sdk/src/opentelemetry/sdk/trace/sampling.py#L364-L380
    _DEFAULT_SW_TRACES_SAMPLER = "solarwinds_sampler"

    def _configure(self, **kwargs: int) -> None:
        """Configure SolarWinds APM and OTel components"""
        apm_txname_manager = SolarWindsTxnNameManager()
        apm_config = SolarWindsApmConfig()
        reporter = self._initialize_solarwinds_reporter(apm_config)
        self._configure_otel_components(apm_txname_manager, apm_config, reporter)

    def _configure_otel_components(
        self,
        apm_txname_manager: SolarWindsTxnNameManager,
        apm_config: SolarWindsApmConfig,
        reporter: "Reporter",
    ) -> None:
        """Configure OTel sampler, exporter, propagator, response propagator"""
        self._configure_sampler(apm_config)
        if apm_config.agent_enabled:
            self._configure_metrics_span_processor(
                apm_txname_manager,
                apm_config,
            )
            self._configure_exporter(
                reporter,
                apm_txname_manager,
                apm_config.agent_enabled,
            )
            self._configure_propagator()
            self._configure_response_propagator()
        else:
            # Warning: This may still set OTEL_PROPAGATORS if set because OTel API
            logger.error("Tracing disabled. Not setting propagators.")

    def _configure_sampler(
        self,
        apm_config: SolarWindsApmConfig,
    ) -> None:
        """Always configure SolarWinds OTel sampler, or none if disabled"""
        if not apm_config.agent_enabled:
            logger.error("Tracing disabled. Using OTel no-op tracer provider.")
            trace.set_tracer_provider(
                trace.NoOpTracerProvider()
            )
            return
        try:
            sampler = load_entry_point(
                "solarwinds_apm",
                "opentelemetry_traces_sampler",
                self._DEFAULT_SW_TRACES_SAMPLER
            )(apm_config)
        except:
            logger.exception(
                "Failed to load configured sampler {}. "
                "Please reinstall or contact {}.".format(
                    self._DEFAULT_SW_TRACES_SAMPLER,
                    INTL_SWO_SUPPORT_EMAIL,
                )
            )
            raise
        trace.set_tracer_provider(
            TracerProvider(sampler=sampler)
        )

    def _configure_metrics_span_processor(
        self,
        apm_txname_manager: SolarWindsTxnNameManager,
        apm_config: SolarWindsApmConfig,
    ) -> None:
        """Configure SolarWindsInboundMetricsSpanProcessor"""
        trace.get_tracer_provider().add_span_processor(
            SolarWindsInboundMetricsSpanProcessor(
                apm_txname_manager,
                apm_config.agent_enabled,
            )
        )

    def _configure_exporter(
        self,
        reporter: "Reporter",
        apm_txname_manager: SolarWindsTxnNameManager,
        agent_enabled: bool = True,
    ) -> None:
        """Configure SolarWinds OTel span exporters, defaults or environment
        configured, or none if agent disabled. Initialization of SolarWinds
        exporter requires a liboboe reporter and agent_enabled flag."""
        if not agent_enabled:
            logger.error("Tracing disabled. Cannot set span_processor.")
            return

        # SolarWindsDistro._configure does setdefault so this shouldn't
        # be None, but safer and more explicit this way
        environ_exporter_names = environ.get(
            OTEL_TRACES_EXPORTER,
            INTL_SWO_DEFAULT_TRACES_EXPORTER,
        ).split(",")

        for exporter_name in environ_exporter_names:
            exporter = None
            try:
                if exporter_name == INTL_SWO_DEFAULT_TRACES_EXPORTER:
                    exporter = load_entry_point(
                        "solarwinds_apm",
                        "opentelemetry_traces_exporter",
                        exporter_name
                    )(reporter, apm_txname_manager, agent_enabled)
                else:
                    exporter = next(
                        iter_entry_points(
                            "opentelemetry_traces_exporter",
                            exporter_name
                        )
                    ).load()()
            except:
                # At this point any non-default OTEL_TRACES_EXPORTER has 
                # been checked by ApmConfig so exception here means 
                # something quite wrong
                logger.exception(
                    "Failed to load configured exporter {}. "
                    "Please reinstall or contact {}.".format(
                        exporter_name,
                        INTL_SWO_SUPPORT_EMAIL,
                    )
                )
                raise
            logger.debug("Setting trace with BatchSpanProcessor using {}".format(exporter_name))
            span_processor = BatchSpanProcessor(exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

    def _configure_propagator(self) -> None:
        """Configure CompositePropagator with SolarWinds and other propagators, default or environment configured"""
        propagators = []

        # SolarWindsDistro._configure does setdefault so this shouldn't
        # be None, but safer and more explicit this way
        environ_propagators_names = environ.get(
            OTEL_PROPAGATORS,
            ",".join(INTL_SWO_DEFAULT_PROPAGATORS),
        ).split(",")

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
        logger.debug("Setting CompositePropagator with {}".format(environ_propagators_names))
        set_global_textmap(CompositePropagator(propagators))

    def _configure_response_propagator(self) -> None:
        # Set global HTTP response propagator
        set_global_response_propagator(SolarWindsTraceResponsePropagator())

    def _initialize_solarwinds_reporter(
        self,
        apm_config: SolarWindsApmConfig,
    ) -> "Reporter":
        """Initialize SolarWinds reporter used by sampler and exporter, using SolarWindsApmConfig. This establishes collector and sampling settings in a background thread."""
        if apm_config.agent_enabled:
            from solarwinds_apm.extension.oboe import Reporter
        else:
            from solarwinds_apm.apm_noop import Reporter

        return Reporter(
            hostname_alias=apm_config.get("hostname_alias"),
            log_level=apm_config.get("debug_level"),
            log_file_path=apm_config.get("logname"),
            max_transactions=apm_config.get("max_transactions"),
            max_flush_wait_time=apm_config.get("max_flush_wait_time"),
            events_flush_interval=apm_config.get("events_flush_interval"),
            max_request_size_bytes=apm_config.get("max_request_size_bytes"),
            reporter=apm_config.get("reporter"),
            host=apm_config.get("collector"),
            service_key=apm_config.get("service_key"),
            trusted_path=apm_config.get("trustedpath"),
            buffer_size=apm_config.get("bufsize"),
            trace_metrics=apm_config.get("trace_metrics"),
            histogram_precision=apm_config.get("histogram_precision"),
            token_bucket_capacity=apm_config.get("token_bucket_capacity"),
            token_bucket_rate=apm_config.get("token_bucket_rate"),
            file_single=apm_config.get("reporter_file_single"),
            ec2_metadata_timeout=apm_config.get("ec2_metadata_timeout"),
            grpc_proxy=apm_config.get("proxy"),
            stdout_clear_nonblocking=0,
            is_grpc_clean_hack_enabled=apm_config.get("is_grpc_clean_hack_enabled"),
            w3c_trace_format=1,
            metric_format=apm_config.metric_format,
        )
