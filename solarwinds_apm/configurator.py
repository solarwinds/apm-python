"""Module to initialize OpenTelemetry SDK components and liboboe to work with SolarWinds backend"""

import logging
import os
import sys
import time

from opentelemetry import trace
from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER,
)
from opentelemetry.instrumentation.propagators import (
    set_global_response_propagator,
)
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk._configuration import _OTelSDKConfigurator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pkg_resources import iter_entry_points, load_entry_point

from solarwinds_apm import apm_logging
from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.apm_constants import (
    INTL_SWO_DEFAULT_PROPAGATORS,
    INTL_SWO_DEFAULT_TRACES_EXPORTER,
    INTL_SWO_SUPPORT_EMAIL,
)
from solarwinds_apm.apm_noop import Reporter as NoopReporter
from solarwinds_apm.apm_oboe_codes import OboeReporterCode
from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager
from solarwinds_apm.extension.oboe import Config, Context, Metadata, Reporter
from solarwinds_apm.inbound_metrics_processor import (
    SolarWindsInboundMetricsSpanProcessor,
)
from solarwinds_apm.response_propagator import (
    SolarWindsTraceResponsePropagator,
)
from solarwinds_apm.version import __version__

solarwinds_apm_logger = apm_logging.logger
logger = logging.getLogger(__name__)


