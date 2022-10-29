
import json

from unittest import mock
from unittest.mock import patch

from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.test.wsgitestutil import WsgiTestBase

from .propagation_test_app import PropagationTest
from .sw_distro_test import SolarWindsDistroTestBase

class TestHeadersAndSpanAttributes_v01(PropagationTest, SolarWindsDistroTestBase, WsgiTestBase):

    @classmethod
    def setUpClass(cls):

        # Instrument requests to/from test Flask app to check headers
        cls.httpx_inst = HTTPXClientInstrumentor()
        cls.httpx_inst.instrument()
        cls.requests_inst = RequestsInstrumentor()
        cls.requests_inst.instrument()
        cls.flask_inst = FlaskInstrumentor()
        cls.flask_inst.instrument()

        super().setUpClass()

        cls.wakeup_request()

        # Set up test app
        
        cls._app_init(cls)

        def my_request_hook(span, environ):
            if span and span.is_recording():
                span.update_name("bar-span")
        
        def my_response_hook(span, status, response_headers):
            if span and span.is_recording():
                span.update_name("baz-span")

        # The hooks do nothing
        cls.flask_inst.instrument_app(
            app=cls.app,
            tracer_provider=cls.tracer_provider,
            # request_hook=my_request_hook,
            # response_hook=my_response_hook,
        )
        
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
            resp = self.client.post(
                "/test_trace_with_span_name",
                headers={
                    "span_name": "foo-span"
                }
            )
        resp_json = json.loads(resp.data)

        # verify all spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) > 1
        # assert spans[0].name == "foo-span"