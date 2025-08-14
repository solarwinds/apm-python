# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import re
import json
import time
from unittest import mock

from opentelemetry import trace as trace_api

from .test_base_sw_headers_attrs import TestBaseSwHeadersAndAttributes


class TestScenario1(TestBaseSwHeadersAndAttributes):
    """
    Test class for starting a new tracing decision with no input headers.
    """

    def test_scenario_1_sampled(self):
        """
        Scenario #1, sampled:
        1. Decision to sample is made at root/service entry span (mocked). There is no
           OTel context extracted from request headers, so this is the root and start
           of the trace.
        2. Headers in the original request are not altered by the SW propagator.
        3. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        4. Sampling-related attributes are set for the root/service entry span.
        5. The span_id of the outgoing request span matches the span_id portion in the
           tracestate header.
        """
        # Use in-process test app client and mock to propagate context
        # and create in-memory trace
        resp = None
        # Mock JSON read to guarantee sample decision
        timestamp = int(time.time())
        with mock.patch(
            target="solarwinds_apm.oboe.json_sampler.JsonSampler._read",
            return_value=[
                {
                    "arguments": {
                        "BucketCapacity": 2,
                        "BucketRate": 1,
                        "MetricsFlushInterval": 60,
                        "SignatureKey": "",
                        "TriggerRelaxedBucketCapacity": 4,
                        "TriggerRelaxedBucketRate": 3,
                        "TriggerStrictBucketCapacity": 6,
                        "TriggerStrictBucketRate": 5,
                    },
                    "flags": "SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer": "",
                    "timestamp": timestamp,
                    "ttl": 120,
                    "type": 0,
                    "value": 1000000,
                }
            ],
        ):
            # Request to instrumented app, no traceparent/tracestate
            resp = self.client.get(
                "/test_trace/", headers={"some-header": "some-value"}
            )
        resp_json = json.loads(resp.data)

        # Verify some-header was not altered by instrumentation
        try:
            assert resp_json["incoming-headers"]["some-header"] == "some-value"
        except KeyError as e:
            self.fail("KeyError was raised at incoming-headers check: {}".format(e))

        # Verify trace context injected into test app's outgoing postman-echo call
        # (added to Flask app's response data) includes:
        #    - traceparent with a trace_id, span_id, and trace_flags for do_sample
        #    - tracestate with same span_id and trace_flags for do_sample
        assert "traceparent" in resp_json
        _TRACEPARENT_HEADER_FORMAT = (
            "^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$"
        )
        _TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)
        traceparent_re_result = re.search(
            _TRACEPARENT_HEADER_FORMAT_RE,
            resp_json["traceparent"],
        )
        new_trace_id = traceparent_re_result.group(2)
        assert new_trace_id is not None
        new_span_id = traceparent_re_result.group(3)
        assert new_span_id is not None
        new_trace_flags = traceparent_re_result.group(4)
        assert new_trace_flags == "01"

        assert "tracestate" in resp_json
        # In this test we know there is only `sw` in tracestate
        # and its value will be new_span_id and new_trace_flags
        assert resp_json["tracestate"] == "sw={}-{}".format(
            new_span_id, new_trace_flags
        )

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify spans exported: service entry (root) + outgoing request (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]
        assert span_server.name == "GET /test_trace/"
        assert span_server.kind == trace_api.SpanKind.SERVER
        assert span_client.name == "GET"
        assert span_client.kind == trace_api.SpanKind.CLIENT

        # Check root span tracestate has no `sw` key
        # because no valid parent context
        expected_trace_state = trace_api.TraceState([])
        assert span_server.context.trace_state.get("sw") == expected_trace_state.get(
            "sw"
        )  # None

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     SWKeys, because no xtraceoptions in otel context
        assert all(
            attr_key in span_server.attributes for attr_key in self.SW_SETTINGS_KEYS
        )
        assert span_server.attributes["BucketCapacity"] == 2
        assert span_server.attributes["BucketRate"] == 1
        assert span_server.attributes["SampleRate"] == 1000000
        assert span_server.attributes["SampleSource"] == 6
        assert "sw.tracestate_parent_id" not in span_server.attributes
        assert "SWKeys" not in span_server.attributes

        # Check outgoing request span tracestate has no `sw` key
        # because no valid parent context
        expected_trace_state = trace_api.TraceState([])
        assert span_client.context.trace_state.get("sw") == expected_trace_state.get(
            "sw"
        )  # None

        # Check outgoing request span attributes
        #   :absent:
        #     service entry internal KVs, which are only on entry spans
        #     sw.tracestate_parent_id, because cannot be set without attributes at decision
        #     SWKeys, because no xtraceoptions in otel context
        assert not any(
            attr_key in span_client.attributes for attr_key in self.SW_SETTINGS_KEYS
        )
        assert "sw.tracestate_parent_id" not in span_client.attributes
        assert "SWKeys" not in span_client.attributes

        # Check span_id of the outgoing request span (client span) matches
        # the span_id portion in the outgoing tracestate header, which
        # is stored in the test app's response body (new_span_id).
        # Note: context.span_id needs a 16-byte hex conversion first.
        assert "{:016x}".format(span_client.context.span_id) == new_span_id
