# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Module to initialize OpenTelemetry SDK components for SolarWinds backend"""

import importlib
import logging
import math
import os
import platform
import sys
from typing import Any, Dict, Optional, Type, Union

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry._logs._internal import NoOpLoggerProvider
from opentelemetry.environment_variables import (
    OTEL_METRICS_EXPORTER,
    OTEL_PROPAGATORS,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as GrpcSpanExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HttpSpanExporter,
)
from opentelemetry.instrumentation.dependencies import (
    get_dist_dependency_conflicts,
)
from opentelemetry.instrumentation.environment_variables import (
    OTEL_PYTHON_DISABLED_INSTRUMENTATIONS,
)
from opentelemetry.instrumentation.propagators import (
    set_global_response_propagator,
)
from opentelemetry.metrics import set_meter_provider
from opentelemetry.metrics._internal import NoOpMeterProvider
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk._configuration import (
    _get_exporter_names,
    _import_exporters,
    _init_logging,
    _OTelSDKConfigurator,
)
from opentelemetry.sdk.environment_variables import (
    _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED,
    OTEL_EXPORTER_OTLP_PROTOCOL,
    OTEL_EXPORTER_OTLP_TRACES_PROTOCOL,
)
from opentelemetry.sdk.metrics import (
    Counter,
    Histogram,
    MeterProvider,
    ObservableCounter,
    ObservableGauge,
    ObservableUpDownCounter,
    UpDownCounter,
)
from opentelemetry.sdk.metrics.export import (
    AggregationTemporality,
    MetricExporter,
    MetricReader,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor,
    SpanExporter,
)
from opentelemetry.sdk.trace.id_generator import IdGenerator
from opentelemetry.sdk.trace.sampling import Sampler
from opentelemetry.trace import NoOpTracerProvider, set_tracer_provider
from opentelemetry.util._importlib_metadata import entry_points, version

from solarwinds_apm import apm_logging
from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.apm_constants import INTL_SWO_DEFAULT_PROPAGATORS
from solarwinds_apm.exporter import SolarWindsSpanExporter

# from solarwinds_apm.apm_oboe_codes import OboeReporterCode
from solarwinds_apm.response_propagator import (
    SolarWindsTraceResponsePropagator,
)
from solarwinds_apm.sampler import ParentBasedSwSampler
from solarwinds_apm.trace import (
    ResponseTimeProcessor,
    ServiceEntrySpanProcessor,
)
from solarwinds_apm.tracer_provider import SolarwindsTracerProvider
from solarwinds_apm.version import __version__

# if TYPE_CHECKING:
#     from solarwinds_apm.extension.oboe import Event, OboeAPI, Reporter

_SPAN_EXPORTER_BY_OTLP_PROTOCOL = {
    "grpc": GrpcSpanExporter,
    "http/protobuf": HttpSpanExporter,
}

solarwinds_apm_logger = apm_logging.logger
logger = logging.getLogger(__name__)


