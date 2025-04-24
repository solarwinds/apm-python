# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import re
import json
import time

from opentelemetry import trace as trace_api
from unittest import mock

from .test_base_sw_headers_attrs import TestBaseSwHeadersAndAttributes


class TestXtraceoptionsValidation(TestBaseSwHeadersAndAttributes):
    """
    Test class for x-trace-options header validation as part of unsigned requests.

    These tests focus mainly on xtraceoptions handling through tracestate and
    service xtraceoptions responses, and successful span export. There is less
    focus on w3c trace context propagation, which is covered in other integration
    tests.
    """

    def get_response(self, headers=None):
        """Helper to get test app response with mocked decision"""
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
                    "value":1000000
                }
            ],
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers=headers,
            )
        return json.loads(resp.data)

    def get_new_span_id_and_trace_flags(self, resp_json):
        """Get new_span_id and new_trace_flagsfrom resp_json's traceparent"""
        assert "traceparent" in resp_json
        _TRACEPARENT_HEADER_FORMAT = (
            "^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$"
        )
        _TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)
        traceparent_re_result = re.search(
            _TRACEPARENT_HEADER_FORMAT_RE,
            resp_json["traceparent"],
        )
        new_span_id = traceparent_re_result.group(3)
        assert new_span_id is not None
        new_trace_flags = traceparent_re_result.group(4)
        assert new_trace_flags == "01"
        return new_span_id, new_trace_flags

    def check_some_header_ok(self, resp_json):
        """Verify some-header in resp_json was not altered by instrumentation"""
        try:
            assert resp_json["incoming-headers"]["some-header"] == "some-value"
        except KeyError as e:
            self.fail("KeyError was raised at incoming-headers check: {}".format(e))

    def test_remove_leading_trailing_spaces(self):
        resp_json = self.get_response(
            {
                "x-trace-options": " trigger-trace ;  custom-something=value; custom-OtherThing = other val ;  sw-keys = 029734wr70:9wqj21,0d9j1   ; ts = 12345 ; foo = bar ",
                "some-header": "some-value"
            }
        )
        self.check_some_header_ok(resp_json)

        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert "tracestate" in resp_json
        assert resp_json["tracestate"] == "sw={}".format(
            "-".join(self.get_new_span_id_and_trace_flags(resp_json)),
        )

        # Verify spans exported: service entry (root) + outgoing request
        # (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####foo"),
        ])
        assert span_server.context.trace_state == expected_trace_state

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     SWKeys, because included in xtraceoptions in otel context
        #     custom-*, because included in xtraceoptions in otel context
        #     TriggeredTrace, because trigger-trace in otel context
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     the ignored value in the x-trace-options-header
        print(f"span_server.attributes = {span_server.attributes}")
        assert all(attr_key in span_server.attributes for attr_key in ["BucketCapacity", "BucketRate"])
        assert span_server.attributes["BucketCapacity"] == 6
        assert span_server.attributes["BucketRate"] == 5
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" in span_server.attributes
        assert span_server.attributes["SWKeys"] == "029734wr70:9wqj21,0d9j1"
        assert "custom-something" in span_server.attributes
        assert span_server.attributes["custom-something"] == "value"
        assert "custom-OtherThing" in span_server.attributes
        assert span_server.attributes["custom-OtherThing"] == "other val"
        assert "TriggeredTrace" in span_server.attributes
        assert span_server.attributes["TriggeredTrace"] == True
        assert "foo" not in span_server.attributes

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####foo"),
        ])
        assert span_client.context.trace_state == expected_trace_state

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
        assert not "custom-something" in span_client.attributes
        assert not "custom-OtherThing" in span_client.attributes
        assert not "TriggeredTrace" in span_client.attributes
        assert "foo" not in span_client.attributes

    def test_handle_sequential_semicolons(self):
        resp_json = self.get_response(
            {
                "x-trace-options": ";foo=bar;;;custom-something=value_thing;;sw-keys=02973r70:1b2a3;;;;custom-key=val;ts=12345;;;;;;;trigger-trace;;;",
                "some-header": "some-value"
            }
        )
        self.check_some_header_ok(resp_json)

        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert "tracestate" in resp_json
        assert resp_json["tracestate"] == "sw={}".format(
            "-".join(self.get_new_span_id_and_trace_flags(resp_json)),
        )

        # Verify spans exported: service entry (root) + outgoing request
        # (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####foo"),
        ])
        assert span_server.context.trace_state == expected_trace_state

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     SWKeys, because included in xtraceoptions in otel context
        #     custom-*, because included in xtraceoptions in otel context
        #     TriggeredTrace, because trigger-trace in otel context
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     the ignored value in the x-trace-options-header
        assert all(attr_key in span_server.attributes for attr_key in ["BucketCapacity", "BucketRate"])
        assert span_server.attributes["BucketCapacity"] == 6
        assert span_server.attributes["BucketRate"] == 5
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" in span_server.attributes
        assert span_server.attributes["SWKeys"] == "02973r70:1b2a3"
        assert "custom-something" in span_server.attributes
        assert span_server.attributes["custom-something"] == "value_thing"
        assert "custom-key" in span_server.attributes
        assert span_server.attributes["custom-key"] == "val"
        assert "TriggeredTrace" in span_server.attributes
        assert span_server.attributes["TriggeredTrace"] == True
        assert "foo" not in span_server.attributes

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####foo"),
        ])
        assert span_client.context.trace_state == expected_trace_state

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
        assert not "custom-something" in span_client.attributes
        assert not "custom-key" in span_client.attributes
        assert not "TriggeredTrace" in span_client.attributes
        assert "foo" not in span_client.attributes

    def test_keep_first_of_repeated_key(self):
        resp_json = self.get_response(
            {
                "x-trace-options": "custom-something=keep_this_0;sw-keys=keep_this;sw-keys=029734wrqj21,0d9;custom-something=otherval;trigger-trace",
                "some-header": "some-value"
            }
        )
        self.check_some_header_ok(resp_json)

        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert "tracestate" in resp_json
        assert resp_json["tracestate"] == "sw={}".format(
            "-".join(self.get_new_span_id_and_trace_flags(resp_json)),
        )

        # Verify spans exported: service entry (root) + outgoing request
        # (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####sw-keys....custom-something"),
        ])
        assert span_server.context.trace_state == expected_trace_state

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     SWKeys, because included in xtraceoptions in otel context
        #     custom-*, because included in xtraceoptions in otel context
        #     TriggeredTrace, because trigger-trace in otel context
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     the ignored value in the x-trace-options-header
        assert all(attr_key in span_server.attributes for attr_key in ["BucketCapacity", "BucketRate"])
        assert span_server.attributes["BucketCapacity"] == 6
        assert span_server.attributes["BucketRate"] == 5
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" in span_server.attributes
        assert span_server.attributes["SWKeys"] == "keep_this"
        assert "custom-something" in span_server.attributes
        assert span_server.attributes["custom-something"] == "keep_this_0"
        assert "TriggeredTrace" in span_server.attributes
        assert span_server.attributes["TriggeredTrace"] == True
        assert "foo" not in span_server.attributes

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####sw-keys....custom-something"),
        ])
        assert span_client.context.trace_state == expected_trace_state

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
        assert not "custom-something" in span_client.attributes
        assert not "TriggeredTrace" in span_client.attributes
        assert "foo" not in span_client.attributes

    def test_keep_values_with_equals_signs(self):
        resp_json = self.get_response(
            {
                "x-trace-options": "trigger-trace;custom-something=value_thing=4;custom-OtherThing=other val;sw-keys=g049sj345=0spd",
                "some-header": "some-value"
            }
        )
        self.check_some_header_ok(resp_json)

        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert "tracestate" in resp_json
        assert resp_json["tracestate"] == "sw={}".format(
            "-".join(self.get_new_span_id_and_trace_flags(resp_json)),
        )

        # Verify spans exported: service entry (root) + outgoing request
        # (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok"),
        ])
        assert span_server.context.trace_state == expected_trace_state

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     SWKeys, because included in xtraceoptions in otel context
        #     custom-*, because included in xtraceoptions in otel context
        #     TriggeredTrace, because trigger-trace in otel context
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     the ignored value in the x-trace-options-header
        assert all(attr_key in span_server.attributes for attr_key in ["BucketCapacity", "BucketRate"])
        assert span_server.attributes["BucketCapacity"] == 6
        assert span_server.attributes["BucketRate"] == 5
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" in span_server.attributes
        assert span_server.attributes["SWKeys"] == "g049sj345=0spd"
        assert "custom-something" in span_server.attributes
        assert span_server.attributes["custom-something"] == "value_thing=4"
        assert "custom-OtherThing" in span_server.attributes
        assert span_server.attributes["custom-OtherThing"] == "other val"
        assert "TriggeredTrace" in span_server.attributes
        assert span_server.attributes["TriggeredTrace"] == True
        assert "foo" not in span_server.attributes

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok"),
        ])
        assert span_client.context.trace_state == expected_trace_state

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
        assert not "custom-something" in span_client.attributes
        assert not "custom-OtherThing" in span_client.attributes
        assert not "TriggeredTrace" in span_client.attributes
        assert "foo" not in span_client.attributes

    def test_ignore_tt_with_value(self):
        resp_json = self.get_response(
            {
                "x-trace-options": "trigger-trace=1;custom-something=value_thing=4;custom-OtherThing=other val;sw-keys=g049sj345=0spd",
                "some-header": "some-value"
            }
        )
        self.check_some_header_ok(resp_json)

        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert "tracestate" in resp_json
        assert resp_json["tracestate"] == "sw={}".format(
            "-".join(self.get_new_span_id_and_trace_flags(resp_json)),
        )

        # Verify spans exported: service entry (root) + outgoing request
        # (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####not-requested;ignored####trigger-trace"),
        ])
        assert span_server.context.trace_state == expected_trace_state

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     SWKeys, because included in xtraceoptions in otel context
        #     custom-*, because included in xtraceoptions in otel context
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     TriggeredTrace, because no valid trigger-trace in otel context
        #     the ignored value in the x-trace-options-header
        assert all(attr_key in span_server.attributes for attr_key in ["BucketCapacity", "BucketRate"])
        assert span_server.attributes["BucketCapacity"] == 2
        assert span_server.attributes["BucketRate"] == 1
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" in span_server.attributes
        assert span_server.attributes["SWKeys"] == "g049sj345=0spd"
        assert "custom-something" in span_server.attributes
        assert span_server.attributes["custom-something"] == "value_thing=4"
        assert "custom-OtherThing" in span_server.attributes
        assert span_server.attributes["custom-OtherThing"] == "other val"
        assert "TriggeredTrace" not in span_server.attributes

        # Check client span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####not-requested;ignored####trigger-trace"),
        ])
        assert span_client.context.trace_state == expected_trace_state

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
        assert not "custom-something" in span_client.attributes
        assert not "custom-OtherThing" in span_client.attributes
        assert not "TriggeredTrace" in span_client.attributes

    def test_single_quotes_ok(self):
        resp_json = self.get_response(
            {
                "x-trace-options": "trigger-trace;custom-foo='bar;bar';custom-bar=foo",
                "some-header": "some-value"
            }
        )
        self.check_some_header_ok(resp_json)

        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert "tracestate" in resp_json
        assert resp_json["tracestate"] == "sw={}".format(
            "-".join(self.get_new_span_id_and_trace_flags(resp_json)),
        )

        # Verify spans exported: service entry (root) + outgoing request
        # (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####bar'"),
        ])
        assert span_server.context.trace_state == expected_trace_state

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     custom-*, because included in xtraceoptions in otel context
        #     TriggeredTrace, because trigger-trace in otel context
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     SWKeys, because not included in xtraceoptions in otel context
        #     the ignored value in the x-trace-options-header
        assert all(attr_key in span_server.attributes for attr_key in ["BucketCapacity", "BucketRate"])
        assert span_server.attributes["BucketCapacity"] == 6
        assert span_server.attributes["BucketRate"] == 5
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" not in span_server.attributes
        assert "custom-foo" in span_server.attributes
        assert span_server.attributes["custom-foo"] == "'bar"
        assert "custom-bar" in span_server.attributes
        assert span_server.attributes["custom-bar"] == "foo"
        assert "TriggeredTrace" in span_server.attributes
        assert span_server.attributes["TriggeredTrace"] == True
        assert "bar'" not in span_server.attributes

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####bar'"),
        ])
        assert span_client.context.trace_state == expected_trace_state

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
        assert not "custom-foo" in span_client.attributes
        assert not "custom-bar" in span_client.attributes
        assert not "TriggeredTrace" in span_client.attributes
        assert "bar'" not in span_client.attributes

    def test_multiple_missing_values_and_semis(self):
        resp_json = self.get_response(
            {
                "x-trace-options": ";trigger-trace;custom-something=value_thing;sw-keys=02973r70:9wqj21,0d9j1;1;2;3;4;5;=custom-key=val?;=",
                "some-header": "some-value"
            }
        )
        self.check_some_header_ok(resp_json)

        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert "tracestate" in resp_json
        assert resp_json["tracestate"] == "sw={}".format(
            "-".join(self.get_new_span_id_and_trace_flags(resp_json)),
        )

        # Verify spans exported: service entry (root) + outgoing request
        # (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####1....2....3....4....5"),
        ])
        assert span_server.context.trace_state == expected_trace_state

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     SWKeys, because included in xtraceoptions in otel context
        #     custom-*, because included in xtraceoptions in otel context
        #     TriggeredTrace, because trigger-trace in otel context
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     the ignored value in the x-trace-options-header
        assert all(attr_key in span_server.attributes for attr_key in ["BucketCapacity", "BucketRate"])
        assert span_server.attributes["BucketCapacity"] == 6
        assert span_server.attributes["BucketRate"] == 5
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" in span_server.attributes
        assert span_server.attributes["SWKeys"] == "02973r70:9wqj21,0d9j1"
        assert "custom-something" in span_server.attributes
        assert span_server.attributes["custom-something"] == "value_thing"
        assert "TriggeredTrace" in span_server.attributes
        assert span_server.attributes["TriggeredTrace"] == True
        assert "custom-key" not in span_server.attributes
        assert "1" not in span_server.attributes
        assert "2" not in span_server.attributes
        assert "3" not in span_server.attributes
        assert "4" not in span_server.attributes
        assert "5" not in span_server.attributes

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####1....2....3....4....5"),
        ])
        assert span_client.context.trace_state == expected_trace_state

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
        assert not "custom-something" in span_client.attributes
        assert not "TriggeredTrace" in span_client.attributes
        assert not "custom-key" in span_client.attributes
        assert "1" not in span_server.attributes
        assert "2" not in span_server.attributes
        assert "3" not in span_server.attributes
        assert "4" not in span_server.attributes
        assert "5" not in span_server.attributes

    def test_custom_key_spaces_not_allowed(self):
        resp_json = self.get_response(
            {
                "x-trace-options": "trigger-trace;custom- key=this_is_bad;custom-key 7=this_is_bad_too",
                "some-header": "some-value"
            }
        )
        self.check_some_header_ok(resp_json)

        # In this test we know tracestate will have `sw`
        # with new_span_id and new_trace_flags.
        # `xtrace_options_response` is not propagated.
        assert "tracestate" in resp_json
        assert resp_json["tracestate"] == "sw={}".format(
            "-".join(self.get_new_span_id_and_trace_flags(resp_json)),
        )

        # Verify spans exported: service entry (root) + outgoing request
        # (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####custom- key....custom-key 7"),
        ])
        assert span_server.context.trace_state == expected_trace_state

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     TriggeredTrace, because trigger-trace in otel context
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     SWKeys, because not included in xtraceoptions in otel context
        #     the ignored value in the x-trace-options-header
        assert all(attr_key in span_server.attributes for attr_key in ["BucketCapacity", "BucketRate"])
        assert span_server.attributes["BucketCapacity"] == 6
        assert span_server.attributes["BucketRate"] == 5
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" not in span_server.attributes
        assert "TriggeredTrace" in span_server.attributes
        assert span_server.attributes["TriggeredTrace"] == True
        assert "custom- key" not in span_server.attributes
        assert "custom-key 7" not in span_server.attributes

        # Check root span tracestate has `xtrace_options_response` key
        # SWO APM uses TraceState to stash the trigger trace response so it's available
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("xtrace_options_response", "trigger-trace####ok;ignored####custom- key....custom-key 7"),
        ])
        assert span_client.context.trace_state == expected_trace_state

        # Check outgoing request span attributes
        #   :absent:
        #     service entry internal KVs, which are only on entry spans
        #     sw.tracestate_parent_id, because cannot be set without attributes at decision
        #     SWKeys, because only written for service entry spans
        #     TriggeredTrace, because only written for service entry spans
        #     the ignored value in the x-trace-options-header
        assert not any(attr_key in span_client.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert not "sw.tracestate_parent_id" in span_client.attributes
        assert not "SWKeys" in span_client.attributes
        assert not "TriggeredTrace" in span_client.attributes
        assert "custom- key" not in span_server.attributes
        assert "custom-key 7" not in span_server.attributes
