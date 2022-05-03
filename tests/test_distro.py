import os
import pytest

from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER
)

from solarwinds_apm.distro import SolarWindsDistro


# We can mock these, but they aren't used by distro because setup.py
# is called before tox-triggered tests run

# otel_propagators = "foo"
# otel_traces_exporter = "bar"
# otel_traces_sampler = "baz"
# @pytest.fixture(autouse=True)
# def fixture_env_and_otel_keys(mocker):
#     # mocker.patch.dict("os.environ", {})
#     mocker.patch.object(opentelemetry.environment_variables, "OTEL_PROPAGATORS", otel_propagators)
#     mocker.patch.object(opentelemetry.sdk.environment_variables, "OTEL_TRACES_SAMPLER", otel_traces_sampler)
#     mocker.patch.object(opentelemetry.environment_variables, "OTEL_TRACES_EXPORTER", otel_traces_exporter)

class TestDistro:
    def test_configure_no_env(self):
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "solarwinds_exporter"

    # TODO After merging https://github.com/appoptics/opentelemetry-python-instrumentation-custom-distro/pull/14/files
    def test_configure_env_without_sw_propagator_fails(self):
        pass

    def test_configure_env_without_tracecontext_propagator_fails(self):
        pass

    def test_configure_env_sw_before_tracecontext_propagator_fails(self):
        pass

    def test_configure_env_with_external_propagator(self):
        pass
