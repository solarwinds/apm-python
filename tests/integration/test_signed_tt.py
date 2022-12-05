import re
import json

from opentelemetry import trace as trace_api
from unittest import mock

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
        3. A x-trace-options-response header is calculated using the extracted x-trace-options
           and injected into the HTTP response.
        4. Sampling-related, SWKeys, custom-*, and TriggeredTrace attributes are set
           for the root/service entry span, but not what's ignored.
        5. The span_id of the outgoing request span matches the span_id portion in the
           tracestate header.
        """
        # Use in-process test app client and mock to propagate context
        # and create in-memory trace
        resp = None
        # liboboe mocked to guarantee return of "do_sample" (2nd arg),
        # plus status_msg (the first "ok" string)
        mock_decision = mock.Mock(
            return_value=(1, 1, -1, -1, 5.0, 6.0, 1, 0, "ok", "ok", 0)
        )
        with mock.patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo",
                    "x-trace-options-signature": "foo-sig",
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
        # In this test we know there is `sw` and `xtrace_options_response` in tracestate
        # where value of former will be new_span_id and new_trace_flags
        assert resp_json["tracestate"] == "sw={}-{},xtrace_options_response=auth####ok;trigger-trace####ok;ignored####this-will-be-ignored".format(new_span_id, new_trace_flags)

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
        assert span_server.name == "/test_trace/"
        assert span_server.kind == trace_api.SpanKind.SERVER
        assert span_client.name == "HTTP GET"
        assert span_client.kind == trace_api.SpanKind.CLIENT

        # Check root span tracestate has `sw` and `xtrace_options_response` keys
        # In this test we know `sw` value will have invalid span_id
        expected_trace_state = trace_api.TraceState([
            ("sw", "0000000000000000-01"),
            ("xtrace_options_response", "auth####ok;trigger-trace####ok;ignored####this-will-be-ignored"),
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
        assert all(attr_key in span_server.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert span_server.attributes["BucketCapacity"] == "6.0"
        assert span_server.attributes["BucketRate"] == "5.0"
        assert span_server.attributes["SampleRate"] == -1
        assert span_server.attributes["SampleSource"] == -1
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" in span_server.attributes
        assert span_server.attributes["SWKeys"] == "check-id:check-1013,website-id:booking-demo"
        assert "custom-awesome-key" in span_server.attributes
        assert span_server.attributes["custom-awesome-key"] == "foo"
        assert "TriggeredTrace" in span_server.attributes
        assert span_server.attributes["TriggeredTrace"] == True
        assert "this-will-be-ignored" not in span_server.attributes

        # Check root span tracestate has `sw` and `xtrace_options_response` keys
        # In this test we know `sw` value will also have invalid span_id.
        # SWO APM uses TraceState to stash the trigger trace response so it's available 
        # at the time of custom injecting the x-trace-options-response header.
        expected_trace_state = trace_api.TraceState([
            ("sw", "0000000000000000-01"),
            ("xtrace_options_response", "auth####ok;trigger-trace####ok;ignored####this-will-be-ignored"),
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
        Signed request without trigger-trace, auth ok:
        1. Decision to sample is made at root/service entry span (mocked). There
           is no OTel context extracted from request headers, so this is the root
           and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. No x-trace-options-response header is calculated because the extracted
           x-trace-options does not include trigger-trace.
        4. Sampling-related, SWKeys, and custom-*, and attributes are set
           for the root/service entry span, but not what's ignored nor TriggeredTrace.
        5. The span_id of the outgoing request span matches the span_id portion in the
           tracestate header.
        """
        # Use in-process test app client and mock to propagate context
        # and create in-memory trace
        resp = None
        # liboboe mocked to guarantee return of "do_sample" (2nd arg),
        # plus status_msg (the first "ok" string)
        mock_decision = mock.Mock(
            return_value=(1, 1, -1, -1, 5.0, 6.0, 0, 0, "ok", "ok", 0)
        )
        with mock.patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": "sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo",
                    "x-trace-options-signature": "foo-sig",
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

        # Verify spans exported: service entry (root) + outgoing request (child with local parent)
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]
        assert span_server.name == "/test_trace/"
        assert span_server.kind == trace_api.SpanKind.SERVER
        assert span_client.name == "HTTP GET"
        assert span_client.kind == trace_api.SpanKind.CLIENT

        # Check root span tracestate has `sw` key.
        # In this test we know `sw` value will have invalid span_id.
        # There should be no `xtrace_options_response` key because there is
        # no trigger-trace in the extracted x-trace-options header.
        expected_trace_state = trace_api.TraceState([
            ("sw", "0000000000000000-01"),
        ])
        assert span_server.context.trace_state == expected_trace_state

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     SWKeys, because included in xtraceoptions in otel context
        #     custom-*, because included in xtraceoptions in otel context
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set at root nor without attributes at decision
        #     TriggeredTrace, because trigger-trace not in otel context
        #     the ignored value in the x-trace-options-header
        assert all(attr_key in span_server.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert span_server.attributes["BucketCapacity"] == "6.0"
        assert span_server.attributes["BucketRate"] == "5.0"
        assert span_server.attributes["SampleRate"] == -1
        assert span_server.attributes["SampleSource"] == -1
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert "SWKeys" in span_server.attributes
        assert span_server.attributes["SWKeys"] == "check-id:check-1013,website-id:booking-demo"
        assert "custom-awesome-key" in span_server.attributes
        assert span_server.attributes["custom-awesome-key"] == "foo"
        assert "TriggeredTrace" not in span_server.attributes
        assert "this-will-be-ignored" not in span_server.attributes

        # Check root span tracestate has `sw` key/
        # In this test we know `sw` value will also have invalid span_id.
        # There should be no `xtrace_options_response` key because there is
        # no trigger-trace in the extracted x-trace-options header.
        expected_trace_state = trace_api.TraceState([
            ("sw", "0000000000000000-01"),
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
        3. No spans are exported.
        """
        # liboboe mocked to guarantee return of "do_sample" (2nd arg),
        # plus status_msg (the "rate-exceeded" string)
        mock_decision = mock.Mock(
            return_value=(1, 0, -1, -1, 5.0, 6.0, 0, -1, "rate-exceeded", "ok", -4)
        )
        with mock.patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo",
                    "x-trace-options-signature": "foo-sig",
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
        # In this test we know there is `sw` and `xtrace_options_response` in tracestate
        # where value of former will be new_span_id and new_trace_flags
        assert resp_json["tracestate"] == "sw={}-{},xtrace_options_response=auth####ok;trigger-trace####rate-exceeded;ignored####this-will-be-ignored".format(new_span_id, new_trace_flags)

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

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
        3. No spans are exported.
        """
        # liboboe mocked to guarantee return of "do_sample" (2nd arg),
        # plus status_msg (the "rate-exceeded" string)
        mock_decision = mock.Mock(
            return_value=(1, 0, -1, -1, 5.0, 6.0, 0, -1, "tracing-disabled", "ok", -2)
        )
        with mock.patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo",
                    "x-trace-options-signature": "foo-sig",
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
        # In this test we know there is `sw` and `xtrace_options_response` in tracestate
        # where value of former will be new_span_id and new_trace_flags
        assert resp_json["tracestate"] == "sw={}-{},xtrace_options_response=auth####ok;trigger-trace####tracing-disabled;ignored####this-will-be-ignored".format(new_span_id, new_trace_flags)

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify no spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_signed_auth_fail(self):
        """
        Signed request with trigger-trace, auth fail:
        1. Decision to sample with failed signed trigger trace flag is made at root/service
           entry span (mocked). There is no OTel context extracted from request headers,
           so this is the root and start of the trace.
        2. Some traceparent and tracestate are injected into service's outgoing request
           (done by OTel TraceContextTextMapPropagator).
        3. No spans are exported.
        """
        # Use in-process test app client and mock to propagate context
        # and create in-memory trace
        resp = None
        # liboboe mocked to guarantee return of "do_sample" (2nd arg)
        # and auth-failed due to bad-signature
        mock_decision = mock.Mock(
            return_value=(1, 0, 100, 6, 0.0, 0.0, -1, 2, "auth-failed", "bad-signature", -5)
        )
        with mock.patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "x-trace-options": "trigger-trace;sw-keys=check-id:check-1013,website-id:booking-demo;this-will-be-ignored;custom-awesome-key=foo",
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
        # In this test we know there is `sw` and `xtrace_options_response` in tracestate
        # where value of former will be new_span_id and new_trace_flags.
        # The `xtrace_options_response` excludes trigger-trace because of the auth failure. 
        assert resp_json["tracestate"] == "sw={}-{},xtrace_options_response=auth####bad-signature;ignored####this-will-be-ignored".format(new_span_id, new_trace_flags)

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

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
        4. No spans are exported.
        """
        # Use in-process test app client and mock to propagate context
        # and create in-memory trace
        resp = None
        # liboboe mocked to guarantee return of "do_sample" (2nd arg)
        # and auth-failed due to bad-signature
        mock_decision = mock.Mock(
            return_value=(1, 0, 100, 6, 0.0, 0.0, -1, 2, "auth-failed", "bad-signature", -5)
        )
        with mock.patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
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

        # Verify no spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 0
