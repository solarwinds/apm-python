"""
Instruments test app with SolarWinds APM to test propagation and trace.
Exports spans to InMemorySpanExporter.

Mocks:
  - liboboe getDecisions, to guarantee sampling and rate/capacity values
  - exporter, as InMemorySpanExporter.
Real:
  - requests
  - liboboe init
  - SW propagator
  - SW sampler
  - SW response propagator
"""
import json
import logging
import os
from pkg_resources import iter_entry_points
from re import sub
import requests
import sys
import time

from flask import Flask, request
import pytest
from unittest import mock
from unittest.mock import patch

from opentelemetry import trace as trace_api
from opentelemetry.propagate import get_global_textmap
from opentelemetry.test.globals_test import reset_trace_globals
from opentelemetry.test.test_base import TestBase

from opentelemetry.instrumentation.flask import FlaskInstrumentor
# from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from tests.propagation_test_app import PropagationTest
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


class TestScenario04(PropagationTest, TestBase):

    @classmethod
    def setUpClass(self):
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
        self.tracer_provider, self.memory_exporter = self.create_tracer_provider(sampler=sampler)
        trace_api.set_tracer_provider(self.tracer_provider)
        self.tracer = self.tracer_provider.get_tracer(__name__)

        # Load and instrument OTel Python library
        # so any `requests` should have headers
        RequestsInstrumentor().instrument()
        # HTTPXClientInstrumentor().instrument()

        # Set up test app
        self._app_init(self)
        FlaskInstrumentor().instrument_app(
            app=self.app,
            tracer_provider=self.tracer_provider
        )

        # Make sure SW SDK components were set
        propagators = get_global_textmap()._propagators
        assert len(propagators) == 3
        assert isinstance(propagators[2], SolarWindsPropagator)
        assert isinstance(trace_api.get_tracer_provider().sampler, ParentBasedSwSampler)

        self.composite_propagator = get_global_textmap()
        self.tc_propagator = self.composite_propagator._propagators[0]
        self.sw_propagator = self.composite_propagator._propagators[2]
        self.traceparent_h = self.tc_propagator._TRACEPARENT_HEADER_NAME
        self.tracestate_h = self.sw_propagator._TRACESTATE_HEADER_NAME
        self.response_h = "x-trace"

        # Wake-up request and wait for oboe_init
        with self.tracer.start_as_current_span("wakeup_span"):
            r = requests.get(f"http://solarwinds.com")
            logger.debug("Wake-up request with headers: {}".format(r.headers))
            time.sleep(2)
        
    @classmethod
    def tearDownClass(self):
        FlaskInstrumentor().uninstrument_app(self.app)

    def test_attrs_with_valid_traceparent_sw_in_tracestate_do_sample(self):
        """Acceptance Criterion #4, decision do_sample"""
        FlaskInstrumentor().instrument()
        resp = None
        # liboboe mocked to guarantee return of “do_sample” and “start
        # decision” rate/capacity values
        mock_decision = mock.Mock(
            return_value=(1, 1, 3, 4, 5.0, 6.0, 7, 8, 9, 10, 11)
        )
        with patch(
            target="solarwinds_apm.extension.oboe.Context.getDecisions",
            new=mock_decision,
        ):
            # Request to instrumented app with headers
            resp = self.client.get(
                "/test_trace",
                headers={
                    self.traceparent_h: "00-11112222333344445555666677778888-000100010001000-01",
                    self.tracestate_h: "sw=1111111111111111-01",
                }
            )

        # TODO verify correct trace context was injected in outbound call
        # Need a place to store the headers that test app sent to postman-echo
        resp_json = json.loads(resp.data)
        assert self.traceparent_h in resp_json
        # assert "11112222333344445555666677778888" in resp_json[self.traceparent_h]
        
        # TODO verify correct trace context was injected in response
        assert self.response_h in resp.headers
        # assert "11112222333344445555666677778888" in resp.headers[self.response_h]

        # TODO verify SW trace created
        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        assert SW_TRACESTATE_KEY in spans[0].context.trace_state
        # assert spans[0].context.trace_state[SW_TRACESTATE_KEY] == "000100010001000-01"
        
        # TODO verify span attrs:
        #   - present: sw.tracestate_parent_id
        #   - absent: service entry internal
        # assert "sw.tracestate_parent_id" in spans[0].attributes
        # assert not any(attr_key in spans[0].attributes for attr_key in self.SW_SETTINGS_KEYS)

        FlaskInstrumentor().uninstrument()
        
    def test_attrs_with_valid_traceparent_sw_in_tracestate_not_do_sample(self):
        """Acceptance Criterion #4, decision not do_sample"""
        pass