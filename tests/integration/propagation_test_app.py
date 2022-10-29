"""
OTel SDK-using, bare-bones Flask/Werkzeug test app.
Provides route to make outbound request to postman-echo and respond
with the `traceparent and `tracestate` headers of that request.
"""

import logging
import os
import sys

import flask
import requests
from werkzeug.test import Client
from werkzeug.wrappers import Response

from opentelemetry import trace
from opentelemetry.instrumentation.requests import RequestsInstrumentor


# Logging
level = os.getenv("TEST_DEBUG_LEVEL", logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(level)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(level)
formatter = logging.Formatter('%(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# OTel SDK
tracer = trace.get_tracer(__name__)

class PropagationTest:
    def _app_init(self):
        """Set up Flask app and test Client.

        See also:
        https://github.com/pallets/werkzeug/blob/main/docs/test.rst"""
        # pylint: disable=attribute-defined-outside-init

        # # Instrument outgoing requests
        # requests_inst = RequestsInstrumentor()
        # requests_inst.instrument()

        self.app = create_app()
        self.client = Client(self.app, Response)


def create_app():
    # # Instrument outgoing requests
    # requests_inst = RequestsInstrumentor()
    # requests_inst.instrument()

    app = flask.Flask(__name__)

    @app.get("/test_trace")
    def test_trace():
        logger.debug("Incoming request headers: {}".format(flask.request.headers))
        resp = requests.get(f"http://postman-echo.com/headers")

        #  The return type must be a string, dict, tuple, Response instance, or WSGI callable
        # (not CaseInsensitiveDict)
        return {
            "traceparent": resp.request.headers["traceparent"],
            "tracestate": resp.request.headers["tracestate"],
        }

    @app.post("/test_trace_with_span_name")
    def test_trace_with_span_name():

        # Host: localhost
        logger.debug("Incoming request headers: {}".format(flask.request.headers))

        with tracer.start_as_current_span(flask.request.headers["span_name"]):
            requests_inst = RequestsInstrumentor()
            requests_inst.instrument()
            resp = requests.get(f"http://postman-echo.com/headers")

        #  The return type must be a string, dict, tuple, Response instance, or WSGI callable
        # (not CaseInsensitiveDict)
        return {
            "traceparent": resp.request.headers["traceparent"],
            "tracestate": resp.request.headers["tracestate"],
        }

    return app
