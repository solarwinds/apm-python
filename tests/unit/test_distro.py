import os
import pytest

from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER
)

from solarwinds_apm.distro import SolarWindsDistro

class TestDistro:
    def test_configure_no_env(self, mocker):
        mocker.patch.dict(os.environ, {})
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "solarwinds_exporter"

    def test_configure_env_exporter(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_TRACES_EXPORTER": "foobar"})
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "foobar"

    def test_configure_env_propagators(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "tracecontext,solarwinds_propagator,foobar"})
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,solarwinds_propagator,foobar"
        assert os.environ[OTEL_TRACES_EXPORTER] == "solarwinds_exporter"
