"""
Test span attributes calculation by SW sampler.
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

    def test_root_span_attrs(self):
        """Test attribute setting for a root span with no parent"""
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

    def test_root_span_attrs_with_traceparent_and_tracestate(self):
        """Test attribute setting for a root span with no parent,
        but OTel context has valid traceparent and sw-containing tracestate"""
        # Need to explicitly extract and give to tracer so sampler receives these
        extracted_context = self.composite_propagator.extract({
            "traceparent": "00-11112222333344445555666677778888-1000100010001000-01",
            "tracestate": "sw=e000baa4e000baa4-01",
        })

        # liboboe mocked to guarantee return of “do_sample” and “start
        # decision” rate/capacity values
        mock_decision = mock.Mock(
            return_value=(1, 1, 3, 4, 5.0, 6.0, 7, 8, 9, 10, 11)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            with self.tracer.start_span(name="span-01", context=extracted_context) as s1:
                logger.debug("Created local root span-01")

        # verify span created
        self.memory_exporter.export([s1])
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        root_span = spans[0]
        assert root_span.name == "span-01"

        # verify trace_state calculated for span-01
        assert "sw" in root_span.get_span_context().trace_state
        assert root_span.get_span_context().trace_state.get("sw") == "1000100010001000-01"

        # verify span attrs calculated for span-01:
        #   :present:
        #     service entry internal KVs, which are on all spans
        #     sw.tracestate_parent_id, because only set if not root and no attributes at 
        #   :absent:
        #     SWKeys, because no xtraceoptions in otel context
        assert all(attr_key in root_span.attributes for attr_key in self.SW_SETTINGS_KEYS)
        assert root_span.attributes["BucketCapacity"] == "6.0"
        assert root_span.attributes["BucketRate"] == "5.0"
        assert root_span.attributes["SampleRate"] == 3
        assert root_span.attributes["SampleSource"] == 4
        assert "sw.tracestate_parent_id" in root_span.attributes
        assert root_span.attributes["sw.tracestate_parent_id"] == "e000baa4e000baa4"
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
                    logger.debug("Created local child span-01")
                
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