class SolarWindsConfigurator(_OTelSDKConfigurator):
    """OpenTelemetry Configurator for initializing APM logger and SolarWinds-reporting SDK components"""

    # Agent process start time, which is supposed to be a constant. -- don't modify it.
    _AGENT_START_TIME = time.time() * 1e6
    # Cannot set as env default because not part of OTel Python _KNOWN_SAMPLERS
    # https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-sdk/src/opentelemetry/sdk/trace/sampling.py#L364-L380
    _DEFAULT_SW_TRACES_SAMPLER = "solarwinds_sampler"

    def _configure(self, **kwargs: int) -> None:
        """Configure SolarWinds APM and OTel components"""
        apm_txname_manager = SolarWindsTxnNameManager()
        apm_config = SolarWindsApmConfig()
        reporter = self._initialize_solarwinds_reporter(apm_config)
        self._configure_otel_components(
            apm_txname_manager, apm_config, reporter
        )
        # Report an status event after everything is done.
        self._report_init_event(reporter, apm_config)

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
            trace.set_tracer_provider(trace.NoOpTracerProvider())
            return
        try:
            sampler = load_entry_point(
                "solarwinds_apm",
                "opentelemetry_traces_sampler",
                self._DEFAULT_SW_TRACES_SAMPLER,
            )(apm_config)
        except Exception as ex:
            logger.exception("A exception was raised: %s", ex)
            logger.exception(
                "Failed to load configured sampler %s. "
                "Please reinstall or contact %s.",
                self._DEFAULT_SW_TRACES_SAMPLER,
                INTL_SWO_SUPPORT_EMAIL,
            )
            raise
        trace.set_tracer_provider(TracerProvider(sampler=sampler))

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
        environ_exporter_names = os.environ.get(
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
                        exporter_name,
                    )(reporter, apm_txname_manager, agent_enabled)
                else:
                    exporter = next(
                        iter_entry_points(
                            "opentelemetry_traces_exporter", exporter_name
                        )
                    ).load()()
            except Exception as ex:
                logger.exception("A exception was raised: %s", ex)
                # At this point any non-default OTEL_TRACES_EXPORTER has
                # been checked by ApmConfig so exception here means
                # something quite wrong
                logger.exception(
                    "Failed to load configured exporter %s. "
                    "Please reinstall or contact %s.",
                    exporter_name,
                    INTL_SWO_SUPPORT_EMAIL,
                )
                raise
            logger.debug(
                "Setting trace with BatchSpanProcessor using %s",
                exporter_name,
            )
            span_processor = BatchSpanProcessor(exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

    def _configure_propagator(self) -> None:
        """Configure CompositePropagator with SolarWinds and other propagators, default or environment configured"""
        propagators = []

        # SolarWindsDistro._configure does setdefault so this shouldn't
        # be None, but safer and more explicit this way
        environ_propagators_names = os.environ.get(
            OTEL_PROPAGATORS,
            ",".join(INTL_SWO_DEFAULT_PROPAGATORS),
        ).split(",")

        for propagator_name in environ_propagators_names:
            try:
                propagators.append(
                    next(
                        iter_entry_points(
                            "opentelemetry_propagator", propagator_name
                        )
                    ).load()()
                )
            except Exception:
                logger.exception(
                    "Failed to load configured propagator %s",
                    propagator_name,
                )
                raise
        logger.debug(
            "Setting CompositePropagator with %s",
            environ_propagators_names,
        )
        set_global_textmap(CompositePropagator(propagators))

    def _configure_response_propagator(self) -> None:
        # Set global HTTP response propagator
        set_global_response_propagator(SolarWindsTraceResponsePropagator())

    def _initialize_solarwinds_reporter(
        self,
        apm_config: SolarWindsApmConfig,
    ) -> "Reporter":
        """Initialize SolarWinds reporter used by sampler and exporter, using SolarWindsApmConfig. This establishes collector and sampling settings in a background thread."""
        reporter_kwargs = {
            "hostname_alias": apm_config.get("hostname_alias"),
            "log_level": apm_config.get("debug_level"),
            "log_file_path": apm_config.get("logname"),
            "max_transactions": apm_config.get("max_transactions"),
            "max_flush_wait_time": apm_config.get("max_flush_wait_time"),
            "events_flush_interval": apm_config.get("events_flush_interval"),
            "max_request_size_bytes": apm_config.get("max_request_size_bytes"),
            "reporter": apm_config.get("reporter"),
            "host": apm_config.get("collector"),
            "service_key": apm_config.get("service_key"),
            "certificates": apm_config.certificates,
            "buffer_size": apm_config.get("bufsize"),
            "trace_metrics": apm_config.get("trace_metrics"),
            "histogram_precision": apm_config.get("histogram_precision"),
            "token_bucket_capacity": apm_config.get("token_bucket_capacity"),
            "token_bucket_rate": apm_config.get("token_bucket_rate"),
            "file_single": apm_config.get("reporter_file_single"),
            "ec2_metadata_timeout": apm_config.get("ec2_metadata_timeout"),
            "grpc_proxy": apm_config.get("proxy"),
            "stdout_clear_nonblocking": 0,
            "metric_format": apm_config.metric_format,
        }

        if apm_config.agent_enabled:
            return Reporter(**reporter_kwargs)

        return NoopReporter(**reporter_kwargs)

    def _report_init_event(
        self,
        reporter: "Reporter",
        apm_config: SolarWindsApmConfig,
        layer: str = "Python",
        keys: dict = None,
    ) -> None:
        """Report the APM library's init message, when reporter ready.
        Note: We keep the original "brand" keynames with AppOptics, instead of SolarWinds"""
        reporter_ready = False
        if reporter.init_status in (
            OboeReporterCode.OBOE_INIT_OK,
            OboeReporterCode.OBOE_INIT_ALREADY_INIT,
        ):
            reporter_ready = apm_config.agent_enabled
        if not reporter_ready:
            if apm_config.agent_enabled:
                logger.error(
                    "Failed to initialize the reporter, error code=%s (%s). Not sending init message.",
                    reporter.init_status,
                    OboeReporterCode.get_text_code(reporter.init_status),
                )
            else:
                logger.warning("Agent disabled. Not sending init message.")
            return

        version_keys = {}
        version_keys["__Init"] = "True"
        # liboboe adds key Hostname for us
        try:
            version_keys[
                "Python.Version"
            ] = f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
        except (AttributeError, IndexError) as ex:
            logger.warning("Could not retrieve Python version: %s", ex)

        version_keys["Python.AppOptics.Version"] = __version__
        version_keys[
            "Python.AppOpticsExtension.Version"
        ] = Config.getVersionString()

        # Attempt to get the following info if we are in a regular file.
        # Else the path operations fail, for example when the agent is running
        # in an application zip archive.
        if os.path.isfile(__file__):
            version_keys["Python.InstallDirectory"] = os.path.dirname(__file__)
            version_keys["Python.InstallTimestamp"] = os.path.getmtime(
                __file__
            )  # in sec since epoch
        else:
            version_keys["Python.InstallDirectory"] = "Unknown"
            version_keys["Python.InstallTimestamp"] = 0
        version_keys["Python.LastRestart"] = self._AGENT_START_TIME  # in usec

        if keys:
            version_keys.update(keys)

        md = Metadata.makeRandom(True)
        if not md.isValid():
            logger.warning(
                "Warning: Could not generate Metadata for reporter init. Skipping init message."
            )
            return
        Context.set(md)
        evt = md.createEvent()
        evt.addInfo("Label", "single")
        evt.addInfo("Layer", layer)
        for ver_k, ver_v in version_keys.items():
            evt.addInfo(ver_k, ver_v)
        reporter.sendStatus(evt)
