# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import requests

from flask import Flask
from opentelemetry import trace

app = Flask(__name__)
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
            requests.get("http://www.solarwinds.com/")
            return "Done"
