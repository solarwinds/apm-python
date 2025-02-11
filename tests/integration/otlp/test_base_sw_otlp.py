# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import os

from opentelemetry import metrics as metrics_api
from opentelemetry._logs import SeverityNumber
from opentelemetry.sdk._logs import (
    LoggerProvider,
    LoggingHandler,
)
from opentelemetry.sdk._logs.export import (
    InMemoryLogExporter,
    SimpleLogRecordProcessor,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from solarwinds_apm.extension.oboe import (
    OboeAPI,
)
from solarwinds_apm.apm_noop import (
    Reporter as NoOpReporter,
)

from ..test_base_sw import TestBaseSw

class TestBaseSwOtlp(TestBaseSw):
    """
    Class for testing SolarWinds custom distro header propagation
    and span attributes calculation from decision and headers,
    in OTLP mode.
    """

    @staticmethod
    def _test_trace():
        # Add logs for LoggingHandler else no logs from instrumentors alone
        logger = logging.getLogger("foo-logger")
        logger.warning("My foo log!")
        return TestBaseSw._test_trace()

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
        oboe_api = None,
    ):
        oboe_api = OboeAPI()
        super()._setup_test_traces_export(
            apm_config,
            configurator,
            reporter,
            oboe_api,
        )

    def _setup_test_metrics_reader(self):
        # Set InMemory reader instead of exporter
        self.metric_reader = InMemoryMetricReader()
        meter_provider = MeterProvider(
            metric_readers=[self.metric_reader],
        )
        metrics_api.set_meter_provider(meter_provider)

    def _setup_test_logs_export(self):
        self.logger_provider = LoggerProvider()

        # Set InMemory exporter for testing generated telemetry
        # instead of SolarWinds/OTLP exporter
        self.memory_log_exporter = InMemoryLogExporter()
        self.logger_provider.add_log_record_processor(
            SimpleLogRecordProcessor(self.memory_log_exporter)
        )
        logger = logging.getLogger("foo-logger")
        logger.propagate = False
        logger.addHandler(
            LoggingHandler(logger_provider=self.logger_provider)
        )

    def setUp(self):
        super().setUp()
        self._setup_test_metrics_reader()
        self._setup_test_logs_export()

        # Finish setup by running Flask app instrumented with APM Python
        self._setup_instrumented_app()

    def assertFlaskMetrics(self):
        """Assert server metrics generated from test app Flask instrumentation"""
        metric_data = self.metric_reader.get_metrics_data()
        metrics = metric_data.resource_metrics[0].scope_metrics[0].metrics
        self.assertEqual(len(metrics), 2)
        active_requests = metrics[0]
        self.assertEqual(
            active_requests.name,
            "http.server.active_requests",
        )
        self.assertEqual(
            active_requests.data.data_points[0].attributes,
            {"http.request.method": "GET", "url.scheme": "http"},
        )
        request_duration = metrics[1]
        self.assertEqual(
            request_duration.name,
            "http.server.request.duration",
        )
        self.assertEqual(
            request_duration.data.data_points[0].attributes,
            {
                "http.request.method": "GET",
                "url.scheme": "http",
                "network.protocol.version": "1.1",
                "http.response.status_code": 200,
                "http.route": "/test_trace/"
            },
        )

    def assertRequestsMetrics(self, status_code=True):
        """Assert client metrics from test app Requests instrumentation.
        Instrumentor sometimes does not include status_code attribute,
        i.e. decision is not-sampled."""
        metric_data = self.metric_reader.get_metrics_data()
        metrics = metric_data.resource_metrics[0].scope_metrics[1].metrics
        self.assertEqual(len(metrics), 1)
        request_duration = metrics[0]
        self.assertEqual(
            request_duration.name,
            "http.client.request.duration",
        )
        expected_attrs = {
                "http.request.method": "GET",
                "server.address": "postman-echo.com",
                "network.protocol.version": "1.1",
            }
        if status_code:
            expected_attrs.update(
                {
                    "http.response.status_code": 200,
                }
            )
        self.assertEqual(
            request_duration.data.data_points[0].attributes,
            expected_attrs,
       )

    def assertApmMetrics(self):
        """Assert APM Python response time, request counter metrics"""
        # SW response time metrics
        metric_data = self.metric_reader.get_metrics_data()
        scope = metric_data.resource_metrics[0].scope_metrics[2].scope
        self.assertEqual(
            scope.name,
            "sw.apm.request.metrics",
        )
        metrics = metric_data.resource_metrics[0].scope_metrics[2].metrics
        self.assertEqual(len(metrics), 1)
        response_time = metrics[0]
        self.assertEqual(
            response_time.name,
            "trace.service.response_time",
        )
        self.assertEqual(
            response_time.data.data_points[0].attributes,
            {
                "sw.is_error": False,
                "sw.transaction": "GET /test_trace/"
            },
        )
        self.assertEqual(
            response_time.data.aggregation_temporality,
            2,  # cumulative
        )

        # SW request count metrics
        metric_data = self.metric_reader.get_metrics_data()
        scope = metric_data.resource_metrics[0].scope_metrics[3].scope
        self.assertEqual(
            scope.name,
            "sw.apm.sampling.metrics",
        )
        metrics = metric_data.resource_metrics[0].scope_metrics[3].metrics
        self.assertEqual(len(metrics), 6)
        self.assertEqual(metrics[0].name, "trace.service.tracecount")
        self.assertEqual(metrics[1].name, "trace.service.samplecount")
        self.assertEqual(metrics[2].name, "trace.service.request_count")
        self.assertEqual(metrics[3].name, "trace.service.tokenbucket_exhaustion_count")
        self.assertEqual(metrics[4].name, "trace.service.through_trace_count")
        self.assertEqual(metrics[5].name, "trace.service.triggered_trace_count")

    def assertLogs(self):
        """Assert log events generated"""
        finished_logs = self.memory_log_exporter.get_finished_logs()
        self.assertEqual(len(finished_logs), 1)
        warning_log_record = finished_logs[0].log_record
        self.assertEqual(warning_log_record.body, "My foo log!")
        self.assertEqual(warning_log_record.severity_text, "WARN")
        self.assertEqual(
            warning_log_record.severity_number, SeverityNumber.WARN
        )
        self.assertEqual(
            finished_logs[0].instrumentation_scope.name, "foo-logger"
        )