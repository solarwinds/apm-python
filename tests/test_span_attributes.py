"""
Test root span attributes creation by SW sampler with liboboe, before export.

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
from unittest.mock import patch

from opentelemetry import trace as trace_api
from opentelemetry.propagate import get_global_textmap
from opentelemetry.test.globals_test import reset_trace_globals
from opentelemetry.test.test_base import TestBase
from opentelemetry.trace.span import SpanContext

from solarwinds_apm import SW_TRACESTATE_KEY
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
        trace_api.set_tracer_provider(cls.tracer_provider)
        cls.tracer = cls.tracer_provider.get_tracer(__name__)

        # Make sure SW SDK components were set
        propagators = get_global_textmap()._propagators
        assert len(propagators) == 3
        assert isinstance(propagators[2], SolarWindsPropagator)
        assert isinstance(trace_api.get_tracer_provider().sampler, ParentBasedSwSampler)

        # Wake-up request and wait for oboe_init
        with cls.tracer.start_as_current_span("wakeup_span"):
            requests.get(f"http://solarwinds.com")
            time.sleep(2)
        
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # TODO: anything else?

    def test_attrs_no_input_headers(self):
        """Acceptance Criterion #1"""
        with self.tracer.start_as_current_span("attrs_no_input_headers"):
            pass
        spans = self.memory_exporter.get_finished_spans()
        # assert len(spans) == 1
        # assert all(attr_key in spans[0].attributes for attr_key in self.SW_SETTINGS_KEYS)
        # assert SW_TRACESTATE_KEY in spans[0].context.trace_state
        # assert spans[0].context.trace_state[SW_TRACESTATE_KEY] == "0000000000000000-01"

    def test_attrs_with_valid_traceparent(self):
        """Acceptance Criterion #2"""
        pass

    def test_attrs_with_no_traceparent_nonempty_tracestate(self):
        """Acceptance Criterion #3"""
        pass

    def test_attrs_with_valid_traceparent_sw_in_tracestate(self):
        """Acceptance Criterion #4"""
        pass

    def test_attrs_with_valid_traceparent_nonempty_tracestate(self):
        """Acceptance Criterion #5"""
        pass

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

    # TODO: trigger trace scenarios
