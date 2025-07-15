# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

"""Module to initialize OpenTelemetry SDK components for SolarWinds backend"""

import logging
import math
import os
import uuid
from typing import Optional, Union

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry._logs._internal import NoOpLoggerProvider
from opentelemetry.environment_variables import (
    OTEL_METRICS_EXPORTER,
    OTEL_PROPAGATORS,
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
from opentelemetry.util._importlib_metadata import entry_points

from solarwinds_apm import apm_logging
from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.apm_constants import INTL_SWO_DEFAULT_PROPAGATORS
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

solarwinds_apm_logger = apm_logging.logger
logger = logging.getLogger(__name__)


class SolarWindsConfigurator(_OTelSDKConfigurator):
    """OpenTelemetry Configurator for initializing APM logger and SolarWinds-reporting SDK components"""

    def __init__(self) -> None:
        super().__init__()
        self.apm_config = SolarWindsApmConfig()

    def _swap_legacy_span_exporter(
        self,
        span_exporters: dict[str, type[SpanExporter]],
    ) -> dict:
        """Intermediary helper to swap legacy span exporter, if configured, with an OTLP exporter if not already configured."""
        if "solarwinds_exporter" in span_exporters:
            logger.warning(
                "SolarWindsSpanExporter is deprecated; configuration ignored."
            )
            del span_exporters["solarwinds_exporter"]

            if (
                "otlp_proto_http" in span_exporters
                or "otlp_proto_grpc" in span_exporters
            ):
                logger.warning("Using already-configured OTLP span exporter.")
            else:
                logger.warning("Initializing OTLP span exporter instead.")
                # Check env vars for OTLP traces protocol (grpc/http),
                # which could be setdefault from custom distro,
                # to select correct OTLP exporter. Else OTLP HTTP default.
                otlp_protocol = os.environ.get(
                    OTEL_EXPORTER_OTLP_TRACES_PROTOCOL
                ) or os.environ.get(
                    OTEL_EXPORTER_OTLP_PROTOCOL, "http/protobuf"
                )
                otlp_protocol = otlp_protocol.strip()
                if otlp_protocol not in ["http/protobuf", "grpc"]:
                    logger.debug(
                        "Unknown OTLP protocol; defaulting to HTTP to init SpanExporter."
                    )
                    otlp_protocol = "http/protobuf"

                if otlp_protocol == "http/protobuf":
                    exporter_entry_point = "otlp_proto_http"
                else:
                    exporter_entry_point = "otlp_proto_grpc"

                span_exporters[exporter_entry_point] = next(
                    iter(
                        entry_points(
                            group="opentelemetry_traces_exporter",
                            name=exporter_entry_point,
                        )
                    )
                ).load()

        return span_exporters

    def _create_apm_resource(self) -> Resource:
        """Helper to create new OTel Resource for telemetry providers"""
        apm_resource = Resource.create(
            {
                "sw.apm.version": __version__,
                "sw.data.module": "apm",
                "service.name": self.apm_config.service_name,
            }
        )
        # Prioritize service.instance.id set by any Resource Detectors
        updated_apm_resource = apm_resource.merge(
            Resource(
                {"service.instance.id": str(uuid.uuid4())}
                if "service.instance.id" not in apm_resource.attributes
                else {}
            )
        )
        return updated_apm_resource

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
        # TODO NH-107047 Remove this function, the class, and its entry point
        span_exporters = self._swap_legacy_span_exporter(span_exporters)

        # Custom initialization of OTel components
        apm_sampler = ParentBasedSwSampler(
            self.apm_config,
        )
        apm_resource = self._create_apm_resource()

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

    # TODO rm disable when Python 3.9 dropped
    # pylint: disable=consider-alternative-union-syntax
    def _custom_init_tracing(
        self,
        exporters: dict[str, type[SpanExporter]],
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
        exporters_or_readers: dict[
            str, Union[type[MetricExporter], type[MetricReader]]
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
