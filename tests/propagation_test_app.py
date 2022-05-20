"""
Bare-bones Flask/Werkzeug test app.
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


# Logging
level = os.getenv("PYTHON_DEBUG_LEVEL", logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(level)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(level)
formatter = logging.Formatter('%(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class PropagationTest:
    def _app_init(self):
        """Set up Flask app and test Client"""
        # pylint: disable=attribute-defined-outside-init
        self.app = create_app()
        self.client = Client(self.app, Response)


def create_app():
    app = flask.Flask(__name__)

    @app.route("/test_trace")
    def test_trace():
        logger.debug("Incoming request headers: {}".format(flask.request.headers))
        resp = requests.get(f"http://postman-echo.com/headers")

        # # CaseInsensitiveDict
        # logger.debug("Outgoing request headers: (type {})".format(type(resp.request.headers)))
        # logger.debug(resp.request.headers)
        # logger.debug("Response content:")
        # logger.debug(resp.content)
        # logger.debug("Response headers:")
        # logger.debug(resp.headers)

        #  The return type must be a string, dict, tuple, Response instance, or WSGI callable
        return {
            "traceparent": resp.request.headers["traceparent"],
            "tracestate": resp.request.headers["tracestate"],
        }
    
    return app
