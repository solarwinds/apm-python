import requests

from flask import Flask
from flask_talisman import Talisman
from opentelemetry import trace

app = Flask(__name__)
Talisman(app)
tracer = trace.get_tracer(__name__)

@app.route("/test/")
def test_trace():
    """Makes request traced by autoinstrumentation
    and a trace started manually with SDK"""
    with tracer.start_as_current_span("test_manual_outer"):
        current_span = trace.get_current_span()
        current_span.set_attribute("test.custom_attribute", "outer-foo-bar")
        with tracer.start_as_current_span("test_manual_inner"):
            current_span = trace.get_current_span()
            current_span.set_attribute("test.custom_attribute", "inner-foo-bar")
            requests.get("https://www.solarwinds.com/")
            return "Done"
