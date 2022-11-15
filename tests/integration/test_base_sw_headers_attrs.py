import hashlib
import hmac
import os
from pkg_resources import (
    iter_entry_points,
    load_entry_point
)
import json
import re
import time

import flask
import requests
from unittest import mock
from unittest.mock import patch
from werkzeug.test import Client
from werkzeug.wrappers import Response

from opentelemetry import trace as trace_api
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.propagate import get_global_textmap
from opentelemetry.sdk.trace import TracerProvider, export
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.test.globals_test import reset_trace_globals
from opentelemetry.test.test_base import TestBase

from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.configurator import SolarWindsConfigurator
from solarwinds_apm.distro import SolarWindsDistro
from solarwinds_apm.propagator import SolarWindsPropagator
from solarwinds_apm.sampler import ParentBasedSwSampler


class TestBaseSwHeadersAndAttributes(TestBase):

    SW_SETTINGS_KEYS = [
        "BucketCapacity",
        "BucketRate",
        "SampleRate",
        "SampleSource"
    ]

    @staticmethod
    def _test_trace():
        resp = requests.get(f"http://postman-echo.com/headers")

        #  The return type must be a string, dict, tuple, Response instance, or WSGI callable
        # (not CaseInsensitiveDict)
        return {
            "traceparent": resp.request.headers["traceparent"],
            "tracestate": resp.request.headers["tracestate"],
        }
    
    def _setup_endpoints(self):
        # pylint: disable=no-member
        self.app.route("/test_trace/")(self._test_trace)
        # pylint: disable=attribute-defined-outside-init
        self.client = Client(self.app, Response)

    def setUp(self):
        """Set up called before each test scenario"""
        # Based on auto_instrumentation run() and sitecustomize.py
        # Load OTel env vars entry points
        argument_otel_environment_variable = {}
        for entry_point in iter_entry_points(
            "opentelemetry_environment_variables"
        ):
            environment_variable_module = entry_point.load()
            for attribute in dir(environment_variable_module):
                if attribute.startswith("OTEL_"):
                    argument = re.sub(r"OTEL_(PYTHON_)?", "", attribute).lower()
                    argument_otel_environment_variable[argument] = attribute

        # Set APM service key
        os.environ["SW_APM_SERVICE_KEY"] = "foo:bar"

        # Load Distro
        SolarWindsDistro().configure()
        assert os.environ["OTEL_PROPAGATORS"] == "tracecontext,baggage,solarwinds_propagator"

        # Load Configurator to Configure SW custom SDK components
        # except use TestBase InMemorySpanExporter
        apm_config = SolarWindsApmConfig()
        configurator = SolarWindsConfigurator()
        configurator._initialize_solarwinds_reporter(apm_config)
        configurator._configure_propagator()
        configurator._configure_response_propagator()
        # This is done because set_tracer_provider cannot override the
        # current tracer provider. Has to be done here.
        reset_trace_globals()
        sampler = load_entry_point(
            "solarwinds_apm",
            "opentelemetry_traces_sampler",
            configurator._DEFAULT_SW_TRACES_SAMPLER
        )(apm_config)
        self.tracer_provider = TracerProvider(sampler=sampler)
        # Set InMemorySpanExporter for testing
        # We do NOT use SolarWindsSpanExporter
        self.memory_exporter = InMemorySpanExporter()
        span_processor = export.SimpleSpanProcessor(self.memory_exporter)
        self.tracer_provider.add_span_processor(span_processor)
        trace_api.set_tracer_provider(self.tracer_provider)
        self.tracer = self.tracer_provider.get_tracer(__name__)

        # Make sure SW SDK components were set
        propagators = get_global_textmap()._propagators
        assert len(propagators) == 3
        assert isinstance(propagators[2], SolarWindsPropagator)
        assert isinstance(trace_api.get_tracer_provider().sampler, ParentBasedSwSampler)

        # We need to instrument and create test app for every test
        self.requests_inst = RequestsInstrumentor()
        self.flask_inst = FlaskInstrumentor()
        self.flask_inst.uninstrument()
        self.flask_inst.instrument(
            tracer_provider=trace_api.get_tracer_provider()
        )
        self.requests_inst.uninstrument()
        self.requests_inst.instrument(
            tracer_provider=trace_api.get_tracer_provider()
        )
        self.app = flask.Flask(__name__)
        self._setup_endpoints()
        self.client = Client(self.app, Response)

    def tearDown(self):
        """Teardown called after each test scenario"""
        # clean up for other tests
        self.memory_exporter.clear()

    def test_scenario_1(self):
        """
        Scenario #1:
        1. Decision to sample is made at root/service entry span (mocked).
        2. Some traceparent and tracestate are injected into service's outgoing request (done by OTel TraceContextTextMapPropagator).
        3. Sampling-related attributes are set for the root/service entry span.
        4. The span_id of the outgoing request span matches the span_id portion in the tracestate header.
        """
        # Use in-process test app client and mock to propagate context
        # and create in-memory trace
        resp = None
        # liboboe mocked to guarantee return of "do_sample" and "start
        # decision" rate/capacity values in order to trace and set attrs
        mock_decision = mock.Mock(
            return_value=(1, 1, 3, 4, 5.0, 6.0, 1, 0, "ok", "ok", 0)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app, no traceparent/tracestate
            resp = self.client.get("/test_trace/")
        resp_json = json.loads(resp.data)

        # Verify trace context injected into test app's outgoing postman-echo call
        # (added to Flask app's response data) includes:
        #    - traceparent with a trace_id, span_id, and trace_flags for do_sample
        #    - tracestate with same span_id and trace_flags for do_sample
        assert "traceparent" in resp_json
        _TRACEPARENT_HEADER_FORMAT = (
            "^[ \t]*([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})"
            + "(-.*)?[ \t]*$"
        )
        _TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)
        traceparent_re_result = re.search(
            _TRACEPARENT_HEADER_FORMAT_RE,
            resp_json["traceparent"],
        )
        new_trace_id = traceparent_re_result.group(2)
        assert new_trace_id
        new_span_id = traceparent_re_result.group(3)
        assert new_span_id
        new_trace_flags = traceparent_re_result.group(4)
        assert new_trace_flags == "01"

        assert "tracestate" in resp_json
        assert new_span_id in resp_json["tracestate"]
        # In this test we know there is only `sw` in tracestate
        # e.g. sw=e000baa4e000baa4-01
        _TRACESTATE_HEADER_FORMAT = (
            "^[ \t]*sw=([0-9a-f]{16})-([0-9a-f]{2})"
            + "(-.*)?[ \t]*$"
        )
        _TRACESTATE_HEADER_FORMAT_RE = re.compile(_TRACESTATE_HEADER_FORMAT)
        tracestate_re_result = re.search(
            _TRACESTATE_HEADER_FORMAT_RE,
            resp_json["tracestate"],
        )
        new_tracestate_flags = tracestate_re_result.group(2)
        assert new_tracestate_flags == "01"

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify spans exported: service entry (root) + outgoing request
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]
        assert span_server.name == "/test_trace/"
        assert span_server.kind == trace_api.SpanKind.SERVER
        assert span_client.name == "HTTP GET"
        assert span_client.kind == trace_api.SpanKind.CLIENT

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set without attributes at decision
        #     SWKeys, because no xtraceoptions in otel context
        assert all(attr_key in span_server.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert span_server.attributes["BucketCapacity"] == "6.0"
        assert span_server.attributes["BucketRate"] == "5.0"
        assert span_server.attributes["SampleRate"] == 3
        assert span_server.attributes["SampleSource"] == 4
        assert not "sw.tracestate_parent_id" in span_server.attributes
        assert not "SWKeys" in span_server.attributes

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

    def test_scenario_4_sampled(self):
        """
        Scenario #4, sampled: 
        1. Decision to sample is continued at root/service entry span (mocked).
        2. traceparent and tracestate headers in the request to the test app are
        injected into the outgoing request (done by OTel TraceContextTextMapPropagator).
        3. The injected traceparent's trace_id is the trace_id of all spans.
        4. Sampling-related attributes are set for the root/service entry span.
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
        # liboboe mocked to guarantee return of "do_sample" and "start
        # decision" rate/capacity values in order to trace and set attrs
        mock_decision = mock.Mock(
            return_value=(1, 1, 3, 4, 5.0, 6.0, 1, 0, "ok", "ok", 0)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "traceparent": traceparent,
                    "tracestate": tracestate,
                }
            )
        resp_json = json.loads(resp.data)

        # Verify trace context injected into test app's outgoing postman-echo call
        # (added to Flask app's response data) includes:
        #    - traceparent with a trace_id, trace_flags from original request
        #    - tracestate from original request
        assert "traceparent" in resp_json
        _TRACEPARENT_HEADER_FORMAT = (
            "^[ \t]*([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})"
            + "(-.*)?[ \t]*$"
        )
        _TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)
        traceparent_re_result = re.search(
            _TRACEPARENT_HEADER_FORMAT_RE,
            resp_json["traceparent"],
        )
        new_trace_id = traceparent_re_result.group(2)
        assert new_trace_id
        assert new_trace_id == trace_id
        new_span_id = traceparent_re_result.group(3)
        assert new_span_id
        new_trace_flags = traceparent_re_result.group(4)
        assert new_trace_flags == trace_flags

        assert "tracestate" in resp_json
        assert new_span_id in resp_json["tracestate"]
        # In this test we know there is only `sw` in tracestate
        # e.g. sw=e000baa4e000baa4-01
        # but it will be different from the original injected tracestate
        _TRACESTATE_HEADER_FORMAT = (
            "^[ \t]*sw=([0-9a-f]{16})-([0-9a-f]{2})"
            + "(-.*)?[ \t]*$"
        )
        _TRACESTATE_HEADER_FORMAT_RE = re.compile(_TRACESTATE_HEADER_FORMAT)
        tracestate_re_result = re.search(
            _TRACESTATE_HEADER_FORMAT_RE,
            resp_json["tracestate"],
        )
        new_tracestate_span = tracestate_re_result.group(1)
        assert new_tracestate_span
        assert new_tracestate_span != tracestate_span
        new_tracestate_flags = tracestate_re_result.group(2)
        assert new_tracestate_flags
        assert new_tracestate_flags == trace_flags

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify spans exported: service entry (root) + outgoing request
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]
        assert span_server.name == "/test_trace/"
        assert span_server.kind == trace_api.SpanKind.SERVER
        assert span_client.name == "HTTP GET"
        assert span_client.kind == trace_api.SpanKind.CLIENT

        # Check spans' trace_id, which should match traceparent of original request
        # Note: context.trace_id needs a 32-byte hex conversion first.
        assert "{:032x}".format(span_server.context.trace_id) == trace_id
        assert "{:032x}".format(span_client.context.trace_id) == trace_id

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     sw.tracestate_parent_id, because only set if not root and no attributes
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

    def test_scenario_4_not_sampled(self):
        """
        Scenario #4, NOT sampled:
        1. Decision to NOT sample is continued at root/service entry span (mocked).
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
        # liboboe mocked to guarantee return of "do_sample" and "start
        # decision" rate/capacity values in order to trace and set attrs
        mock_decision = mock.Mock(
            return_value=(1, 0, 3, 4, 5.0, 6.0, 1, 0, "ok", "ok", 0)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "traceparent": traceparent,
                    "tracestate": tracestate,
                }
            )
        resp_json = json.loads(resp.data)

        # Verify trace context injected into test app's outgoing postman-echo call
        # (added to Flask app's response data) includes:
        #    - traceparent with a trace_id, trace_flags from original request
        #    - tracestate from original request
        assert "traceparent" in resp_json
        _TRACEPARENT_HEADER_FORMAT = (
            "^[ \t]*([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})"
            + "(-.*)?[ \t]*$"
        )
        _TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)
        traceparent_re_result = re.search(
            _TRACEPARENT_HEADER_FORMAT_RE,
            resp_json["traceparent"],
        )
        new_trace_id = traceparent_re_result.group(2)
        assert new_trace_id
        assert new_trace_id == trace_id
        new_span_id = traceparent_re_result.group(3)
        assert new_span_id
        new_trace_flags = traceparent_re_result.group(4)
        assert new_trace_flags == trace_flags

        assert "tracestate" in resp_json
        assert new_span_id in resp_json["tracestate"]
        # In this test we know there is only `sw` in tracestate
        # e.g. sw=e000baa4e000baa4-01
        # but it will be different from the original injected tracestate
        _TRACESTATE_HEADER_FORMAT = (
            "^[ \t]*sw=([0-9a-f]{16})-([0-9a-f]{2})"
            + "(-.*)?[ \t]*$"
        )
        _TRACESTATE_HEADER_FORMAT_RE = re.compile(_TRACESTATE_HEADER_FORMAT)
        tracestate_re_result = re.search(
            _TRACESTATE_HEADER_FORMAT_RE,
            resp_json["tracestate"],
        )
        new_tracestate_span = tracestate_re_result.group(1)
        assert new_tracestate_span
        assert new_tracestate_span != tracestate_span
        new_tracestate_flags = tracestate_re_result.group(2)
        assert new_tracestate_flags
        assert new_tracestate_flags == trace_flags

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify no spans exported
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 0

    def test_scenario_6(self):
        """
        Scenario #6:
        1. Decision to sample with trigger trace flag is made at root/service entry span (mocked).
        2. traceparent and tracestate headers in the request to the test app are
        injected into the outgoing request (done by OTel TraceContextTextMapPropagator).
        3. The injected traceparent's trace_id is the trace_id of all spans.
        4. Sampling-related attributes are set for the root/service entry span.
        5. The span_id of the outgoing request span matches the span_id portion in the tracestate header.
        """
        trace_id = "11112222333344445555666677778888"
        span_id = "1000100010001000"
        trace_flags = "01"
        traceparent = "00-{}-{}-{}".format(trace_id, span_id, trace_flags)
        tracestate_span = "e000baa4e000baa4"
        tracestate = "sw={}-{}".format(tracestate_span, trace_flags)

        # Calculate current timestamp, signature, x-trace-options headers
        xtraceoptions = "trigger-trace;custom-from=lin;foo=bar;sw-keys=custom-sw-from:tammy,baz:qux;ts={}".format(int(time.time()))
        xtraceoptions_signature = hmac.new(
            b'8mZ98ZnZhhggcsUmdMbS',
            xtraceoptions.encode('ascii'),
            hashlib.sha1
        ).hexdigest()

        # Use in-process test app client and mock to propagate context
        # and create in-memory trace
        resp = None
        # liboboe mocked to guarantee return of "do_sample" and "start
        # decision" rate/capacity values in order to trace and set attrs
        mock_decision = mock.Mock(
            return_value=(1, 1, 3, 4, 5.0, 6.0, 1, 0, "ok", "ok", 0)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace/",
                headers={
                    "traceparent": traceparent,
                    "tracestate": tracestate,
                    "x-trace-options": xtraceoptions,
                    "x-trace-options-signature": xtraceoptions_signature,
                }
            )
        resp_json = json.loads(resp.data)

        # Verify trace context injected into test app's outgoing postman-echo call
        # (added to Flask app's response data) includes:
        #    - traceparent with a trace_id, trace_flags from original request
        #    - tracestate from original request
        assert "traceparent" in resp_json
        assert trace_id in resp_json["traceparent"]
        _TRACEPARENT_HEADER_FORMAT = (
            "^[ \t]*([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})"
            + "(-.*)?[ \t]*$"
        )
        _TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)
        traceparent_re_result = re.search(
            _TRACEPARENT_HEADER_FORMAT_RE,
            resp_json["traceparent"],
        )
        new_trace_id = traceparent_re_result.group(2)
        assert new_trace_id
        assert new_trace_id == trace_id
        new_span_id = traceparent_re_result.group(3)
        assert new_span_id
        new_trace_flags = traceparent_re_result.group(4)
        assert new_trace_flags == trace_flags

        assert "tracestate" in resp_json
        assert new_span_id in resp_json["tracestate"]
        # In this test we know tracestate will have `sw`, `xtrace_options_response`,
        # `trigger-trace`, and any `ignored` KVs
        # i.e. sw=e000baa4e000baa4-01,xtrace_options_response=auth####ok;trigger-trace####ok;ignored####foo
        _TRACESTATE_HEADER_FORMAT = (
            "^[ \t]*sw=([0-9a-f]{16})-([0-9a-f]{2})"
        )
        _TRACESTATE_HEADER_FORMAT_RE = re.compile(_TRACESTATE_HEADER_FORMAT)
        tracestate_re_result = re.search(
            _TRACESTATE_HEADER_FORMAT_RE,
            resp_json["tracestate"],
        )
        new_tracestate_span = tracestate_re_result.group(1)
        assert new_tracestate_span
        assert new_tracestate_span != tracestate_span
        new_tracestate_flags = tracestate_re_result.group(2)
        assert new_tracestate_flags
        assert new_tracestate_flags == trace_flags
        assert "xtrace_options_response=auth####ok" in resp_json["tracestate"]
        assert "trigger-trace####ok" in resp_json["tracestate"]
        assert "ignored####foo" in resp_json["tracestate"]
        # TODO Change solarwinds-apm in NH-24786 to make this pass instead of above
        # assert "ignored" not in resp_json["tracestate"]

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert new_trace_id in resp.headers["x-trace"]

        # Verify x-trace-options-response response header present
        # and has same values as tracestate but different delimiters
        # i.e. auth=ok;trigger-trace=ok;ignored=foo
        assert "x-trace-options-response" in resp.headers
        assert "auth=ok" in resp.headers["x-trace-options-response"]
        assert "trigger-trace=ok" in resp.headers["x-trace-options-response"]
        assert "ignored=foo" in resp.headers["x-trace-options-response"]
        # TODO Change solarwinds-apm in NH-24786 to make this pass instead of above
        # assert "ignored" not in resp.headers["x-trace-options-response"]

        # Verify spans exported: service entry (root) + outgoing request
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        span_server = spans[1]
        span_client = spans[0]
        assert span_server.name == "/test_trace/"
        assert span_server.kind == trace_api.SpanKind.SERVER
        assert span_client.name == "HTTP GET"
        assert span_client.kind == trace_api.SpanKind.CLIENT

        # Check spans' trace_id, which should match traceparent of original request
        # Note: context.trace_id needs a 32-byte hex conversion first.
        assert "{:032x}".format(span_server.context.trace_id) == trace_id
        assert "{:032x}".format(span_client.context.trace_id) == trace_id

        # Check root span attributes
        #   :present:
        #     service entry internal KVs, which are on all entry spans
        #     sw.tracestate_parent_id, because only set if not root and no attributes
        #     SWKeys, because no xtraceoptions in otel context
        assert all(attr_key in span_server.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert span_server.attributes["BucketCapacity"] == "6.0"
        assert span_server.attributes["BucketRate"] == "5.0"
        assert span_server.attributes["SampleRate"] == 3
        assert span_server.attributes["SampleSource"] == 4
        assert "sw.tracestate_parent_id" in span_server.attributes
        assert span_server.attributes["sw.tracestate_parent_id"] == tracestate_span
        assert "SWKeys" in span_server.attributes
        # TODO Change solarwinds-apm in NH-24786 to include more
        assert span_server.attributes["SWKeys"] == "custom-sw-from:tammy,baz:qux"

        # Check outgoing request span attributes
        #   :absent:
        #     service entry internal KVs, which are only on entry spans
        #     sw.tracestate_parent_id, because cannot be set without attributes at decision
        #     SWKeys, because only on entry spans
        assert not any(attr_key in span_client.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert not "sw.tracestate_parent_id" in span_client.attributes
        assert not "SWKeys" in span_client.attributes

        # Check span_id of the outgoing request span (client span) matches
        # the span_id portion in the outgoing tracestate header, which
        # is stored in the test app's response body (new_span_id).
        # Note: context.span_id needs a 16-byte hex conversion first.
        assert "{:016x}".format(span_client.context.span_id) == new_span_id
