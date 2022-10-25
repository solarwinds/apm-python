"""
Tests propagator header injection by SW propagator given different incoming headers
"""
import json
import logging
import os
from pkg_resources import iter_entry_points
import re
import requests
import sys
import time

from flask import Flask, request
import pytest
from unittest import mock
from unittest.mock import patch

from opentelemetry import trace as trace_api
from opentelemetry.propagate import get_global_textmap
from opentelemetry.sdk.trace import export
from opentelemetry.test.globals_test import reset_trace_globals
from opentelemetry.test.test_base import TestBase

from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from functional.propagation_test_app import PropagationTest
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


class TestHeaderPropagation(PropagationTest, TestBase):

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

        # Set up test app
        cls._app_init(cls)
        FlaskInstrumentor().instrument_app(
            app=cls.app,
            tracer_provider=cls.tracer_provider
        )
        
    @classmethod
    def tearDownClass(cls):
        FlaskInstrumentor().uninstrument_app(cls.app)

    def helper_existing_traceparent_tracestate(self, trace_flags, do_sample) -> None:
        """Helper for similar tests with different trace_flags, do_sample decision"""
        trace_id = "11112222333344445555666677778888"
        span_id = "1000100010001000"
        traceparent = "00-{}-{}-{}".format(trace_id, span_id, trace_flags)
        tracestate = "sw=e000baa4e000baa4-{}".format(trace_flags)
        resp = None

        # liboboe mocked to guarantee return of "do_sample" and "start
        # decision" rate/capacity values in order to trace and set attrs
        mock_decision = mock.Mock(
            return_value=(1, do_sample, 3, 4, 5.0, 6.0, 7, 8, 9, 10, 11)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app
            resp = self.client.get(
                "/test_trace",
                headers={
                    "traceparent": traceparent,
                    "tracestate": tracestate,
                }
            )
        resp_json = json.loads(resp.data)
       
        # Verify Flask app's response data (trace context injected to its 
        # outgoing postman echo call) includes:
        #    - traceparent with same trace_id and trace_flags, new span_id
        #    - tracestate with same trace_flags, new span_id
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
        new_span_id = traceparent_re_result.group(3)
        assert span_id not in resp_json["traceparent"]
        assert new_span_id in resp_json["traceparent"]
        assert trace_flags == traceparent_re_result.group(4)

        assert "tracestate" in resp_json
        assert span_id not in resp_json["tracestate"]
        assert new_span_id in resp_json["tracestate"]
        # In this test we know there is only `sw` in tracestate
        # i.e. sw=e000baa4e000baa4-01
        _TRACESTATE_HEADER_FORMAT = (
            "^[ \t]*sw=([0-9a-f]{16})-([0-9a-f]{2})"
            + "(-.*)?[ \t]*$"
        )
        _TRACESTATE_HEADER_FORMAT_RE = re.compile(_TRACESTATE_HEADER_FORMAT)
        tracestate_re_result = re.search(
            _TRACESTATE_HEADER_FORMAT_RE,
            resp_json["tracestate"],
        )
        assert trace_flags == tracestate_re_result.group(2)

        # Verify x-trace response header has same trace_id
        # though it will have different span ID because of Flask
        # app's outgoing request
        assert "x-trace" in resp.headers
        assert trace_id in resp.headers["x-trace"]

    def test_injection_new_decision(self):
        """Test that some traceparent and tracestate are injected
        when a new decision to do_sample is made"""
        pass

    def test_injection_with_existing_traceparent_tracestate(self):
        """Test that the provided traceparent and tracestate are injected
        to continue the existing decision to sample"""
        self.helper_existing_traceparent_tracestate("01", 1)
        
    def test_injection_with_existing_traceparent_tracestate_not_sampled(self):
        """Test that the provided traceparent and tracestate are injected
        to continue the existing decision to NOT sample"""
        self.helper_existing_traceparent_tracestate("00", 0)

    def test_injection_signed_tt(self):
        """Test that successful signed trigger trace results in injection
        of x-trace-options-response"""
        pass