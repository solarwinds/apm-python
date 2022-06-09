import os

from solarwinds_apm import apm_config
from solarwinds_apm import (
    DEFAULT_SW_PROPAGATORS,
    DEFAULT_SW_TRACES_EXPORTER,
)

class TestSolarWindsApmConfig:

    def test_calculate_agent_enabled_ok_defaults(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": ",".join(DEFAULT_SW_PROPAGATORS),
            "OTEL_TRACES_EXPORTER": DEFAULT_SW_TRACES_EXPORTER,
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_points = mocker.MagicMock()
        mock_points.__iter__.return_value = ["foo"]
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )
        assert apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_ok_explicit(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "foo,tracecontext,bar,solarwinds_propagator",
            "OTEL_TRACES_EXPORTER": "foo",
            "SW_APM_SERVICE_KEY": "valid:key",
            "SW_APM_AGENT_ENABLED": "true",
        })
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_points = mocker.MagicMock()
        mock_points.__iter__.return_value = ["foo"]
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )
        assert apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_no_sw_propagator(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "tracecontext,baggage",
            "OTEL_TRACES_EXPORTER": DEFAULT_SW_TRACES_EXPORTER,
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_no_tracecontext_propagator(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "solarwinds_propagator",
            "OTEL_TRACES_EXPORTER": DEFAULT_SW_TRACES_EXPORTER,
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_sw_before_tracecontext_propagator(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "solarwinds_propagator,tracecontext",
            "OTEL_TRACES_EXPORTER": DEFAULT_SW_TRACES_EXPORTER,
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_no_such_exporter(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": ",".join(DEFAULT_SW_PROPAGATORS),
            "OTEL_TRACES_EXPORTER": "not-valid",
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            side_effect=StopIteration("mock error")
        )
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_set_false(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "foo,tracecontext,bar,solarwinds_propagator",
            "OTEL_TRACES_EXPORTER": "foo",
            "SW_APM_SERVICE_KEY": "valid:key",
            "SW_APM_AGENT_ENABLED": "false",
        })
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_points = mocker.MagicMock()
        mock_points.__iter__.return_value = ["foo"]
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_service_key_missing(self, mocker):
        # Save any service key in os for later
        old_service_key = os.environ.get("SW_APM_SERVICE_KEY", None)
        del os.environ["SW_APM_SERVICE_KEY"]
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "foo,tracecontext,bar,solarwinds_propagator",
            "OTEL_TRACES_EXPORTER": "foo",
            "SW_APM_AGENT_ENABLED": "true",
        })
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_points = mocker.MagicMock()
        mock_points.__iter__.return_value = ["foo"]
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()
        # Restore that service key
        os.environ["SW_APM_SERVICE_KEY"] = old_service_key

    def test_calculate_agent_enabled_service_key_bad_format(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "foo,tracecontext,bar,solarwinds_propagator",
            "OTEL_TRACES_EXPORTER": "foo",
            "SW_APM_SERVICE_KEY": "invalidkey",
            "SW_APM_AGENT_ENABLED": "true",
        })
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_points = mocker.MagicMock()
        mock_points.__iter__.return_value = ["foo"]
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()
