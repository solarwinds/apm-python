
import json

import flask
from werkzeug.test import Client
from werkzeug.wrappers import Response

from opentelemetry import trace as trace_api
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.test.wsgitestutil import WsgiTestBase

from unittest import mock
from unittest.mock import patch

from .propagation_test_app_v02 import PropagationTest_v02_mixin
from .sw_distro_test import SolarWindsDistroTestBase

class TestHeadersAndSpanAttributes_v02(
    PropagationTest_v02_mixin,
    SolarWindsDistroTestBase,
    WsgiTestBase
):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wakeup_request()
        # Instrument requests to/from test Flask app to check headers
        cls.httpx_inst = HTTPXClientInstrumentor()
        cls.requests_inst = RequestsInstrumentor()
        cls.flask_inst = FlaskInstrumentor()

        # Set up test app
        cls.app = flask.Flask(__name__)
        cls._setup_endpoints(cls)
        # # Not needed
        # cls.flask_inst.instrument_app(
        #     app=cls.app,
        #     tracer_provider=cls.tracer_provider,
        # )
        
    @classmethod
    def tearDownClass(cls):
        # FlaskInstrumentor().uninstrument_app(cls.app)
        cls.flask_inst.uninstrument()
        cls.httpx_inst.uninstrument()
        cls.requests_inst.uninstrument()


    def test_check_exporter_for_spans_after_request(self):
        """
        I want to generate and export these spans to compare headers to attributes:
          1. span for client.post, root span and entry span in this test
          2. span when PropagationTest receives post request (its entry span)
          3. foo-span, a manual span in PropagationTest
          4. span for PropagationTest's requests.get
        
        The manual span 3 is being exported to InMemorySpanExporter.
        The others are not. 2 and 4 are supposed to be created automatically
        through OTel instrumentation libraries for Flask and requests.
        I expect somewhat that 1 won't exist because it's from Werkzeug.
        """
        # We seem to need to do this here instead of setUpClass
        self.flask_inst.uninstrument()
        self.flask_inst.instrument(
            tracer_provider=trace_api.get_tracer_provider()
        )
        # self.httpx_inst.uinstrument()  # AttributeError: 'HTTPXClientInstrumentor' object has no attribute 'uinstrument'
        self.httpx_inst.instrument(
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
            # Request to instrumented app
            resp = client.get(
                "/test_trace_with_span_name/foo-span",
            )
        resp_json = json.loads(resp.data)

        # verify all spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) > 1
        print("len(spans) is {}".format(len(spans))) # 3
        for span in spans:
            # HTTP GET
            # foo-span
            # /test_trace_with_span_name/<span_name>
            print("span.name: {}".format(span.name))
        # assert spans[0].name == "foo-span"