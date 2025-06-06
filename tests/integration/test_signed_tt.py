# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
import hashlib
import hmac
import re
import json
import time
from unittest import mock

from opentelemetry import trace as trace_api
from unittest import mock

from solarwinds_apm.oboe.settings import LocalSettings, TracingMode
from .test_base_sw_headers_attrs import TestBaseSwHeadersAndAttributes


class TestSignedWithOrWithoutTt(TestBaseSwHeadersAndAttributes):
    """
    Test class for signed requests, with or without trigger tracing,
    without traceparent nor tracestate headers.
    """

    def test_signed_with_tt_auth_ok(self):
        """
        Signed request with trigger-trace, auth ok:
        1. Decision to sample with correctly signed trigger trace flag is made at root/service
           entry span (mocked). There is no OTel context extracted from request headers,
           so this is the root and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. The valid x-trace-options is handled and an x-trace-options-response
           header is injected into the response.
        4. Sampling-related, SWKeys, custom-*, and TriggeredTrace attributes are set
           for the root/service entry span, but not what's ignored.
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
                    "arguments":
                        {
                            "BucketCapacity":2,
                            "BucketRate":1,
                            "MetricsFlushInterval":60,
                            "SignatureKey":"key",
                            "TriggerRelaxedBucketCapacity":4,
                            "TriggerRelaxedBucketRate":3,
                            "TriggerStrictBucketCapacity":6,
                            "TriggerStrictBucketRate":5,
                        },
                    "flags":"SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer":"",
                    "timestamp":timestamp,
                    "ttl":120,
                    "type":0,
                    "value":1000000
                }
            ],
        ):
            x_trace_options = f"trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo;ts={timestamp}"
            x_trace_options_signature = hmac.new(str.encode("key"), str.encode(x_trace_options), hashlib.sha1).hexdigest()
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": x_trace_options,
                    "x-trace-options-signature": x_trace_options_signature,
                    "some-header": "some-value"
                }
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
        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert resp_json["tracestate"] == "sw={}-{}".format(new_span_id, new_trace_flags)

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify x-trace-options-response response header present
        assert "x-trace-options-response" in resp.headers
        assert "trigger-trace=ok" in resp.headers["x-trace-options-response"]
        assert "ignored=this-will-be-ignored" in resp.headers["x-trace-options-response"]

        # Verify spans exported: service entry (root) + outgoing request (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]
        assert span_server.name == "GET /test_trace/"
        assert span_server.kind == trace_api.SpanKind.SERVER
        assert span_client.name == "GET"
        assert span_client.kind == trace_api.SpanKind.CLIENT

        # Check root span tracestate has `xtrace_options_response` key but no `sw` key
        # because no valid parent context.
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "auth####ok;trigger-trace####ok;ignored####this-will-be-ignored"),
        ])
        actual_trace_state = span_server.context.trace_state
        assert actual_trace_state.get("sw") == expected_trace_state.get("sw")  # both None
        assert actual_trace_state.get("xtrace_options_response") == expected_trace_state.get("xtrace_options_response")

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     SWKeys, because included in xtraceoptions in otel context
        #     custom-*, because included in xtraceoptions in otel context
        #     TriggeredTrace, because trigger-trace in otel context
        #     Bucket* in attributes, because trigger trace is sampled
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     the ignored value in the x-trace-options-header
        #     SampleRate, SampleSource in attributes, because it is a trigger trace
        assert all(attr_key in span_server.attributes for attr_key in ["BucketCapacity","BucketRate"])
        assert span_server.attributes["BucketCapacity"] == 4
        assert span_server.attributes["BucketRate"] == 3
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" in span_server.attributes
        assert span_server.attributes["SWKeys"] == "check-id:check-1013,website-id:booking-demo"
        assert "custom-awesome-key" in span_server.attributes
        assert span_server.attributes["custom-awesome-key"] == "foo"
        assert "TriggeredTrace" in span_server.attributes
        assert span_server.attributes["TriggeredTrace"] == True
        assert "this-will-be-ignored" not in span_server.attributes

        # Check client span tracestate has `xtrace_options_response` key but no `sw` key
        # because no valid parent context.
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "auth####ok;trigger-trace####ok;ignored####this-will-be-ignored"),
        ])
        actual_trace_state = span_client.context.trace_state
        assert actual_trace_state.get("sw") == expected_trace_state.get("sw")  # both None
        assert actual_trace_state.get("xtrace_options_response") == expected_trace_state.get("xtrace_options_response")

        # Check outgoing request span attributes
        #   :absent:
        #     service entry internal KVs, which are only on entry spans
        #     sw.tracestate_parent_id, because cannot be set without attributes at decision
        #     SWKeys, because only written for service entry spans
        #     custom-*, because only written for service entry spans
        #     TriggeredTrace, because only written for service entry spans
        #     the ignored value in the x-trace-options-header
        assert not any(attr_key in span_client.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert not "sw.tracestate_parent_id" in span_client.attributes
        assert not "SWKeys" in span_client.attributes
        assert not "custom-awesome-key" in span_client.attributes
        assert not "TriggeredTrace" in span_client.attributes
        assert "this-will-be-ignored" not in span_client.attributes

        # Check span_id of the outgoing request span (client span) matches
        # the span_id portion in the outgoing tracestate header, which
        # is stored in the test app's response body (new_span_id).
        # Note: context.span_id needs a 16-byte hex conversion first.
        assert "{:016x}".format(span_client.context.span_id) == new_span_id

    def test_signed_without_tt_auth_ok(self):
        """
        Signed request without trigger-trace, auth ok, but it will use dice roll algo:
        1. Decision to sample is made at root/service entry span (mocked). There
           is no OTel context extracted from request headers, so this is the root
           and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. The valid x-trace-options is handled and an x-trace-options-response
           header is injected into the response.
        4. Sampling-related, SWKeys, and custom-*, and attributes are set
           for the root/service entry span, but not what's ignored nor TriggeredTrace.
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
                    "arguments":
                        {
                            "BucketCapacity":2,
                            "BucketRate":1,
                            "MetricsFlushInterval":60,
                            "SignatureKey":"key",
                            "TriggerRelaxedBucketCapacity":4,
                            "TriggerRelaxedBucketRate":3,
                            "TriggerStrictBucketCapacity":6,
                            "TriggerStrictBucketRate":5
                        },
                    "flags":"SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer":"",
                    "timestamp":timestamp,
                    "ttl":120,
                    "type":0,
                    "value":1_000_000
                }
            ],
        ):
            x_trace_options = f"sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo;ts={timestamp}"
            x_trace_options_signature = hmac.new(str.encode("key"), str.encode(x_trace_options),
                                                 hashlib.sha1).hexdigest()
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": x_trace_options,
                    "x-trace-options-signature": x_trace_options_signature,
                    "some-header": "some-value"
                }
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
        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert resp_json["tracestate"] == "sw={}-{}".format(
            new_span_id,
            new_trace_flags,
        )

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify x-trace-options-response response header present
        assert "x-trace-options-response" in resp.headers
        assert "trigger-trace=not-requested" in resp.headers["x-trace-options-response"]
        assert "ignored=this-will-be-ignored" in resp.headers["x-trace-options-response"]

        # Verify spans exported: service entry (root) + outgoing request (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]
        assert span_server.name == "GET /test_trace/"
        assert span_server.kind == trace_api.SpanKind.SERVER
        assert span_client.name == "GET"
        assert span_client.kind == trace_api.SpanKind.CLIENT

        # Check root span tracestate has `xtrace_options_response` key but no `sw` key
        # because no valid parent context.
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "auth####ok;trigger-trace####not-requested;ignored####this-will-be-ignored"),
        ])
        actual_trace_state = span_server.context.trace_state
        assert actual_trace_state.get("sw") == expected_trace_state.get("sw")  # both None
        assert actual_trace_state.get("xtrace_options_response") == expected_trace_state.get("xtrace_options_response")

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     SWKeys, because included in xtraceoptions in otel context
        #     custom-*, because included in xtraceoptions in otel context
        #     Bucket* in attributes, because trigger trace is sampled
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     TriggeredTrace, because trigger-trace not in otel context
        #     the ignored value in the x-trace-options-header
        #     SampleRate, SampleSource in attributes, because it is a trigger trace
        assert all(attr_key in span_server.attributes for attr_key in ["BucketCapacity", "BucketRate"])
        assert span_server.attributes["BucketCapacity"] == 2
        assert span_server.attributes["BucketRate"] == 1
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" in span_server.attributes
        assert span_server.attributes["SWKeys"] == "check-id:check-1013,website-id:booking-demo"
        assert "custom-awesome-key" in span_server.attributes
        assert span_server.attributes["custom-awesome-key"] == "foo"
        assert "TriggeredTrace" not in span_server.attributes
        assert "this-will-be-ignored" not in span_server.attributes

        # Check client span tracestate has `xtrace_options_response` key but no `sw` key
        # because no valid parent context.
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "auth####ok;trigger-trace####not-requested;ignored####this-will-be-ignored"),
        ])
        actual_trace_state = span_client.context.trace_state
        assert actual_trace_state.get("sw") == expected_trace_state.get("sw")  # both None
        assert actual_trace_state.get("xtrace_options_response") == expected_trace_state.get("xtrace_options_response")

        # Check outgoing request span attributes
        #   :absent:
        #     service entry internal KVs, which are only on entry spans
        #     sw.tracestate_parent_id, because cannot be set without attributes at decision
        #     SWKeys, because only written for service entry spans
        #     custom-*, because only written for service entry spans
        #     TriggeredTrace, because only written for service entry spans
        #     the ignored value in the x-trace-options-header
        assert not any(attr_key in span_client.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert not "sw.tracestate_parent_id" in span_client.attributes
        assert not "SWKeys" in span_client.attributes
        assert not "custom-awesome-key" in span_client.attributes
        assert not "TriggeredTrace" in span_client.attributes
        assert "this-will-be-ignored" not in span_client.attributes

        # Check span_id of the outgoing request span (client span) matches
        # the span_id portion in the outgoing tracestate header, which
        # is stored in the test app's response body (new_span_id).
        # Note: context.span_id needs a 16-byte hex conversion first.
        assert "{:016x}".format(span_client.context.span_id) == new_span_id

    def test_signed_with_tt_rate_exceeded(self):
        """
        Signed request with trigger-trace, rate exceeded:
        1. Decision to NOT sample with is made at root/service entry span (mocked).
           There is no OTel context extracted from request headers,
           so this is the root and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. The valid x-trace-options is handled and an x-trace-options-response
           header is injected into the response.
        4. No spans are exported.
        """
        # Mock JSON read to guarantee sample decision
        timestamp = int(time.time())
        with mock.patch(
            target="solarwinds_apm.oboe.json_sampler.JsonSampler._read",
            return_value=[
                {
                    "arguments":
                        {
                            "BucketCapacity":2,
                            "BucketRate":1,
                            "MetricsFlushInterval":60,
                            "SignatureKey":"key",
                            "TriggerRelaxedBucketCapacity":0,
                            "TriggerRelaxedBucketRate":0,
                            "TriggerStrictBucketCapacity":6,
                            "TriggerStrictBucketRate":5,
                        },
                    "flags":"SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer":"",
                    "timestamp":timestamp,
                    "ttl":120,
                    "type":0,
                    "value":0
                }
            ],
        ):
            x_trace_options = f"trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo;ts={timestamp}"
            x_trace_options_signature = hmac.new(str.encode("key"), str.encode(x_trace_options),
                                                 hashlib.sha1).hexdigest()
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": x_trace_options,
                    "x-trace-options-signature": x_trace_options_signature,
                    "some-header": "some-value"
                }
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
        assert new_trace_flags == "00"

        assert "tracestate" in resp_json
        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert resp_json["tracestate"] == "sw={}-{}".format(new_span_id, new_trace_flags)

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify x-trace-options-response response header present
        assert "x-trace-options-response" in resp.headers
        assert "auth=ok" in resp.headers["x-trace-options-response"]
        assert "trigger-trace=rate-exceeded" in resp.headers["x-trace-options-response"]
        assert "ignored=this-will-be-ignored" in resp.headers["x-trace-options-response"]

        # Verify no spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_signed_with_tt_tracing_disabled(self):
        """
        Signed request with trigger-trace, tracing disabled:
        1. Decision to NOT sample with is made at root/service entry span (mocked).
           There is no OTel context extracted from request headers,
           so this is the root and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. The valid x-trace-options is handled and an x-trace-options-response
           header is injected into the response.
        4. No spans are exported.
        """
        # Mock JSON read to guarantee sample decision
        timestamp = int(time.time())

        with mock.patch(
            target="solarwinds_apm.oboe.sampler.Sampler.local_settings",
            return_value=LocalSettings(tracing_mode=TracingMode.NEVER, trigger_mode=False)
        ):
            with mock.patch(
                target="solarwinds_apm.oboe.json_sampler.JsonSampler._read",
                return_value=[
                    {
                        "arguments":
                            {
                                "BucketCapacity":2,
                                "BucketRate":1,
                                "MetricsFlushInterval":60,
                                "SignatureKey":"key",
                                "TriggerRelaxedBucketCapacity":4,
                                "TriggerRelaxedBucketRate":3,
                                "TriggerStrictBucketCapacity":6,
                                "TriggerStrictBucketRate":5
                            },
                        "flags":"",
                        "layer":"",
                        "timestamp":timestamp,
                        "ttl":120,
                        "type":0,
                        "value":1_000_000
                    }
                ],
            ):
                x_trace_options = f"trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo;ts={timestamp}"
                x_trace_options_signature = hmac.new(str.encode("key"), str.encode(x_trace_options),
                                                     hashlib.sha1).hexdigest()
                # Request to instrumented app with headers
                resp = self.client.get(
                    "/test_trace/",
                    headers={
                        "x-trace-options": x_trace_options,
                        "x-trace-options-signature": x_trace_options_signature,
                        "some-header": "some-value"
                    }
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
        assert new_trace_flags == "00"

        assert "tracestate" in resp_json
        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert resp_json["tracestate"] == "sw={}-{}".format(new_span_id, new_trace_flags)

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify x-trace-options-response response header present
        assert "x-trace-options-response" in resp.headers
        assert "auth=ok" in resp.headers["x-trace-options-response"]
        assert "trigger-trace=tracing-disabled" in resp.headers["x-trace-options-response"]
        assert "ignored=this-will-be-ignored" in resp.headers["x-trace-options-response"]

        # Verify no spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_signed_with_tt_auth_fail(self):
        """
        Signed request with trigger-trace, auth fail:
        1. Decision to sample with failed signed trigger trace flag is made at root/service
           entry span (mocked). There is no OTel context extracted from request headers,
           so this is the root and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. The valid x-trace-options is handled and an x-trace-options-response
           header is injected into the response.
        4. No spans are exported.
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
                    "arguments":
                        {
                            "BucketCapacity":2,
                            "BucketRate":1,
                            "MetricsFlushInterval":60,
                            "SignatureKey":"",
                            "TriggerRelaxedBucketCapacity":4,
                            "TriggerRelaxedBucketRate":3,
                            "TriggerStrictBucketCapacity":6,
                            "TriggerStrictBucketRate":5,
                        },
                    "flags":"SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer":"",
                    "timestamp":timestamp,
                    "ttl":120,
                    "type":0,
                    "value":0
                }
            ],
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": f"trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo;ts={timestamp}",
                    "x-trace-options-signature": "bad-sig",
                    "some-header": "some-value"
                }
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
        assert new_trace_flags == "00"

        assert "tracestate" in resp_json
        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert resp_json["tracestate"] == "sw={}-{}".format(new_span_id, new_trace_flags)

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify x-trace-options-response response header present
        # but only with 'auth' KV
        assert "x-trace-options-response" in resp.headers
        assert "auth=no-signature-key" in resp.headers["x-trace-options-response"]
        assert "ignored" not in resp.headers["x-trace-options-response"]

        # Verify no spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_signed_without_tt_auth_fail(self):
        """
        Signed request without trigger-trace, auth fail:
        1. Decision to sample with failed signed trigger trace flag is made at root/service
           entry span (mocked). There is no OTel context extracted from request headers,
           so this is the root and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. The valid x-trace-options is handled and an x-trace-options-response
           header is injected into the response.
        4. No spans are exported.
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
                    "arguments":
                        {
                            "BucketCapacity":2,
                            "BucketRate":1,
                            "MetricsFlushInterval":60,
                            "SignatureKey":"",
                            "TriggerRelaxedBucketCapacity":4,
                            "TriggerRelaxedBucketRate":3,
                            "TriggerStrictBucketCapacity":6,
                            "TriggerStrictBucketRate":5,
                        },
                    "flags":"SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer":"",
                    "timestamp":timestamp,
                    "ttl":120,
                    "type":0,
                    "value":0
                }
            ],
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": f"sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo;ts={timestamp}",
                    "x-trace-options-signature": "bad-sig",
                    "some-header": "some-value"
                }
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
        assert new_trace_flags == "00"

        assert "tracestate" in resp_json
        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert resp_json["tracestate"] == "sw={}-{}".format(
            new_span_id,
            new_trace_flags,
        )

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify x-trace-options-response response header present
        # but only with 'auth' KV
        assert "x-trace-options-response" in resp.headers
        assert "auth=no-signature-key" in resp.headers["x-trace-options-response"]
        assert "ignored" not in resp.headers["x-trace-options-response"]

        # Verify no spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_signed_with_tt_auth_fail_bad_ts(self):
        """
        Signed request with trigger-trace, auth fail from bad timestamp:
        1. Decision to sample with failed signed trigger trace flag is made at root/service
           entry span (mocked). There is no OTel context extracted from request headers,
           so this is the root and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. The valid x-trace-options is handled and an x-trace-options-response
           header is injected into the response.
        4. No spans are exported.
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
                    "arguments":
                        {
                            "BucketCapacity":2,
                            "BucketRate":1,
                            "MetricsFlushInterval":60,
                            "SignatureKey":"key",
                            "TriggerRelaxedBucketCapacity":4,
                            "TriggerRelaxedBucketRate":3,
                            "TriggerStrictBucketCapacity":6,
                            "TriggerStrictBucketRate":5,
                        },
                    "flags":"SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer":"",
                    "timestamp":timestamp,
                    "ttl":120,
                    "type":0,
                    "value":0
                }
            ],
        ):
            x_trace_options = f"trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo;ts={timestamp-5*60-1}"
            x_trace_options_signature = hmac.new(str.encode("key"), str.encode(x_trace_options), hashlib.sha1).hexdigest()
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": x_trace_options,
                    "x-trace-options-signature": x_trace_options_signature,
                    "some-header": "some-value"
                }
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
        assert new_trace_flags == "00"

        assert "tracestate" in resp_json
        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert resp_json["tracestate"] == "sw={}-{}".format(new_span_id, new_trace_flags)

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify x-trace-options-response response header present
        # but only with 'auth' KV
        assert "x-trace-options-response" in resp.headers
        assert "auth=bad-timestamp" in resp.headers["x-trace-options-response"]
        assert "ignored" not in resp.headers["x-trace-options-response"]

        # Verify no spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_signed_without_tt_auth_fail_bad_ts(self):
        """
        Signed request without trigger-trace, auth fail from bad timestamp:
        1. Decision to sample with failed signed trigger trace flag is made at root/service
           entry span (mocked). There is no OTel context extracted from request headers,
           so this is the root and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. The valid x-trace-options is handled and an x-trace-options-response
           header is injected into the response.
        4. No spans are exported.
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
                    "arguments":
                        {
                            "BucketCapacity":2,
                            "BucketRate":1,
                            "MetricsFlushInterval":60,
                            "SignatureKey":"key",
                            "TriggerRelaxedBucketCapacity":4,
                            "TriggerRelaxedBucketRate":3,
                            "TriggerStrictBucketCapacity":6,
                            "TriggerStrictBucketRate":5,
                        },
                    "flags":"SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer":"",
                    "timestamp":timestamp,
                    "ttl":120,
                    "type":0,
                    "value":0
                }
            ],
        ):
            x_trace_options = f"sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo;ts={timestamp - 5 * 60 - 1}"
            x_trace_options_signature = hmac.new(str.encode("key"), str.encode(x_trace_options),
                                                 hashlib.sha1).hexdigest()

            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": x_trace_options,
                    "x-trace-options-signature": x_trace_options_signature,
                    "some-header": "some-value"
                }
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
        assert new_trace_flags == "00"

        assert "tracestate" in resp_json
        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert resp_json["tracestate"] == "sw={}-{}".format(
            new_span_id,
            new_trace_flags,
        )

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify x-trace-options-response response header present
        # but only with 'auth' KV
        assert "x-trace-options-response" in resp.headers
        assert "auth=bad-timestamp" in resp.headers["x-trace-options-response"]
        assert "ignored" not in resp.headers["x-trace-options-response"]

        # Verify no spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_signed_missing_xtraceoptions_header(self):
        """
        Signed request missing x-trace-options header:
        1. Decision to NOT sample with signature but no x-trace-options is made at root/service
           entry span (mocked). There is no OTel context extracted from request headers,
           so this is the root and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. No valid x-trace-options is handled so no x-trace-options-response
           header is injected into the response.
        4. No spans are exported.
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
                    "arguments":
                        {
                            "BucketCapacity":2,
                            "BucketRate":1,
                            "MetricsFlushInterval":60,
                            "SignatureKey":"key",
                            "TriggerRelaxedBucketCapacity":4,
                            "TriggerRelaxedBucketRate":3,
                            "TriggerStrictBucketCapacity":6,
                            "TriggerStrictBucketRate":5,
                        },
                    "flags":"SAMPLE_START,SAMPLE_THROUGH_ALWAYS,SAMPLE_BUCKET_ENABLED,TRIGGER_TRACE",
                    "layer":"",
                    "timestamp":timestamp,
                    "ttl":120,
                    "type":0,
                    "value":0
                }
            ],
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options-signature": "good-sig-but-no-ts",
                    "some-header": "some-value"
                }
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
        assert new_trace_flags == "00"

        assert "tracestate" in resp_json
        # In this test we know there is `sw` in tracestate
        # where value will be new_span_id and new_trace_flags.
        # There should be no `xtrace_options_response` key because there is
        # no trigger-trace in the extracted x-trace-options header.
        assert resp_json["tracestate"] == "sw={}-{}".format(
            new_span_id,
            new_trace_flags,
        )

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify x-trace-options-response response header not present
        # because no x-trace-options-header
        assert "x-trace-options-response" not in resp.headers

        # Verify no spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 0
