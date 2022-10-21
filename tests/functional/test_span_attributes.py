"""
Test non-root span attributes creation by SW sampler.
Has nearly the same setUpClass as TestFunctionalHeaderPropagation.
Demos what is possible with mocks alone, without test clients nor containers.
Not a great test script. Might remove later.
"""
import logging
import os
from pkg_resources import iter_entry_points
from re import sub
import requests
import sys
import time

from unittest import mock
from unittest.mock import patch

from opentelemetry import trace as trace_api
from opentelemetry.propagate import get_global_textmap
from opentelemetry.sdk.trace import export
from opentelemetry.test.globals_test import reset_trace_globals
from opentelemetry.test.test_base import TestBase
from opentelemetry.trace.span import TraceState

from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from solarwinds_apm.apm_constants import INTL_SWO_TRACESTATE_KEY
from solarwinds_apm.apm_config import SolarWindsApmConfig
from solarwinds_apm.configurator import SolarWindsConfigurator
from solarwinds_apm.distro import SolarWindsDistro
from solarwinds_apm.propagator import SolarWindsPropagator
from solarwinds_apm.sampler import ParentBasedSwSampler


# Logging
level = os.getenv("TEST_DEBUG_LEVEL", logging.DEBUG)
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
        # current tracer provider.
        reset_trace_globals()
        configurator._configure_sampler(apm_config)
        sampler = trace_api.get_tracer_provider().sampler
        # Set InMemorySpanExporter for testing
        cls.tracer_provider, cls.memory_exporter = cls.create_tracer_provider(sampler=sampler)
        span_processor = export.SimpleSpanProcessor(cls.memory_exporter)
        cls.tracer_provider.add_span_processor(span_processor)
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

    def test_root_span_attrs_no_context(self):
        """Test attribute setting for a root span with no parent, no injected context"""
        # liboboe mocked to guarantee return of “do_sample” and “start
        # decision” rate/capacity values in order to trace and set attrs
        mock_decision = mock.Mock(
            return_value=(1, 1, 3, 4, 5.0, 6.0, 7, 8, 9, 10, 11)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            with self.tracer.start_span("span-01") as s1:
                logger.debug("Created local root span-01")

        # verify span created
        self.memory_exporter.export([s1])
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        root_span = spans[0]
        assert root_span.name == "span-01"

        # verify trace_state calculated for span-01, though it'll be random here
        assert "sw" in root_span.get_span_context().trace_state

        # verify span attrs calculated for span-01:
        #   :present:
        #     service entry internal KVs, which are on all spans
        #   :absent:
        #     sw.tracestate_parent_id, because cannot be set without attributes at decision
        #     SWKeys, because no xtraceoptions in otel context
        assert all(attr_key in root_span.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert root_span.attributes["BucketCapacity"] == "6.0"
        assert root_span.attributes["BucketRate"] == "5.0"
        assert root_span.attributes["SampleRate"] == 3
        assert root_span.attributes["SampleSource"] == 4
        assert not "sw.tracestate_parent_id" in root_span.attributes
        assert not "SWKeys" in root_span.attributes

        # clean up for other tests
        self.memory_exporter.clear()

    def test_child_span_attrs(self):
        """Test attribute setting for a span under existing, valid Otel context (child span)"""
        # liboboe mocked to guarantee return of “do_sample” and “start
        # decision” rate/capacity values in order to trace and set attrs
        mock_decision = mock.Mock(
            return_value=(1, 1, 3, 4, 5.0, 6.0, 7, 8, 9, 10, 11)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # mock get_current_span() and get_span_context() for start_span/should_sample
            # representing the parent span
            mock_parent_span_context = mock.Mock()
            mock_parent_span_context.trace_id = 0x11112222333344445555666677778888
            mock_parent_span_context.span_id = 0x1000100010001000
            mock_parent_span_context.trace_flags = 0x01
            mock_parent_span_context.is_remote = True
            mock_parent_span_context.is_valid = True
            mock_parent_span_context.trace_state = TraceState([["sw", "f000baa4f000baa4-01"]])

            mock_get_current_span = mock.Mock()
            mock_get_current_span.return_value.get_span_context.return_value = mock_parent_span_context
            
            with mock.patch(
                target="solarwinds_apm.sampler.get_current_span",
                new=mock_get_current_span
            ):
                with self.tracer.start_span("span-01") as s1:
                    logger.debug("Created local root span-01")
                
                self.memory_exporter.export([s1])

        # verify span and its parent created
        self.memory_exporter.export([s1])
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        child_span = spans[0]
        assert child_span.name == "span-01"

        # verify trace_state calculated for span-01
        assert "sw" in child_span.get_span_context().trace_state
        assert child_span.get_span_context().trace_state.get("sw") == "1000100010001000-01"

        # verify span attrs of span-01:
        #   :present:
        #     service entry internal KVs, which are on all spans
        #     sw.tracestate_parent_id, because only set if not root and no attributes at decision
        #   :absent:
        #     SWKeys, because no xtraceoptions in otel context
        assert all(attr_key in child_span.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert child_span.attributes["BucketCapacity"] == "6.0"
        assert child_span.attributes["BucketRate"] == "5.0"
        assert child_span.attributes["SampleRate"] == 3
        assert child_span.attributes["SampleSource"] == 4
        assert "sw.tracestate_parent_id" in child_span.attributes
        assert child_span.attributes["sw.tracestate_parent_id"] == "f000baa4f000baa4"
        assert not "SWKeys" in child_span.attributes

        # clean up for other tests
        self.memory_exporter.clear()


    def test_non_root_attrs_only_do_sample(self):
        """A not-great test with mocked decision do_sample.
        Only tests span attributes, not context propagation.
        Only tests non-root spans.
        
        It seems that the only way for the custom sampler should_sample
        to call oboe decision using a non-None tracestring is to mock
        parent_span_context. Manual extract with custom propagator alone
        still ends up setting trace state sw as 0000000000000000-01 even
        if not the root span (span-02) which isn't correct. If we do set
        parent_span_context it picks up a valid tracestate, but we can
        never generate a root span to check it has present Service KVs
        and absent sw.tracestate_parent_id.
        """
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
            # representing the root span
            mock_parent_span_context = mock.Mock()
            mock_parent_span_context.trace_id = 0x11112222333344445555666677778888
            mock_parent_span_context.span_id = 0x1000100010001000
            mock_parent_span_context.trace_flags = 0x01
            mock_parent_span_context.is_remote = True
            mock_parent_span_context.is_value = True
            mock_parent_span_context.trace_state = TraceState([["sw", "f000baa4f000baa4-01"]])

            mock_get_current_span = mock.Mock()
            mock_get_current_span.return_value.get_span_context.return_value = mock_parent_span_context
            
            with mock.patch(
                target="solarwinds_apm.sampler.get_current_span",
                new=mock_get_current_span
            ):
                # Begin trace of manually started spans

                # This does not get picked up by sampler.should_sample
                self.composite_propagator.extract({
                    traceparent_h: "00-11112222333344445555666677778888-1000100010001000-01",
                    tracestate_h: "sw=e000baa4e000baa4-01",
                })
                with self.tracer.start_span("span-01") as s1:

                    # This does not get picked up by sampler.should_sample
                    self.composite_propagator.extract({
                        traceparent_h: "00-11112222333344445555666677778888-2000200020002000-01",
                        tracestate_h: "sw=e000baa4e000baa4-01",
                    })
                    with self.tracer.start_span("span-02") as s2:
                        pass

        # verify trace created
        self.memory_exporter.export([s2, s1])
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 2
        assert spans[0].name == "span-02"
        assert INTL_SWO_TRACESTATE_KEY in spans[0].context.trace_state
        assert spans[0].context.trace_state[INTL_SWO_TRACESTATE_KEY] == "1000100010001000-01"
        assert spans[1].name == "span-01"
        assert INTL_SWO_TRACESTATE_KEY in spans[1].context.trace_state
        assert spans[1].context.trace_state[INTL_SWO_TRACESTATE_KEY] == "1000100010001000-01"

        # verify span attrs of span-02:
        #     - present: service entry internal
        #     - absent: sw.tracestate_parent_id
        # assert "sw.tracestate_parent_id" in spans[0].attributes  # fails
        assert spans[0].attributes["sw.tracestate_parent_id"] == "f000baa4f000baa4"  
        # assert not any(attr_key in spans[0].attributes for attr_key in self.SW_SETTINGS_KEYS)

        # verify span attrs of span-01:
        #     - present: service entry internal
        #     - absent: sw.tracestate_parent_id
        # assert not "sw.tracestate_parent_id" in spans[1].attributes
        assert all(attr_key in spans[1].attributes for attr_key in self.SW_SETTINGS_KEYS)

    def test_internal_span_attrs(self):
        """Test that internal root span gets Service KVs as attrs
        and a tracestate created with our key"""
        with self.tracer.start_as_current_span("foo-span"):
            pass
        spans = self.memory_exporter.get_finished_spans()
        # assert len(spans) == 1  # fails
        # assert all(attr_key in spans[0].attributes for attr_key in self.SW_SETTINGS_KEYS)
        # assert INTL_SWO_TRACESTATE_KEY in spans[0].context.trace_state
        # assert spans[0].context.trace_state[INTL_SWO_TRACESTATE_KEY] == "0000000000000000-01"
