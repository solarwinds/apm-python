# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import re

import flask
import requests
from werkzeug.test import Client
from werkzeug.wrappers import Response

from opentelemetry import trace as trace_api
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.propagate import get_global_textmap
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.test.globals_test import (
    reset_logging_globals,
    reset_metrics_globals,
    reset_trace_globals,
)
from opentelemetry.test.test_base import TestBase
from opentelemetry.util._importlib_metadata import entry_points

from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.apm_txname_manager import SolarWindsTxnNameManager
from solarwinds_apm.configurator import SolarWindsConfigurator
from solarwinds_apm.distro import SolarWindsDistro
from solarwinds_apm.propagator import SolarWindsPropagator
from solarwinds_apm.sampler import ParentBasedSwSampler
from solarwinds_apm.trace import SolarWindsOTLPMetricsSpanProcessor

class TestBaseSw(TestBase):
    """
    Base class for testing SolarWinds custom distro header propagation
    and span attributes calculation from decision and headers.
    """

    SW_SETTINGS_KEYS = [
        "BucketCapacity",
        "BucketRate",
        "SampleRate",
        "SampleSource"
    ]

    @staticmethod
    def _test_trace():
        incoming_headers = {}
        for k, v in flask.request.headers.items():
            # WSGI capitalizes incoming HTTP headers
            incoming_headers.update({k.lower(): v.lower()})

        resp = requests.get(f"http://postman-echo.com/headers")

        #  The return type must be a string, dict, tuple, Response instance, or WSGI callable
        # (not CaseInsensitiveDict)
        return {
            "traceparent": resp.request.headers["traceparent"],
            "tracestate": resp.request.headers["tracestate"],
            "incoming-headers": incoming_headers,
        }

    def _setup_entrypoints(self):
        # Based on auto_instrumentation run() and sitecustomize.py
        # Load OTel env vars entry points
        argument_otel_environment_variable = {}
        for entry_point in iter(
            entry_points(
                group="opentelemetry_environment_variables"
            )
        ):
            environment_variable_module = entry_point.load()
            for attribute in dir(environment_variable_module):
                if attribute.startswith("OTEL_"):
                    argument = re.sub(r"OTEL_(PYTHON_)?", "", attribute).lower()
                    argument_otel_environment_variable[argument] = attribute

    def _setup_env_vars(self):
        # Set APM service key - not valid, but we mock liboboe anyway
        os.environ["SW_APM_SERVICE_KEY"] = "foo:bar"

    def _assert_defaults(self):
        # Confirm default environment was set by Distro
        assert os.environ["OTEL_PROPAGATORS"] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] == "http"
        assert os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] == "http/protobuf"
        assert os.environ["OTEL_METRICS_EXPORTER"] == "otlp_proto_http"
        assert os.environ["OTEL_EXPORTER_OTLP_METRICS_PROTOCOL"] == "http/protobuf"
        assert os.environ["OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"] == "https://otel.collector.na-01.cloud.solarwinds.com:443/v1/metrics"
        assert os.environ["OTEL_EXPORTER_OTLP_METRICS_HEADERS"] == "authorization=Bearer%20foo"
        assert os.environ["OTEL_LOGS_EXPORTER"] == "otlp_proto_http"
        assert os.environ["OTEL_EXPORTER_OTLP_LOGS_PROTOCOL"] == "http/protobuf"
        assert os.environ["OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"] == "https://otel.collector.na-01.cloud.solarwinds.com:443/v1/logs"
        assert os.environ["OTEL_EXPORTER_OTLP_LOGS_HEADERS"] == "authorization=Bearer%20foo"

    def _assert_reporter(self, reporter):
        raise NotImplementedError("Please implement this test helper")

    def _setup_test_traces_export(
        self,
        apm_config,
        configurator,
        reporter,
        oboe_api,
    ):
        sampler = next(iter(entry_points(
            group="opentelemetry_traces_sampler",
            name=configurator._DEFAULT_SW_TRACES_SAMPLER,
        ))).load()(apm_config, reporter, oboe_api)
        self.tracer_provider = TracerProvider(sampler=sampler)

        # Set InMemory exporter for testing generated telemetry
        # instead of SolarWinds/OTLP exporter
        self.memory_span_exporter = InMemorySpanExporter()
        self.tracer_provider.add_span_processor(
            SimpleSpanProcessor(self.memory_span_exporter)
        )
        trace_api.set_tracer_provider(self.tracer_provider)
        self.tracer = self.tracer_provider.get_tracer(__name__)

        # Manually set up SW OTLP metrics generation
        self.sw_otlp_span_proc = SolarWindsOTLPMetricsSpanProcessor(
                SolarWindsTxnNameManager(),
                apm_config,
                oboe_api,
            )
        self.tracer_provider.add_span_processor(
            self.sw_otlp_span_proc
        )

    def _setup_app_endpoints(self):
        # pylint: disable=no-member
        self.app.route("/test_trace/")(self._test_trace)
        # pylint: disable=attribute-defined-outside-init
        self.client = Client(self.app, Response)

    def _setup_instrumented_app(self):
        # We need to instrument and create test app for every test
        self.requests_inst = RequestsInstrumentor()
        self.flask_inst = FlaskInstrumentor()
        self.flask_inst.uninstrument()
        self.flask_inst.instrument(
            tracer_provider=trace_api.get_tracer_provider()
        )
        self.requests_inst.uninstrument()
        self.requests_inst.instrument(
            tracer_provider=trace_api.get_tracer_provider()
        )
        self.app = flask.Flask(__name__)
        self._setup_app_endpoints()
        self.client = Client(self.app, Response)

    def setUp(self):
        """Set up called before each test scenario"""
        self._setup_entrypoints()
        self._setup_env_vars()

        # Load Distro
        SolarWindsDistro().configure()

        self._assert_defaults()

        # Load Configurator to Configure SW custom SDK components
        # except use TestBase InMemorySpanExporter
        apm_config = SolarWindsApmConfig()
        configurator = SolarWindsConfigurator()

        # Reporter fully functional if legacy
        reporter = configurator._initialize_solarwinds_reporter(apm_config)
        self._assert_reporter(reporter)

        configurator._configure_propagator()
        configurator._configure_response_propagator()
        propagators = get_global_textmap()._propagators
        assert len(propagators) == 3
        assert isinstance(propagators[2], SolarWindsPropagator)

        # This is done because set_*_provider cannot override the
        # current tracer/meter/logger provider. Has to be done here.
        reset_trace_globals()
        reset_metrics_globals()
        reset_logging_globals()

        self._setup_test_traces_export(apm_config, configurator, reporter)
        assert isinstance(trace_api.get_tracer_provider().sampler, ParentBasedSwSampler)

    def tearDown(self):
        """Teardown called after each test scenario"""
        del self.client
        self.memory_span_exporter.clear()
        for env_key in [
            "SW_APM_SERVICE_KEY",
            "SW_APM_LEGACY",
            "OTEL_SEMCONV_STABILITY_OPT_IN",
            "OTEL_PROPAGATORS",
            "OTEL_EXPORTER_OTLP_PROTOCOL",
            "OTEL_TRACES_EXPORTER",
            "OTEL_EXPORTER_OTLP_TRACES_PROTOCOL",
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
            "OTEL_EXPORTER_OTLP_TRACES_HEADERS",
            "OTEL_METRICS_EXPORTER",
            "OTEL_EXPORTER_OTLP_METRICS_PROTOCOL",
            "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
            "OTEL_EXPORTER_OTLP_METRICS_HEADERS",
            "OTEL_LOGS_EXPORTER",
            "OTEL_EXPORTER_OTLP_LOGS_PROTOCOL",
            "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT",
            "OTEL_EXPORTER_OTLP_LOGS_HEADERS",
        ]:
            if os.environ.get(env_key):
                del os.environ[env_key]
