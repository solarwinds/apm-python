# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import re
import json

from opentelemetry import trace as trace_api
from opentelemetry._logs import SeverityNumber
from unittest import mock

from .test_base_sw_otlp import TestBaseSwOtlp


class TestScenario4(TestBaseSwOtlp):
    """
    Test class for continuing tracing decision with input headers
    for traceparent and tracestate.
    """

    def test_scenario_4_sampled(self):
        """
        Scenario #4, sampled: 
        1. Decision to sample is continued at service entry span (mocked). This is
           not the root span because it continues an existing OTel context.
        2. traceparent and tracestate headers in the request to the test app are
        injected into the outgoing request (done by OTel TraceContextTextMapPropagator).
        3. The injected traceparent's trace_id is the trace_id of all spans.
        4. Sampling-related attributes are set for the service entry span.
        5. The span_id of the outgoing request span matches the span_id portion in the tracestate header.
        """
        trace_id = "11112222333344445555666677778888"
        span_id = "1000100010001000"
        trace_flags = "01"
        traceparent = "00-{}-{}-{}".format(trace_id, span_id, trace_flags)
        tracestate_span = "e000baa4e000baa4"
        tracestate = "sw={}-{}".format(tracestate_span, trace_flags)

        # Use in-process test app client and mock to propagate context
        # and create in-memory trace
        resp = None
        # liboboe mocked to guarantee return of "do_sample" (2nd arg)
        mock_decision = mock.Mock(
            return_value=(1, 1, 3, 4, 5.0, 6.0, 1, 0, "ok", "ok", 0)
        )
        with mock.patch(
            target="solarwinds_apm.extension.oboe.OboeAPI.getTracingDecision",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "traceparent": traceparent,
                    "tracestate": tracestate,
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
        #    - traceparent with a trace_id, trace_flags from original request
        #    - tracestate from original request
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
        assert new_trace_id == trace_id
        new_span_id = traceparent_re_result.group(3)
        assert new_span_id is not None
        new_trace_flags = traceparent_re_result.group(4)
        assert new_trace_flags == trace_flags

        assert "tracestate" in resp_json
        # In this test we know there is only `sw` in tracestate
        # and its value will be new_span_id and new_trace_flags
        assert resp_json["tracestate"] == "sw={}-{}".format(new_span_id, new_trace_flags)

        # Verify the OTel context extracted from the original request are continued by
        # the trace context injected into test app's outgoing postman-echo call
        try:
            assert resp_json["incoming-headers"]["traceparent"] == traceparent
            assert new_trace_id in resp_json["incoming-headers"]["traceparent"]
            assert new_span_id not in resp_json["incoming-headers"]["traceparent"]
            assert new_trace_flags in resp_json["incoming-headers"]["traceparent"]

            assert resp_json["incoming-headers"]["tracestate"] == tracestate
            assert "sw=" in resp_json["incoming-headers"]["tracestate"]
            assert new_span_id not in resp_json["incoming-headers"]["tracestate"]
            assert new_trace_flags in resp_json["incoming-headers"]["tracestate"]
        except KeyError as e:
            self.fail("KeyError was raised at continue trace check: {}".format(e))

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify spans exported: service entry + outgoing request (child with local parent)
        spans = self.memory_span_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]
        assert span_server.name == "GET /test_trace/"
        assert span_server.kind == trace_api.SpanKind.SERVER
        assert span_client.name == "GET"
        assert span_client.kind == trace_api.SpanKind.CLIENT

        # Check spans' trace_id, which should match traceparent of original request
        # Note: context.trace_id needs a 32-byte hex conversion first.
        assert "{:032x}".format(span_server.context.trace_id) == trace_id
        assert "{:032x}".format(span_client.context.trace_id) == trace_id

        # Check service entry span tracestate has `sw` key
        # In this test it should be tracestate_span_id, traceflags from extracted traceparent
        expected_trace_state = trace_api.TraceState([
            ("sw", "{}-{}".format(tracestate_span, trace_flags))
        ])
        assert span_server.context.trace_state.get("sw") == expected_trace_state.get("sw")

        # Check service entry span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     sw.tracestate_parent_id, because only set if not the root and no attributes
        #   :absent:
        #     SWKeys, because no xtraceoptions in otel context
        assert all(attr_key in span_server.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert span_server.attributes["BucketCapacity"] == "6.0"
        assert span_server.attributes["BucketRate"] == "5.0"
        assert span_server.attributes["SampleRate"] == 3
        assert span_server.attributes["SampleSource"] == 4
        assert "sw.tracestate_parent_id" in span_server.attributes
        assert span_server.attributes["sw.tracestate_parent_id"] == tracestate_span
        assert not "SWKeys" in span_server.attributes

        # Check outgoing request tracestate has `sw` key
        # In this test it should also be tracestate_span_id, traceflags from extracted traceparent
        expected_trace_state = trace_api.TraceState([
            ("sw", "{}-{}".format(tracestate_span, trace_flags))
        ])
        assert span_client.context.trace_state.get("sw") == expected_trace_state.get("sw")

        # Check outgoing request span attributes
        #   :absent:
        #     service entry internal KVs, which are only on entry spans
        #     sw.tracestate_parent_id, because cannot be set without attributes at decision
        #     SWKeys, because no xtraceoptions in otel context
        assert not any(attr_key in span_client.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert not "sw.tracestate_parent_id" in span_client.attributes
        assert not "SWKeys" in span_client.attributes

        # Check span_id of the outgoing request span (client span) matches
        # the span_id portion in the outgoing tracestate header, which
        # is stored in the test app's response body (new_span_id).
        # Note: context.span_id needs a 16-byte hex conversion first.
        assert "{:016x}".format(span_client.context.span_id) == new_span_id

        # Server metrics from test app Flask instrumentation
        metric_data = self.metric_reader.get_metrics_data()
        metrics = metric_data.resource_metrics[0].scope_metrics[0].metrics
        self.assertEqual(len(metrics), 2)
        active_requests = metrics[0]
        self.assertEqual(
            active_requests.name,
            "http.server.active_requests",
        )
        self.assertEqual(
            active_requests.data.data_points[0].attributes,
            {"http.request.method": "GET", "url.scheme": "http"},
        )
        request_duration = metrics[1]
        self.assertEqual(
            request_duration.name,
            "http.server.request.duration",
        )
        self.assertEqual(
            request_duration.data.data_points[0].attributes,
            {
                "http.request.method": "GET",
                "url.scheme": "http",
                "network.protocol.version": "1.1",
                "http.response.status_code": 200,
                "http.route": "/test_trace/"
            },
        )

        # Client metrics from test app Requests instrumentation
        metric_data = self.metric_reader.get_metrics_data()
        metrics = metric_data.resource_metrics[0].scope_metrics[1].metrics
        self.assertEqual(len(metrics), 1)
        request_duration = metrics[0]
        self.assertEqual(
            request_duration.name,
            "http.client.request.duration",
        )
        self.assertEqual(
            request_duration.data.data_points[0].attributes,
            {
                "http.request.method": "GET",
                "server.address": "postman-echo.com",
                "http.response.status_code": 200,
                "network.protocol.version": "1.1",
            },
        )

        # SW response time metrics
        metric_data = self.metric_reader.get_metrics_data()
        scope = metric_data.resource_metrics[0].scope_metrics[2].scope
        self.assertEqual(
            scope.name,
            "sw.apm.request.metrics",
        )
        metrics = metric_data.resource_metrics[0].scope_metrics[2].metrics
        self.assertEqual(len(metrics), 1)
        response_time = metrics[0]
        self.assertEqual(
            response_time.name,
            "trace.service.response_time",
        )
        self.assertEqual(
            response_time.data.data_points[0].attributes,
            {
                "sw.is_error": False,
                "sw.transaction": "GET /test_trace/"
            },
        )
        self.assertEqual(
            response_time.data.aggregation_temporality,
            2,  # cumulative
        )

        # SW request count metrics
        metric_data = self.metric_reader.get_metrics_data()
        scope = metric_data.resource_metrics[0].scope_metrics[3].scope
        self.assertEqual(
            scope.name,
            "sw.apm.sampling.metrics",
        )
        metrics = metric_data.resource_metrics[0].scope_metrics[3].metrics
        self.assertEqual(len(metrics), 6)
        self.assertEqual(metrics[0].name, "trace.service.tracecount")
        self.assertEqual(metrics[1].name, "trace.service.samplecount")
        self.assertEqual(metrics[2].name, "trace.service.request_count")
        self.assertEqual(metrics[3].name, "trace.service.tokenbucket_exhaustion_count")
        self.assertEqual(metrics[4].name, "trace.service.through_trace_count")
        self.assertEqual(metrics[5].name, "trace.service.triggered_trace_count")

        finished_logs = self.memory_log_exporter.get_finished_logs()
        self.assertEqual(len(finished_logs), 1)
        warning_log_record = finished_logs[0].log_record
        self.assertEqual(warning_log_record.body, "My foo log!")
        self.assertEqual(warning_log_record.severity_text, "WARN")
        self.assertEqual(
            warning_log_record.severity_number, SeverityNumber.WARN
        )
        self.assertEqual(
            finished_logs[0].instrumentation_scope.name, "foo-logger"
        )

    def test_scenario_4_not_sampled(self):
        """
        Scenario #4, NOT sampled:
        1. Decision to NOT sample is continued at service entry span (mocked). This is
           not the root span because it continues an existing OTel context.
        2. traceparent and tracestate headers in the request to the test app are
        injected into the outgoing request (done by OTel TraceContextTextMapPropagator).
        3. No spans are exported.
        """
        trace_id = "11112222333344445555666677778888"
        span_id = "1000100010001000"
        trace_flags = "00"
        traceparent = "00-{}-{}-{}".format(trace_id, span_id, trace_flags)
        tracestate_span = "e000baa4e000baa4"
        tracestate = "sw={}-{}".format(tracestate_span, trace_flags)

        # Use in-process test app client and mock to propagate context
        # and create in-memory trace
        resp = None
        # liboboe mocked to guarantee return of "do_sample" (2nd arg)
        mock_decision = mock.Mock(
            return_value=(1, 0, 3, 4, 5.0, 6.0, 1, 0, "ok", "ok", 0)
        )
        with mock.patch(
            target="solarwinds_apm.extension.oboe.OboeAPI.getTracingDecision",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "traceparent": traceparent,
                    "tracestate": tracestate,
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
        #    - traceparent with a trace_id, trace_flags from original request
        #    - tracestate from original request
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
        assert new_trace_id == trace_id
        new_span_id = traceparent_re_result.group(3)
        assert new_span_id is not None
        new_trace_flags = traceparent_re_result.group(4)
        assert new_trace_flags == trace_flags

        assert "tracestate" in resp_json
        # In this test we know there is only `sw` in tracestate
        # and its value will be new_span_id and new_trace_flags
        assert resp_json["tracestate"] == "sw={}-{}".format(new_span_id, new_trace_flags)

        # Verify the OTel context extracted from the original request are continued by
        # the trace context injected into test app's outgoing postman-echo call
        try:
            assert resp_json["incoming-headers"]["traceparent"] == traceparent
            assert new_trace_id in resp_json["incoming-headers"]["traceparent"]
            assert new_span_id not in resp_json["incoming-headers"]["traceparent"]
            assert new_trace_flags in resp_json["incoming-headers"]["traceparent"]

            assert resp_json["incoming-headers"]["tracestate"] == tracestate
            assert "sw=" in resp_json["incoming-headers"]["tracestate"]
            assert new_span_id not in resp_json["incoming-headers"]["tracestate"]
            assert new_trace_flags in resp_json["incoming-headers"]["tracestate"]
        except KeyError as e:
            self.fail("KeyError was raised at continue trace check: {}".format(e))

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify no spans exported
        spans = self.memory_span_exporter.get_finished_spans()
        assert len(spans) == 0

        # Server metrics from test app Flask instrumentation
        metric_data = self.metric_reader.get_metrics_data()
        metrics = metric_data.resource_metrics[0].scope_metrics[0].metrics
        self.assertEqual(len(metrics), 2)
        active_requests = metrics[0]
        self.assertEqual(
            active_requests.name,
            "http.server.active_requests",
        )
        self.assertEqual(
            active_requests.data.data_points[0].attributes,
            {"http.request.method": "GET", "url.scheme": "http"},
        )
        request_duration = metrics[1]
        self.assertEqual(
            request_duration.name,
            "http.server.request.duration",
        )
        self.assertEqual(
            request_duration.data.data_points[0].attributes,
            {
                "http.request.method": "GET",
                "url.scheme": "http",
                "network.protocol.version": "1.1",
                "http.response.status_code": 200,
                "http.route": "/test_trace/"
            },
        )

        # Client metrics from test app Requests instrumentation
        metric_data = self.metric_reader.get_metrics_data()
        metrics = metric_data.resource_metrics[0].scope_metrics[1].metrics
        self.assertEqual(len(metrics), 1)
        request_duration = metrics[0]
        self.assertEqual(
            request_duration.name,
            "http.client.request.duration",
        )
        self.assertEqual(
            request_duration.data.data_points[0].attributes,
            {
                "http.request.method": "GET",
                "server.address": "postman-echo.com",
                "network.protocol.version": "1.1",
            },
        )

        # SW response time metrics
        metric_data = self.metric_reader.get_metrics_data()
        scope = metric_data.resource_metrics[0].scope_metrics[2].scope
        self.assertEqual(
            scope.name,
            "sw.apm.request.metrics",
        )
        metrics = metric_data.resource_metrics[0].scope_metrics[2].metrics
        self.assertEqual(len(metrics), 1)
        response_time = metrics[0]
        self.assertEqual(
            response_time.name,
            "trace.service.response_time",
        )
        self.assertEqual(
            response_time.data.data_points[0].attributes,
            {
                "sw.is_error": False,
                "sw.transaction": "GET /test_trace/"
            },
        )
        self.assertEqual(
            response_time.data.aggregation_temporality,
            2,  # cumulative
        )

        # SW request count metrics
        metric_data = self.metric_reader.get_metrics_data()
        scope = metric_data.resource_metrics[0].scope_metrics[3].scope
        self.assertEqual(
            scope.name,
            "sw.apm.sampling.metrics",
        )
        metrics = metric_data.resource_metrics[0].scope_metrics[3].metrics
        self.assertEqual(len(metrics), 6)
        self.assertEqual(metrics[0].name, "trace.service.tracecount")
        self.assertEqual(metrics[1].name, "trace.service.samplecount")
        self.assertEqual(metrics[2].name, "trace.service.request_count")
        self.assertEqual(metrics[3].name, "trace.service.tokenbucket_exhaustion_count")
        self.assertEqual(metrics[4].name, "trace.service.through_trace_count")
        self.assertEqual(metrics[5].name, "trace.service.triggered_trace_count")

        finished_logs = self.memory_log_exporter.get_finished_logs()
        self.assertEqual(len(finished_logs), 1)
        warning_log_record = finished_logs[0].log_record
        self.assertEqual(warning_log_record.body, "My foo log!")
        self.assertEqual(warning_log_record.severity_text, "WARN")
        self.assertEqual(
            warning_log_record.severity_number, SeverityNumber.WARN
        )
        self.assertEqual(
            finished_logs[0].instrumentation_scope.name, "foo-logger"
        )
