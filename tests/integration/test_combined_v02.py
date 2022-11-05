
import json
import re

import flask
from werkzeug.test import Client
from werkzeug.wrappers import Response

from opentelemetry import trace as trace_api
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.test.wsgitestutil import WsgiTestBase

from unittest import mock
from unittest.mock import patch

from .propagation_test_app_v02 import PropagationTest_v02_mixin
from .sw_distro_test import SolarWindsDistroTestBase

class TestHeadersAndSpanAttributes(
    PropagationTest_v02_mixin,
    SolarWindsDistroTestBase,
    WsgiTestBase
):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wakeup_request()
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
        # We need to do this for every test
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
        client = Client(self.app, Response)

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

        # Check outgoing request span attributes

        # Check span_id of the outgoing request span matches the span_id portion in the tracestate header

        # ...

        # clean up for other tests
        self.memory_exporter.clear()
