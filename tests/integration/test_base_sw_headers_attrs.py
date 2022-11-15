import os
from pkg_resources import (
    iter_entry_points,
    load_entry_point
)
import re

import flask
import requests
from werkzeug.test import Client
from werkzeug.wrappers import Response

from opentelemetry import trace as trace_api
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.propagate import get_global_textmap
from opentelemetry.sdk.trace import TracerProvider, export
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.test.globals_test import reset_trace_globals
from opentelemetry.test.test_base import TestBase

from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.configurator import SolarWindsConfigurator
from solarwinds_apm.distro import SolarWindsDistro
from solarwinds_apm.propagator import SolarWindsPropagator
from solarwinds_apm.sampler import ParentBasedSwSampler


class TestBaseSwHeadersAndAttributes(TestBase):
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
    
    def _setup_endpoints(self):
        # pylint: disable=no-member
        self.app.route("/test_trace/")(self._test_trace)
        # pylint: disable=attribute-defined-outside-init
        self.client = Client(self.app, Response)

    def setUp(self):
        """Set up called before each test scenario"""
        # Based on auto_instrumentation run() and sitecustomize.py
        # Load OTel env vars entry points
        argument_otel_environment_variable = {}
        for entry_point in iter_entry_points(
            "opentelemetry_environment_variables"
        ):
            environment_variable_module = entry_point.load()
            for attribute in dir(environment_variable_module):
                if attribute.startswith("OTEL_"):
                    argument = re.sub(r"OTEL_(PYTHON_)?", "", attribute).lower()
                    argument_otel_environment_variable[argument] = attribute

        # Set APM service key - not valid, but we mock liboboe anyway
        os.environ["SW_APM_SERVICE_KEY"] = "foo:bar"

        # Load Distro
        SolarWindsDistro().configure()
        assert os.environ["OTEL_PROPAGATORS"] == "tracecontext,baggage,solarwinds_propagator"

        # Load Configurator to Configure SW custom SDK components
        # except use TestBase InMemorySpanExporter
        apm_config = SolarWindsApmConfig()
        configurator = SolarWindsConfigurator()
        configurator._initialize_solarwinds_reporter(apm_config)
        configurator._configure_propagator()
        configurator._configure_response_propagator()
        # This is done because set_tracer_provider cannot override the
        # current tracer provider. Has to be done here.
        reset_trace_globals()
        sampler = load_entry_point(
            "solarwinds_apm",
            "opentelemetry_traces_sampler",
            configurator._DEFAULT_SW_TRACES_SAMPLER
        )(apm_config)
        self.tracer_provider = TracerProvider(sampler=sampler)
        # Set InMemorySpanExporter for testing
        # We do NOT use SolarWindsSpanExporter
        self.memory_exporter = InMemorySpanExporter()
        span_processor = export.SimpleSpanProcessor(self.memory_exporter)
        self.tracer_provider.add_span_processor(span_processor)
        trace_api.set_tracer_provider(self.tracer_provider)
        self.tracer = self.tracer_provider.get_tracer(__name__)

        # Make sure SW SDK components were set
        propagators = get_global_textmap()._propagators
        assert len(propagators) == 3
        assert isinstance(propagators[2], SolarWindsPropagator)
        assert isinstance(trace_api.get_tracer_provider().sampler, ParentBasedSwSampler)

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
        self._setup_endpoints()
        self.client = Client(self.app, Response)

    def tearDown(self):
        """Teardown called after each test scenario"""
        self.memory_exporter.clear()
