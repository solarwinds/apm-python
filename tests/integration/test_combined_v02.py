import os
from pkg_resources import (
    iter_entry_points,
    load_entry_point
)
import json
import re
import requests
import time

import flask
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

from unittest import mock
from unittest.mock import patch

from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.configurator import SolarWindsConfigurator
from solarwinds_apm.distro import SolarWindsDistro
from solarwinds_apm.propagator import SolarWindsPropagator
from solarwinds_apm.sampler import ParentBasedSwSampler

from .propagation_test_app_v02 import PropagationTest_v02_mixin

class TestHeadersAndSpanAttributes(
    PropagationTest_v02_mixin,
    TestBase,
):

    SW_SETTINGS_KEYS = [
        "BucketCapacity",
        "BucketRate",
        "SampleRate",
        "SampleSource"
    ]

    @classmethod
    def setUpClass(cls):
        # Instrument requests to/from test Flask app to check headers
        cls.requests_inst = RequestsInstrumentor()
        cls.flask_inst = FlaskInstrumentor()
        # Set up test app
        cls.app = flask.Flask(__name__)
        cls._setup_endpoints(cls)
        
    @classmethod
    def tearDownClass(cls):
        cls.flask_inst.uninstrument()
        cls.requests_inst.uninstrument()

    def test_scenario_1(self):
        """
        Scenario #1:
        1. Decision to sample is made at root/service entry span (mocked).
        2. Some traceparent and tracestate are injected into service's outgoing request (done by OTel TraceContextTextMapPropagator).
        3. Sampling-related attributes are set for the root/service entry span.
        4. The span_id of the outgoing request span matches the span_id portion in the tracestate header.
        """
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

        # Set APM service key
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

        # We need to do this for every test
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
        self.flask_inst.instrument_app(  # this doesn't seem to help
            app=self.app,
            tracer_provider=trace_api.get_tracer_provider(),
        )
        client = Client(self.app, Response)

        # Use in-process test app client and mock to propagate context
        # and create in-memory trace
        resp = None
        # liboboe mocked to guarantee return of "do_sample" and "start
        # decision" rate/capacity values in order to trace and set attrs
        mock_decision = mock.Mock(
            return_value=(1, 1, 3, 4, 5.0, 6.0, 1, 0, "ok", "ok", 0)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app, no traceparent/tracestate
            resp = client.get("/test_trace/")
        resp_json = json.loads(resp.data)

        # Verify trace context injected into test app's outgoing postman-echo call
        # (added to Flask app's response data) includes:
        #    - traceparent with a trace_id, span_id, and trace_flags for do_sample
        #    - tracestate with same span_id and trace_flags for do_sample
        assert "traceparent" in resp_json
        _TRACEPARENT_HEADER_FORMAT = (
            "^[ \t]*([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})"
            + "(-.*)?[ \t]*$"
        )
        _TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)
        traceparent_re_result = re.search(
            _TRACEPARENT_HEADER_FORMAT_RE,
            resp_json["traceparent"],
        )
        new_trace_id = traceparent_re_result.group(2)
        assert new_trace_id in resp_json["traceparent"]
        new_span_id = traceparent_re_result.group(3)
        assert new_span_id in resp_json["traceparent"]
        assert "01" == traceparent_re_result.group(4)

        assert "tracestate" in resp_json
        assert new_span_id in resp_json["tracestate"]
        # In this test we know there is only `sw` in tracestate
        # i.e. sw=e000baa4e000baa4-01
        _TRACESTATE_HEADER_FORMAT = (
            "^[ \t]*sw=([0-9a-f]{16})-([0-9a-f]{2})"
            + "(-.*)?[ \t]*$"
        )
        _TRACESTATE_HEADER_FORMAT_RE = re.compile(_TRACESTATE_HEADER_FORMAT)
        tracestate_re_result = re.search(
            _TRACESTATE_HEADER_FORMAT_RE,
            resp_json["tracestate"],
        )
        assert "01" == tracestate_re_result.group(2)

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify spans exported: service entry (root) + outgoing request
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]
        assert span_server.name == "/test_trace/"
        assert span_server.kind == trace_api.SpanKind.SERVER
        assert span_client.name == "HTTP GET"
        assert span_client.kind == trace_api.SpanKind.CLIENT

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set without attributes at decision
        #     SWKeys, because no xtraceoptions in otel context
        assert all(attr_key in span_server.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert span_server.attributes["BucketCapacity"] == "6.0"
        assert span_server.attributes["BucketRate"] == "5.0"
        assert span_server.attributes["SampleRate"] == 3
        assert span_server.attributes["SampleSource"] == 4
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert not "SWKeys" in span_server.attributes

        # Check outgoing request span attributes
        #   :absent:
        #     service entry internal KVs, which are only on entry spans
        #     sw.tracestate_parent_id, because cannot be set without attributes at decision
        #     SWKeys, because no xtraceoptions in otel context
        assert not any(attr_key in span_client.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert not "sw.tracestate_parent_id" in span_client.attributes
        assert not "SWKeys" in span_client.attributes

        # Check span_id of the outgoing request span (client span) matches
        # the span_id portion in the outgoing tracestate header, which
        # is stored in the test app's response body (new_span_id).
        # Note: context.span_id needs a 16-byte hex conversion first.
        assert "{:016x}".format(span_client.context.span_id) == new_span_id

        # clean up for other tests
        self.memory_exporter.clear()


    def test_scenario_4(self):
        """
        Scenario #4:
        """
        pass

    def test_scenario_6(self):
        """
        Scenario #6:
        """
        pass
