import os
import pytest

from opentelemetry.environment_variables import (
    OTEL_PROPAGATORS,
    OTEL_TRACES_EXPORTER
)

from solarwinds_apm.distro import SolarWindsDistro

class TestDistro:
    def test_init(self, mocker):
        distro = SolarWindsDistro()
        assert distro._TRACECONTEXT_PROPAGATOR == "tracecontext"
        assert distro._SW_PROPAGATOR == "solarwinds_propagator"
        assert distro._DEFAULT_SW_PROPAGATORS == [
            "tracecontext",
            "baggage",
            "solarwinds_propagator",
        ]

    def test_configure_no_env(self, mocker):
        mocker.patch.dict(os.environ, {})
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "solarwinds_exporter"

    def test_configure_env_exporter_ok(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_TRACES_EXPORTER": "foobar"})
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,baggage,solarwinds_propagator"
        assert os.environ[OTEL_TRACES_EXPORTER] == "foobar"

    def test_configure_env_without_sw_propagator_fails(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "tracecontext,baggage"})
        with pytest.raises(ValueError):
            SolarWindsDistro()._configure()

    def test_configure_env_without_tracecontext_propagator_fails(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "solarwinds_propagator"})
        with pytest.raises(ValueError):
            SolarWindsDistro()._configure()

    def test_configure_env_sw_before_tracecontext_propagator_fails(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "solarwinds_propagator,tracecontext"})
        with pytest.raises(ValueError):
            SolarWindsDistro()._configure()

    def test_configure_env_propagators_ok(self, mocker):
        mocker.patch.dict(os.environ, {"OTEL_PROPAGATORS": "tracecontext,solarwinds_propagator,foobar"})
        SolarWindsDistro()._configure()
        assert os.environ[OTEL_PROPAGATORS] == "tracecontext,solarwinds_propagator,foobar"
        assert os.environ[OTEL_TRACES_EXPORTER] == "solarwinds_exporter"