class SolarWindsConfigurator(_OTelSDKConfigurator):
    """OpenTelemetry Configurator for initializing APM logger and SolarWinds-reporting SDK components"""

    def __init__(self) -> None:
        super().__init__()
        self.apm_config = SolarWindsApmConfig()

    def _configure(self, **kwargs: int) -> None:
        """Configure SolarWinds APM and OTel components"""
        if not self.apm_config.agent_enabled:
            # ApmConfig will log a more informative Info message if disabled
            logger.debug(
                "SWO APM agent disabled. Not configuring OpenTelemetry."
            )
            set_tracer_provider(NoOpTracerProvider())
            set_meter_provider(NoOpMeterProvider())
            set_logger_provider(NoOpLoggerProvider())
            return

        # Duplicated from _OTelSDKConfigurator in order to support custom settings
        trace_exporter_names = kwargs.get("trace_exporter_names", [])
        metric_exporter_names = kwargs.get("metric_exporter_names", [])
        log_exporter_names = kwargs.get("log_exporter_names", [])

        span_exporters, metric_exporters, log_exporters = _import_exporters(
            trace_exporter_names + _get_exporter_names("traces"),
            metric_exporter_names + _get_exporter_names("metrics"),
            log_exporter_names + _get_exporter_names("logs"),
        )

        # Custom initialization of OTel components
        apm_sampler = ParentBasedSwSampler(
            self.apm_config,
            None,  # TODO NH-104999 remove later
        )
        apm_resource = Resource.create(
            {
                "sw.apm.version": __version__,
                "sw.data.module": "apm",
                "service.name": self.apm_config.service_name,
            }
        )
        self._custom_init_tracing(
            exporters=span_exporters,
            id_generator=kwargs.get("id_generator"),
            sampler=apm_sampler,
            resource=apm_resource,
        )
        self._custom_init_metrics(
            exporters_or_readers=metric_exporters,
            resource=apm_resource,
        )

        # Only emit log event telemetry (auto-instrument logs) if feature enabled,
        # with settings precedence: OTEL_* > SW_APM_EXPORT_LOGS_ENABLED.
        # TODO NH-107164 drop support of SW config, and super() will only check OTEL config
        setup_logging_handler = False
        # We don't set a default, so this could be None
        otel_log_enabled = SolarWindsApmConfig.convert_to_bool(
            os.environ.get(_OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED)
        )
        # SW config is False by default
        sw_log_enabled = self.apm_config.get("export_logs_enabled")
        if otel_log_enabled is not None:
            if otel_log_enabled is True:
                setup_logging_handler = True
        elif sw_log_enabled:
            setup_logging_handler = True

        _init_logging(log_exporters, apm_resource, setup_logging_handler)

        # Set up additional custom SW components
        self._configure_service_entry_span_processor()
        self._configure_response_time_processor()
        self._configure_propagator()
        self._configure_response_propagator()

    # TODO rm disable when Python 3.8 dropped
    # pylint: disable=consider-alternative-union-syntax,deprecated-typing-alias
    def _custom_init_tracing(
        self,
        exporters: Dict[str, Type[SpanExporter]],
        id_generator: Optional[IdGenerator] = None,
        sampler: Optional[Sampler] = None,
        resource: Optional[Resource] = None,
    ):
        """APM SWO custom span export init, based on _OTelSDKConfigurator"""
        provider = SolarwindsTracerProvider(
            id_generator=id_generator,
            sampler=sampler,
            resource=resource,
        )
        set_tracer_provider(provider)

        for _, exporter_class in exporters.items():
            # TODO NH-107047 Remove this warning, class, entry point
            if exporter_class == SolarWindsSpanExporter:
                logger.warning(
                    "SolarWindsSpanExporter is deprecated; configuration ignored. Initializing OTLP exporter instead."
                )
                # Check env vars for OTLP traces protocol (grpc/http),
                # which could be setdefault from custom distro,
                # to select correct OTLP exporter. Else OTLP HTTP default.
                otlp_protocol = os.environ.get(
                    OTEL_EXPORTER_OTLP_TRACES_PROTOCOL
                ) or os.environ.get(OTEL_EXPORTER_OTLP_PROTOCOL)
                if not otlp_protocol:
                    otlp_protocol = "http/protobuf"
                otlp_protocol = otlp_protocol.strip()

                if otlp_protocol in _SPAN_EXPORTER_BY_OTLP_PROTOCOL:
                    exporter_class = _SPAN_EXPORTER_BY_OTLP_PROTOCOL[
                        otlp_protocol
                    ]
                else:
                    logger.debug(
                        "Unknown OTLP protocol; defaulting to HTTP SpanExporter."
                    )
                    exporter_class = HttpSpanExporter

            exporter_args = {}
            if self.apm_config.is_lambda:
                provider.add_span_processor(
                    SimpleSpanProcessor(exporter_class(**exporter_args))
                )
            else:
                provider.add_span_processor(
                    BatchSpanProcessor(exporter_class(**exporter_args))
                )

    def _custom_init_metrics(
        self,
        exporters_or_readers: Dict[
            str, Union[Type[MetricExporter], Type[MetricReader]]
        ],
        resource: Optional[Resource] = None,
    ):
        """APM SWO custom metrics export init, based on _OTelSDKConfigurator"""
        metric_readers = []

        for _, exporter_or_reader_class in exporters_or_readers.items():
            exporter_args = {
                "preferred_temporality": {
                    Counter: AggregationTemporality.DELTA,
                    UpDownCounter: AggregationTemporality.DELTA,
                    Histogram: AggregationTemporality.DELTA,
                    ObservableCounter: AggregationTemporality.DELTA,
                    ObservableUpDownCounter: AggregationTemporality.DELTA,
                    ObservableGauge: AggregationTemporality.DELTA,
                }
            }

            if issubclass(exporter_or_reader_class, MetricReader):
                metric_readers.append(
                    exporter_or_reader_class(**exporter_args)
                )
            elif self.apm_config.is_lambda:
                # Inf interval to not invoke periodic collection
                metric_readers.append(
                    PeriodicExportingMetricReader(
                        exporter_or_reader_class(**exporter_args),
                        export_interval_millis=math.inf,
                    )
                )
            else:
                # Use default interval 60s else OTEL_METRIC_EXPORT_INTERVAL
                metric_readers.append(
                    PeriodicExportingMetricReader(
                        exporter_or_reader_class(**exporter_args),
                    )
                )

        provider = MeterProvider(
            resource=resource, metric_readers=metric_readers
        )
        set_meter_provider(provider)

    def _configure_service_entry_span_processor(
        self,
    ) -> None:
        """Configure ServiceEntrySpanProcessor"""
        trace.get_tracer_provider().add_span_processor(
            ServiceEntrySpanProcessor()
        )

    def _configure_response_time_processor(
        self,
    ) -> None:
        """Configure ResponseTimeProcessor if metrics exporters are configured and set up
        i.e. by _configure_metrics_exporter
        """
        # SolarWindsDistro._configure does setdefault before this is called
        environ_exporter = os.environ.get(
            OTEL_METRICS_EXPORTER,
        )
        if not environ_exporter:
            logger.debug(
                "No OTEL_METRICS_EXPORTER set, skipping init of metrics processors"
            )
            return

        trace.get_tracer_provider().add_span_processor(
            ResponseTimeProcessor(
                self.apm_config,
            )
        )

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
                        iter(
                            entry_points(
                                group="opentelemetry_propagator",
                                name=propagator_name,
                            )
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
    ):
        """Initialize SolarWinds reporter used by sampler and exporter, using SolarWindsApmConfig.
        This establishes collector and sampling settings in a background thread.

        Note: if config's extension is no-op, this has no effect."""
        return None
        # reporter_kwargs = {
        #     "hostname_alias": apm_config.get("hostname_alias"),
        #     "log_type": apm_config.get("log_type"),
        #     "log_level": apm_config.get("debug_level"),
        #     "log_file_path": apm_config.get("log_filepath"),
        #     "max_transactions": apm_config.get("max_transactions"),
        #     "max_flush_wait_time": apm_config.get("max_flush_wait_time"),
        #     "events_flush_interval": apm_config.get("events_flush_interval"),
        #     "max_request_size_bytes": apm_config.get("max_request_size_bytes"),
        #     "reporter": apm_config.get("reporter"),
        #     "host": apm_config.get("collector"),
        #     "service_key": apm_config.get("service_key"),
        #     "certificates": apm_config.certificates,
        #     "buffer_size": apm_config.get("bufsize"),
        #     "trace_metrics": apm_config.get("trace_metrics"),
        #     "histogram_precision": apm_config.get("histogram_precision"),
        #     "token_bucket_capacity": -1,  # always unset
        #     "token_bucket_rate": -1,  # always unset
        #     "file_single": apm_config.get("reporter_file_single"),
        #     "stdout_clear_nonblocking": 0,
        #     "metric_format": apm_config.metric_format,
        # }
        #
        # return apm_config.extension.Reporter(**reporter_kwargs)

    # pylint: disable=too-many-branches,too-many-statements
    def _add_all_instrumented_python_framework_versions(
        self,
        version_keys,
    ) -> dict:
        """Updates version_keys with versions of Python frameworks that have been
        instrumented with installed (bootstrapped) OTel instrumentation libraries.
        Borrowed from opentelemetry-instrumentation sitecustomize. Intended for
        creating init event.

        Example output:
        {
            "Python.Urllib.Version": "3.9",
            "Python.Requests.Version": "2.28.1",
            "Python.Django.Version": "4.1.4",
            "Python.Psycopg2.Version": "2.9.5 (dt dec pq3 ext lo64)",
            "Python.Sqlite3.Version": "3.34.1",
            "Python.Logging.Version": "0.5.1.2",
        }
        """
        package_to_exclude = os.environ.get(
            OTEL_PYTHON_DISABLED_INSTRUMENTATIONS, []
        )
        if isinstance(package_to_exclude, str):
            package_to_exclude = package_to_exclude.split(",")
            package_to_exclude = [x.strip() for x in package_to_exclude]

        for entry_point in iter(
            entry_points(group="opentelemetry_instrumentor")
        ):
            if entry_point.name in package_to_exclude:
                logger.debug(
                    "Skipping version lookup for library %s because excluded",
                    entry_point.name,
                )
                continue

            try:
                conflict = get_dist_dependency_conflicts(entry_point.dist)
                if conflict:
                    # TODO Unnecessary tortoiseorm bootstrap will be fixed upstream
                    # https://github.com/open-telemetry/opentelemetry-python-contrib/pull/2409
                    if (
                        "tortoise-orm" in conflict.required
                        and conflict.found is None
                    ):
                        logger.debug(
                            "Init event version lookup for library %s skipped due to known pydantic/tortoiseorm bootstrap conflict: %s",
                            entry_point.name,
                            conflict,
                        )
                    else:
                        logger.debug(
                            "Init event version lookup for library %s skipped due to conflict: %s",
                            entry_point.name,
                            conflict,
                        )
                    continue
            except Exception as ex:  # pylint: disable=broad-except
                logger.debug(
                    "Init event version conflict check of %s failed, so skipping: %s",
                    entry_point.name,
                    ex,
                )
                continue

            # Set up Instrumented Library Versions KVs with several special cases
            entry_point_name = entry_point.name
            # Some OTel instrumentation library entry point names are not exactly
            # the same as their corresponding instrumented libraries
            # https://github.com/open-telemetry/opentelemetry-python-contrib/blob/main/instrumentation/README.md
            if entry_point_name == "aiohttp-client":
                entry_point_name = "aiohttp"
            # Both client/server instrumentors instrument `aiohttp`
            # so key is potentially overwritten, not duplicated
            elif entry_point_name == "aiohttp-server":
                entry_point_name = "aiohttp"
            elif entry_point_name == "aio-pika":
                entry_point_name = "aio_pika"
            elif "grpc_" in entry_point_name:
                entry_point_name = "grpc"
            elif entry_point_name == "system_metrics":
                entry_point_name = "psutil"
            elif entry_point_name == "tortoiseorm":
                entry_point_name = "tortoise"

            # Remove any underscores and convert to UpperCamelCase
            # e.g. aio_pika becomes Python.AioPika.Version
            middle = "".join(
                part.capitalize() for part in entry_point_name.split("_")
            )
            instr_key = f"Python.{middle}.Version"
            try:
                # There is no mysql version, but mysql.connector version
                if entry_point_name == "mysql":
                    importlib.import_module(f"{entry_point_name}.connector")
                # urllib has a rich complex history
                elif entry_point_name == "urllib":
                    importlib.import_module(f"{entry_point_name}.request")
                else:
                    importlib.import_module(entry_point_name)

                # some Python frameworks don't have top-level __version__
                if entry_point_name in self._STDLIB_PKGS:
                    logger.debug(
                        "Using Python version for library %s because part of Python standard library in Python 3.8+",
                        entry_point.name,
                    )
                    version_keys[instr_key] = platform.python_version()
                # elasticsearch gives a version as (8, 5, 3) not 8.5.3
                elif entry_point_name == "elasticsearch":
                    version_tuple = sys.modules[entry_point_name].__version__
                    version_keys[instr_key] = ".".join(
                        [str(d) for d in version_tuple]
                    )
                elif entry_point_name == "mysql":
                    version_keys[instr_key] = sys.modules[
                        f"{entry_point_name}.connector"
                    ].__version__
                elif entry_point_name == "pyramid":
                    version_keys[instr_key] = version(entry_point_name)
                elif entry_point_name == "sqlite3":
                    version_keys[instr_key] = sys.modules[
                        entry_point_name
                    ].sqlite_version
                elif entry_point_name == "tornado":
                    version_keys[instr_key] = sys.modules[
                        entry_point_name
                    ].version
                elif entry_point_name == "urllib":
                    version_keys[instr_key] = sys.modules[
                        f"{entry_point_name}.request"
                    ].__version__
                else:
                    version_keys[instr_key] = sys.modules[
                        entry_point_name
                    ].__version__

            except (AttributeError, ImportError) as ex:
                # could not import package for whatever reason
                logger.warning(
                    "Version lookup of %s failed, so skipping: %s",
                    entry_point_name,
                    ex,
                )

        return version_keys

    # pylint: disable=too-many-locals
    def _create_init_event(
        self,
        reporter,
        apm_config: SolarWindsApmConfig,
        layer: str = "Python",
        keys: dict = None,
    ) -> Any:
        return None

    #     """Create a Reporter init event if the reporter is ready."""
    #     if apm_config.is_lambda:
    #         logger.debug("Skipping init event in lambda")
    #         return None
    #
    #     reporter_ready = False
    #     if reporter.init_status in (
    #         OboeReporterCode.OBOE_INIT_OK,
    #         OboeReporterCode.OBOE_INIT_ALREADY_INIT,
    #     ):
    #         reporter_ready = apm_config.agent_enabled
    #     if not reporter_ready:
    #         if apm_config.agent_enabled:
    #             logger.error(
    #                 "Failed to initialize the reporter, error code=%s (%s). Not sending init message.",
    #                 reporter.init_status,
    #                 OboeReporterCode.get_text_code(reporter.init_status),
    #             )
    #         else:
    #             logger.warning("Agent disabled. Not sending init message.")
    #         return None
    #
    #     version_keys = {}
    #     version_keys["__Init"] = True
    #
    #     # Use configured Resource attributes to set telemetry.sdk.*
    #     resource_attributes = (
    #         trace.get_tracer_provider()
    #         .get_tracer(__name__)
    #         .resource.attributes
    #     )
    #     for ra_k, ra_v in resource_attributes.items():
    #         # Do not include OTEL SERVICE_NAME in __Init message
    #         if ra_k != SERVICE_NAME:
    #             version_keys[ra_k] = ra_v
    #
    #     # liboboe adds key Hostname for us
    #     try:
    #         version_keys["process.runtime.version"] = (
    #             f"{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}"
    #         )
    #     except (AttributeError, IndexError) as ex:
    #         logger.warning("Could not retrieve Python version: %s", ex)
    #     version_keys["process.runtime.name"] = sys.implementation.name
    #     version_keys["process.runtime.description"] = sys.version
    #     version_keys["process.executable.path"] = sys.executable
    #
    #     version_keys["APM.Version"] = __version__
    #     version_keys["APM.Extension.Version"] = (
    #         apm_config.extension.Config.getVersionString()
    #     )
    #
    #     version_keys = self._add_all_instrumented_python_framework_versions(
    #         version_keys
    #     )
    #
    #     if keys:
    #         version_keys.update(keys)
    #
    #     md = apm_config.extension.Metadata.makeRandom(True)
    #     if not md.isValid():
    #         logger.warning(
    #             "Warning: Could not generate Metadata for reporter init. Skipping init message."
    #         )
    #         return None
    #     apm_config.extension.Context.set(md)
    #     evt = md.createEvent()
    #     evt.addInfo("Layer", layer)
    #     for ver_k, ver_v in version_keys.items():
    #         evt.addInfo(ver_k, ver_v)
    #     return evt

    def _report_init_event(
        self,
        reporter,
        init_event,
    ) -> None:
        """Report the APM library's init event message and log its send status."""
        status = reporter.sendStatus(init_event)
        logger.info("Reporter initialized successfully: %s", status)
