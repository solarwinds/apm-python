"""
Test root span attributes creation by SW sampler with liboboe, before export.
Currently a big mess and more of a sandbox!

See also: https://swicloud.atlassian.net/wiki/spaces/NIT/pages/2325479753/W3C+Trace+Context#Acceptance-Criteria
"""
import logging
import os
from pkg_resources import iter_entry_points
from re import sub
import requests
import sys
import time

import pytest
from unittest import mock
from unittest.mock import patch

from opentelemetry import trace as trace_api
from opentelemetry.context import Context as OtelContext
from opentelemetry.propagate import get_global_textmap
from opentelemetry.test.globals_test import reset_trace_globals
from opentelemetry.test.test_base import TestBase
from opentelemetry.trace import get_current_span
from opentelemetry.trace.span import SpanContext, TraceState

from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from solarwinds_apm import SW_TRACESTATE_KEY
from solarwinds_apm.configurator import SolarWindsConfigurator
from solarwinds_apm.distro import SolarWindsDistro
from solarwinds_apm.propagator import SolarWindsPropagator
from solarwinds_apm.sampler import ParentBasedSwSampler


# Logging
level = os.getenv("PYTHON_DEBUG_LEVEL", logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(level)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(level)
formatter = logging.Formatter('%(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class TestFunctionalSpanAttributesAllSpans(TestBase):

    SW_SETTINGS_KEYS = [
        "BucketCapacity",
        "BucketRate",
        "SampleRate",
        "SampleSource"
    ]

    @classmethod
    def setUpClass(cls):
        # Based on auto_instrumentation run() and sitecustomize.py
        # Load OTel env vars entry points
        argument_otel_environment_variable = {}
        for entry_point in iter_entry_points(
            "opentelemetry_environment_variables"
        ):
            environment_variable_module = entry_point.load()
            for attribute in dir(environment_variable_module):
                if attribute.startswith("OTEL_"):
                    argument = sub(r"OTEL_(PYTHON_)?", "", attribute).lower()
                    argument_otel_environment_variable[argument] = attribute

        # Load Distro
        SolarWindsDistro().configure()
        assert os.environ["OTEL_PROPAGATORS"] == "tracecontext,baggage,solarwinds_propagator"

        # Load Configurator to Configure SW custom SDK components
        # except use TestBase InMemorySpanExporter
        configurator = SolarWindsConfigurator()
        configurator._initialize_solarwinds_reporter()
        configurator._configure_propagator()
        configurator._configure_response_propagator()
        # This is done because set_tracer_provider cannot override the
        # current tracer provider.
        reset_trace_globals()
        configurator._configure_sampler()
        sampler = trace_api.get_tracer_provider().sampler
        # Set InMemorySpanExporter for testing
        cls.tracer_provider, cls.memory_exporter = cls.create_tracer_provider(sampler=sampler)
        trace_api.set_tracer_provider(cls.tracer_provider)
        cls.tracer = cls.tracer_provider.get_tracer(__name__)

        # Make sure SW SDK components were set
        propagators = get_global_textmap()._propagators
        assert len(propagators) == 3
        assert isinstance(propagators[2], SolarWindsPropagator)
        assert isinstance(trace_api.get_tracer_provider().sampler, ParentBasedSwSampler)

        cls.composite_propagator = get_global_textmap()
        cls.tc_propagator = cls.composite_propagator._propagators[0]
        cls.sw_propagator = cls.composite_propagator._propagators[2]

        # So we can make requests and check headers
        # Real requests (at least for now) with OTel Python instrumentation libraries
        cls.httpx_inst = HTTPXClientInstrumentor()
        cls.httpx_inst.instrument()
        cls.requests_inst = RequestsInstrumentor()
        cls.requests_inst.instrument()

        # Wake-up request and wait for oboe_init
        with cls.tracer.start_as_current_span("wakeup_span"):
            r = requests.get(f"http://solarwinds.com")
            logger.debug("Wake-up request with headers: {}".format(r.headers))
            time.sleep(2)
        
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.httpx_inst.uninstrument()
        cls.requests_inst.uninstrument()

    def test_attrs_no_input_headers(self):
        """Acceptance Criterion #1"""
        pass

    def test_attrs_with_valid_traceparent_sw_in_tracestate_do_sample(self):
        """Acceptance Criterion #4, decision do_sample"""
        resp = None
        traceparent_h = self.tc_propagator._TRACEPARENT_HEADER_NAME
        tracestate_h = self.sw_propagator._TRACESTATE_HEADER_NAME

        # liboboe mocked to guarantee return of “do_sample” and “start
        # decision” rate/capacity values
        mock_decision = mock.Mock(
            return_value=(1, 1, 3, 4, 5.0, 6.0, 7, 8, 9, 10, 11)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):

            # mock get_current_span() and get_span_context() for start_span/should_sample
            mock_parent_span_context = mock.Mock()
            mock_parent_span_context.trace_id = 0x11112222333344445555666677778888
            mock_parent_span_context.span_id = 0x1111aaaa2222bbbb
            mock_parent_span_context.trace_flags = 0x01
            mock_parent_span_context.is_remote = True
            mock_parent_span_context.is_value = True
            mock_parent_span_context.trace_state = TraceState([["sw", "1111aaaa2222bbbb-01"]])

            mock_get_current_span = mock.Mock()
            mock_get_current_span.return_value.get_span_context.return_value = mock_parent_span_context
            
            with mock.patch(
                target="solarwinds_apm.sampler.get_current_span",
                new=mock_get_current_span
            ):

                # extract valid inbound trace context with our vendor tracestate info
                self.composite_propagator.extract({
                    traceparent_h: "00-11112222333344445555666677778888-1111aaaa2222bbbb-01",
                    tracestate_h: "sw=1111aaaa2222bbbb-01",
                })
                
                # - traced process makes an outbound RPC
                with self.tracer.start_span("foo-span") as foo_span:
                    # make call to postman-echo to get request headers from
                    # response, though not necessary
                    # Note: this isn't NH instrumented
                    resp = requests.get(f"http://postman-echo.com/headers")

        # verify correct trace context was injected in outbound call
        assert traceparent_h in resp.request.headers
        assert tracestate_h in resp.request.headers
        # assert resp.request.headers[traceparent_h] == "foo"  # !!!
        # assert resp.request.headers[tracestate_h] == "foo"  # !!!

        # verify trace created
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert SW_TRACESTATE_KEY in spans[0].context.trace_state
        assert spans[0].context.trace_state[SW_TRACESTATE_KEY] == "1111aaaa2222bbbb-01"

        # verify span attrs:
        #   - present: sw.tracestate_parent_id
        #   - absent: service entry internal
        assert "sw.tracestate_parent_id" in spans[0].attributes
        # assert not any(attr_key in spans[0].attributes for attr_key in self.SW_SETTINGS_KEYS)  # !!!

        # TODO verify correct trace context was injected in response header ?!?!?!

    def test_attrs_with_valid_traceparent_sw_in_tracestate_not_do_sample(self):
        """Acceptance Criterion #4, decision not do_sample"""
        pass

    def test_attrs_with_no_traceparent_valid_unsigned_tt(self):
        """Acceptance Criterion #6"""
        pass


    # Next phase ====================================================

    def test_attrs_with_valid_traceparent_sampled(self):
        """Acceptance Criterion #2, sampled"""
        pass

    def test_attrs_with_valid_traceparent_not_sampled(self):
        """Acceptance Criterion #2, not sampled"""
        pass

    def test_attrs_with_no_traceparent_nonempty_tracestate(self):
        """Acceptance Criterion #3"""
        pass

    def test_attrs_with_valid_traceparent_nonempty_tracestate(self):
        """Acceptance Criterion #5"""
        pass

    # TODO: more trigger trace scenarios

    def test_attrs_with_invalid_traceparent(self):
        """traceparent should be ignored"""
        pass

    def test_attrs_with_valid_traceparent_invalid_tracestate(self):
        """tracestate should be ignored"""
        pass

    def test_attrs_with_valid_traceparent_more_than_32_entries_traceparent(self):
        """tracestate should be truncated"""
        pass

    def test_attrs_with_valid_traceparent_more_than_512_bytes_traceparent(self):
        """tracestate is still valid"""
        pass

    # Attempts at other things ======================================

    def test_internal_span_attrs(self):
        """Test that internal root span gets Service KVs as attrs
        and a tracestate created with our key"""
        with self.tracer.start_as_current_span("foo-span"):
            pass
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert all(attr_key in spans[0].attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert SW_TRACESTATE_KEY in spans[0].context.trace_state
        assert spans[0].context.trace_state[SW_TRACESTATE_KEY] == "0000000000000000-01"

    def test_attempt_to_give_custom_sampler_specific_parent_span_context(self):
        """Trying to start_as_current_span with values so custom sampler
        receives a valid parent_span_context, but not working"""

        # How to 'mock' a SpanContext
        parent_span_context = get_current_span(
            self.composite_propagator.extract({
                self.tc_propagator._TRACEPARENT_HEADER_NAME: "00-11112222333344445555666677778888-1111aaaa2222bbbb-01",
                self.sw_propagator._TRACESTATE_HEADER_NAME: "sw=1111aaaa2222bbbb-01",
                "is_remote": True,
            })
        ).get_span_context()
        
        # SpanContext(trace_id=0x11112222333344445555666677778888, span_id=0x1111aaaa2222bbbb, trace_flags=0x01, trace_state=['{key=sw, value=1111aaaa2222bbbb-01}'], is_remote=True)
        logger.debug("parent_span_context: {}".format(parent_span_context))
        
        # How to 'mock' OTel context with 'propagator-extracted' values
        otel_context = OtelContext({
            "trace_id": 0x11112222333344445555666677778888,
            "span_id": 0x1111aaaa2222bbbb,
            "trace_flags": 0x01,
            "is_remote": True,
            "trace_state": ['{key=sw, value=1111aaaa2222bbbb-01}'],
        })
        # otel_context = OtelContext({
        #     self.tc_propagator._TRACEPARENT_HEADER_NAME: "00-11112222333344445555666677778888-1111aaaa2222bbbb-01",
        #     self.sw_propagator._TRACESTATE_HEADER_NAME: "sw=1111aaaa2222bbbb-01",
        #     "is_remote": True,
        #     "parent_span_context": parent_span_context,
        # })

        logger.debug("otel_context: {}".format(otel_context))

        # with self.tracer.start_span(
        with self.tracer.start_as_current_span(
            name="foo-span",
            context=otel_context,
        ) as foo_span:
            # pass
            with self.tracer.start_as_current_span(
                name="span-with-parent",
                context=otel_context
            ):
                pass

        spans = self.memory_exporter.get_finished_spans()
        # assert len(spans) == 1
        logger.debug("to_json(): {}".format(spans[0].to_json()))
        # SpanContext(trace_id=0xf985a1c01cc33423f98e397f26937f8e, span_id=0xee898212f6db4304, trace_flags=0x01, trace_state=['{key=sw, value=0000000000000000-01}'], is_remote=False)
        logger.debug("span_context: {}".format(spans[0].context))

        # logger.debug("to_json(): {}".format(spans[1].to_json()))
        # logger.debug("span_context: {}".format(spans[1].context))

        assert all(attr_key in spans[0].attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert SW_TRACESTATE_KEY in spans[0].context.trace_state
        
        # assert spans[0].context.trace_state[SW_TRACESTATE_KEY] == "1111aaaa2222bbbb-01"  # AssertionError: assert '0000000000000000-01' == '1111aaaa2222bbbb-01'
        # assert spans[1].context.trace_state[SW_TRACESTATE_KEY] == "1111aaaa2222bbbb-01"
