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

class PropagationTest_v02_mixin:

    @staticmethod
    def _test_trace_with_span_name(span_name):
        with tracer.start_as_current_span(span_name):
            resp = requests.get(f"http://postman-echo.com/headers")

        #  The return type must be a string, dict, tuple, Response instance, or WSGI callable
        # (not CaseInsensitiveDict)
        return {
            "traceparent": resp.request.headers["traceparent"],
            "tracestate": resp.request.headers["tracestate"],
        }
    
    def _setup_endpoints(self):
        # pylint: disable=no-member
        self.app.route("/test_trace_with_span_name/<span_name>")(self._test_trace_with_span_name)
        # pylint: disable=attribute-defined-outside-init
        self.client = Client(self.app, Response)
