import json
import os
import pytest

from solarwinds_apm import apm_config
from solarwinds_apm.apm_constants import (
    INTL_SWO_DEFAULT_PROPAGATORS,
    INTL_SWO_DEFAULT_TRACES_EXPORTER,
)

@pytest.fixture(name="mock_env_vars")
def fixture_mock_env_vars(mocker):
    mocker.patch.dict(os.environ, {
        "OTEL_PROPAGATORS": ",".join(INTL_SWO_DEFAULT_PROPAGATORS),
        "OTEL_TRACES_EXPORTER": INTL_SWO_DEFAULT_TRACES_EXPORTER,
        "SW_APM_SERVICE_KEY": "valid:key",
    })


class TestSolarWindsApmConfig:

    def _mock_with_service_key(self, mocker, service_key):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": ",".join(INTL_SWO_DEFAULT_PROPAGATORS),
            "OTEL_TRACES_EXPORTER": INTL_SWO_DEFAULT_TRACES_EXPORTER,"SW_APM_SERVICE_KEY": service_key,
        })
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_points = mocker.MagicMock()
        mock_points.__iter__.return_value = ["foo"]
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )

    def test_calculate_agent_enabled_ok_defaults(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": ",".join(INTL_SWO_DEFAULT_PROPAGATORS),
            "OTEL_TRACES_EXPORTER": INTL_SWO_DEFAULT_TRACES_EXPORTER,
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
            "OTEL_TRACES_EXPORTER": INTL_SWO_DEFAULT_TRACES_EXPORTER,
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_no_tracecontext_propagator(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "solarwinds_propagator",
            "OTEL_TRACES_EXPORTER": INTL_SWO_DEFAULT_TRACES_EXPORTER,
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_sw_before_tracecontext_propagator(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "solarwinds_propagator,tracecontext",
            "OTEL_TRACES_EXPORTER": INTL_SWO_DEFAULT_TRACES_EXPORTER,
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_no_such_exporter(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": ",".join(INTL_SWO_DEFAULT_PROPAGATORS),
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
        if old_service_key:
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
        if old_service_key:
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

    def test_mask_service_key_no_key_empty_default(self, mocker):
        old_service_key = os.environ.get("SW_APM_SERVICE_KEY", None)
        if old_service_key:
            del os.environ["SW_APM_SERVICE_KEY"]
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": ",".join(INTL_SWO_DEFAULT_PROPAGATORS),
            "OTEL_TRACES_EXPORTER": INTL_SWO_DEFAULT_TRACES_EXPORTER,
        })
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_points = mocker.MagicMock()
        mock_points.__iter__.return_value = ["foo"]
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == ""
        # Restore that service key
        if old_service_key:
            os.environ["SW_APM_SERVICE_KEY"] = old_service_key

    def test_mask_service_key_empty_key(self, mocker):
        self._mock_with_service_key(mocker, "")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == ""

    def test_mask_service_key_whitespace_key(self, mocker):
        self._mock_with_service_key(mocker, " ")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == " "

    def test_mask_service_key_invalid_format_no_colon(self, mocker):
        self._mock_with_service_key(mocker, "a")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "a<invalid_format>"
        self._mock_with_service_key(mocker, "abcd")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcd<invalid_format>"
        self._mock_with_service_key(mocker, "abcde")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcd...<invalid_format>"
        self._mock_with_service_key(mocker, "abcdefgh")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcd...<invalid_format>"
        self._mock_with_service_key(mocker, "abcd1efgh")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcd...<invalid_format>"
        self._mock_with_service_key(mocker, "CyUuit1W--8RVmUXX6_cVjTWemaUyBh1ruL0nMPiFdrPo1iiRnO31_pwiUCPzdzv9UMHK6I")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "CyUu...<invalid_format>"

    def test_mask_service_key_less_than_9_char_token(self, mocker):
        self._mock_with_service_key(mocker, ":foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == ":foo-bar"
        self._mock_with_service_key(mocker, "a:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "a:foo-bar"
        self._mock_with_service_key(mocker, "ab:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "ab:foo-bar"
        self._mock_with_service_key(mocker, "abc:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abc:foo-bar"
        self._mock_with_service_key(mocker, "abcd:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcd:foo-bar"
        self._mock_with_service_key(mocker, "abcde:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcde:foo-bar"
        self._mock_with_service_key(mocker, "abcdef:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcdef:foo-bar"
        self._mock_with_service_key(mocker, "abcdefg:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcdefg:foo-bar"
        self._mock_with_service_key(mocker, "abcdefgh:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcdefgh:foo-bar"

    def test_mask_service_key_9_or_more_char_token(self, mocker):
        self._mock_with_service_key(mocker, "abcd1efgh:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcd...efgh:foo-bar"
        self._mock_with_service_key(mocker, "abcd12efgh:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcd...efgh:foo-bar"
        self._mock_with_service_key(mocker, "abcd123efgh:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcd...efgh:foo-bar"
        self._mock_with_service_key(mocker, "abcd1234567890efgh:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "abcd...efgh:foo-bar"
        self._mock_with_service_key(mocker, "CyUuit1W--8RVmUXX6_cVjTWemaUyBh1ruL0nMPiFdrPo1iiRnO31_pwiUCPzdzv9UMHK6I:foo-bar")
        assert apm_config.SolarWindsApmConfig()._mask_service_key() == "CyUu...HK6I:foo-bar"

    def test_config_mask_service_key(self, mocker):
        self._mock_with_service_key(mocker, "valid-and-long:key")
        assert apm_config.SolarWindsApmConfig()._config_mask_service_key().get("service_key") == "vali...long:key"

    def test_str(self, mocker):
        self._mock_with_service_key(mocker, "valid-and-long:key")
        result = str(apm_config.SolarWindsApmConfig())
        assert "vali...long:key" in result
        assert "agent_enabled" in result
        assert "solarwinds_apm.extension.oboe.Context" in result

    # pylint:disable=unused-argument
    def test_set_config_value_invalid_key(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("invalid_key", "foo")
        assert test_config.get("invalid_key", None) == None
        assert "Ignore invalid configuration key" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_ec2(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("ec2_metadata_timeout", "9999")
        assert test_config.get("ec2_metadata_timeout") == 1000
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_token_cap(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("token_bucket_capacity", "9999")
        assert test_config.get("token_bucket_capacity") == -1
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_token_rate(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("token_bucket_rate", "9999")
        assert test_config.get("token_bucket_rate") == -1
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_proxy(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("proxy", "not-valid-url")
        assert test_config.get("proxy") == ""
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_tracing_mode(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("tracing_mode", "not-valid-mode")
        assert test_config.get("tracing_mode") == None
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_trigger_trace(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("trigger_trace", "not-valid-mode")
        assert test_config.get("trigger_trace") == "enabled"
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_reporter(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("reporter", "not-valid-mode")
        assert test_config.get("reporter") == ""
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_debug_level(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("debug_level", "not-valid-level")
        assert test_config.get("debug_level") == 2
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_log_trace_id(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("log_trace_id", "not-valid-mode")
        assert test_config.get("log_trace_id") == "never"
        assert "Ignore config option" in caplog.text
