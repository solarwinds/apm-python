# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from opentelemetry import metrics as metrics_api
from opentelemetry.sdk._logs import (
    LoggerProvider,
    LoggingHandler,
)
from opentelemetry.sdk._logs.export import (
    InMemoryLogExporter,
    SimpleLogRecordProcessor,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.test.globals_test import (
    reset_logging_globals,
    reset_metrics_globals,
)

from solarwinds_apm.extension.oboe import (
    OboeAPI,
)
from solarwinds_apm.apm_noop import (
    OboeAPI as NoOpOboeAPI,
)

from ..test_base_sw import TestBaseSw
from ..utils.exporter import InMemoryMetricExporter

class TestBaseSwOtlp(TestBaseSw):
    """
    Class for testing SolarWinds custom distro header propagation
    and span attributes calculation from decision and headers,
    in OTLP mode.
    """

    def _setup_env_vars(self):
        super()._setup_env_vars()
        os.environ["SW_APM_LEGACY"] = "false"

    def _assert_defaults(self):
        super()._assert_defaults()
        assert os.environ["OTEL_TRACES_EXPORTER"] == "otlp_proto_http"
        assert os.environ["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] == "http/protobuf"
        assert os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] == "https://otel.collector.na-01.cloud.solarwinds.com:443/v1/traces"
        assert os.environ["OTEL_EXPORTER_OTLP_TRACES_HEADERS"] == "authorization=Bearer%20foo"

    def _assert_reporter(self, reporter):
        assert isinstance(reporter, NoOpReporter)

    def _setup_test_traces_export(
        self,
        apm_config,
        configurator,
        reporter,
    ):
        oboe_api = OboeAPI()
        super()._setup_test_traces_export(
            apm_config,
            configurator,
            reporter,
            oboe_api,
        )

    def _setup_test_metrics_export(self):
        reset_metrics_globals()
        # Set InMemory exporter for testing generated telemetry
        # instead of SolarWinds/OTLP exporter
        self.memory_metric_exporter = InMemoryMetricExporter()
        reader = PeriodicExportingMetricReader(
            self.memory_metric_exporter,
            export_interval_millis=100,
        )
        self.meter_provider = MeterProvider(metric_readers=[reader])
        metrics_api.set_meter_provider(self.meter_provider)

    def _setup_test_logs_export(self):
        reset_logging_globals()
        self.logger_provider = LoggerProvider()

        # Set InMemory exporter for testing generated telemetry
        # instead of SolarWinds/OTLP exporter
        self.memory_log_exporter = InMemoryLogExporter()
        self.logger_provider.add_log_record_processor(
            SimpleLogRecordProcessor(self.memory_log_exporter)
        )
        logger = logging.getLogger("default_level")
        logger.propagate = False
        logger.addHandler(
            LoggingHandler(logger_provider=self.logger_provider)
        )

    def setUp(self):
        super().setUp()
        self._setup_test_metrics_export()
        self._setup_test_logs_export()

        # Finish setup by running Flask app instrumented with APM Python
        self._setup_instrumented_app()