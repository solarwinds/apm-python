import requests

from flask import Flask, request
from opentelemetry import trace

app = Flask(__name__)
tracer = trace.get_tracer(__name__)

@app.route("/test/")
def test_trace():
    """Makes request traced by autoinstrumentation
    and a trace started manually with SDK"""
    with tracer.start_as_current_span("test_trace_manual_span"):
        requests.get("http://www.solarwinds.com/")
        return "Done"
