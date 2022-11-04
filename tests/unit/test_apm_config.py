import json
import os
import pytest

from solarwinds_apm import apm_config
from solarwinds_apm.apm_constants import (
    INTL_SWO_AO_COLLECTOR,
    INTL_SWO_AO_STG_COLLECTOR,
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
    """
    Note: _calculate_agent_enabled sets defaults for OTEL_PROPAGATORS
    and OTEL_TRACES_EXPORTER. SW_APM_SERVICE_KEY is required.
    SW_APM_AGENT_ENABLED is optional.
    """

    def _mock_service_key(self, mocker, service_key):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": service_key,
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
            "OTEL_TRACES_EXPORTER": "solarwinds_exporter,foo",
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
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_no_tracecontext_propagator(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "solarwinds_propagator",
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_sw_before_tracecontext_propagator(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_PROPAGATORS": "solarwinds_propagator,tracecontext",
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_valid_other_but_missing_sw_exporter(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_TRACES_EXPORTER": "foo",
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
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_sw_but_no_such_other_exporter(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_TRACES_EXPORTER": "solarwinds_exporter,not-valid",
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            side_effect=StopIteration("mock error")
        )
        assert not apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_sw_and_two_other_valid_exporters(self, mocker):
        mocker.patch.dict(os.environ, {
            "OTEL_TRACES_EXPORTER": "foo,solarwinds_exporter,bar",
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_points = mocker.MagicMock()
        mock_points.__iter__.return_value = ["foo", "bar"]
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )
        assert apm_config.SolarWindsApmConfig()._calculate_agent_enabled()

    def test_calculate_agent_enabled_set_false(self, mocker):
        mocker.patch.dict(os.environ, {
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

    def test_calculate_metric_format_no_collector(self, mocker):
        # Save any collector in os for later
        old_collector = os.environ.get("SW_APM_COLLECTOR", None)
        if old_collector:
            del os.environ["SW_APM_COLLECTOR"]
        assert apm_config.SolarWindsApmConfig()._calculate_metric_format() == 0
        # Restore old collector
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector

    def test_calculate_metric_format_not_ao(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": "foo-collector-not-ao"
        })
        assert apm_config.SolarWindsApmConfig()._calculate_metric_format() == 0

    def test_calculate_metric_format_ao_prod(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": INTL_SWO_AO_COLLECTOR
        })
        assert apm_config.SolarWindsApmConfig()._calculate_metric_format() == 1

    def test_calculate_metric_format_ao_staging(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": INTL_SWO_AO_STG_COLLECTOR
        })
        assert apm_config.SolarWindsApmConfig()._calculate_metric_format() == 1

    def test_calculate_metric_format_ao_prod_with_port(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": "{}:123".format(INTL_SWO_AO_COLLECTOR)
        })
        assert apm_config.SolarWindsApmConfig()._calculate_metric_format() == 1

    def test_calculate_certificates_no_collector(self):
        # Save any collector in os for later
        old_collector = os.environ.get("SW_APM_COLLECTOR", None)
        if old_collector:
            del os.environ["SW_APM_COLLECTOR"]
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == ""
        # Restore old collector
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector

    def test_calculate_certificates_not_ao(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": "foo-collector-not-ao"
        })
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == ""

    def test_calculate_certificates_ao_prod_no_trustedpath(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": INTL_SWO_AO_COLLECTOR
        })
        mock_get_public_cert = mocker.patch(
            "solarwinds_apm.apm_config.get_public_cert"
        )
        mock_get_public_cert.configure_mock(return_value="foo")
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == "foo"

    def test_calculate_certificates_ao_staging_no_trustedpath(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": INTL_SWO_AO_STG_COLLECTOR
        })
        mock_get_public_cert = mocker.patch(
            "solarwinds_apm.apm_config.get_public_cert"
        )
        mock_get_public_cert.configure_mock(return_value="foo")
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == "foo"

    def test_calculate_certificates_ao_prod_with_port_no_trustedpath(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": "{}:123".format(INTL_SWO_AO_COLLECTOR)
        })
        mock_get_public_cert = mocker.patch(
            "solarwinds_apm.apm_config.get_public_cert"
        )
        mock_get_public_cert.configure_mock(return_value="foo")
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == "foo"

    def test_calculate_certificates_ao_prod_trustedpath_file_missing(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": INTL_SWO_AO_COLLECTOR,
            "SW_APM_TRUSTEDPATH": "/no/file/here"
        })
        mock_read_text = mocker.Mock()
        mock_read_text.side_effect = FileNotFoundError("no file there")
        mock_pathlib_path = mocker.Mock()
        mock_pathlib_path.configure_mock(
            **{
                "read_text": mock_read_text
            }
        )
        mocker.patch("solarwinds_apm.apm_config.Path").configure_mock(return_value=mock_pathlib_path)
        mock_get_public_cert = mocker.patch(
            "solarwinds_apm.apm_config.get_public_cert"
        )
        mock_get_public_cert.configure_mock(return_value="foo")
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == "foo"

    def test_calculate_certificates_ao_prod_trustedpath_file_present(self, mocker):
        """Note: if file exists, same behaviour if file contains valid cert or not"""
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": INTL_SWO_AO_COLLECTOR,
            "SW_APM_TRUSTEDPATH": "/there/is/a/file/here"
        })
        mock_read_text = mocker.Mock()
        mock_read_text.configure_mock(return_value="bar")
        mock_pathlib_path = mocker.Mock()
        mock_pathlib_path.configure_mock(
            **{
                "read_text": mock_read_text
            }
        )
        mocker.patch("solarwinds_apm.apm_config.Path").configure_mock(return_value=mock_pathlib_path)
        mock_get_public_cert = mocker.patch(
            "solarwinds_apm.apm_config.get_public_cert"
        )
        mock_get_public_cert.configure_mock(return_value="foo")
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == "bar"

    def test_mask_service_key_no_key_empty_default(self, mocker):
        old_service_key = os.environ.get("SW_APM_SERVICE_KEY", None)
        if old_service_key:
            del os.environ["SW_APM_SERVICE_KEY"]
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_points = mocker.MagicMock()
        mock_points.__iter__.return_value = ["foo"]
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )
        assert apm_config.SolarWindsApmConfig().mask_service_key() == ""
        # Restore that service key
        if old_service_key:
            os.environ["SW_APM_SERVICE_KEY"] = old_service_key

    def test_mask_service_key_empty_key(self, mocker):
        self._mock_service_key(mocker, "")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == ""

    def test_mask_service_key_whitespace_key(self, mocker):
        self._mock_service_key(mocker, " ")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == " "

    def test_mask_service_key_invalid_format_no_colon(self, mocker):
        self._mock_service_key(mocker, "a")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "a<invalid_format>"
        self._mock_service_key(mocker, "abcd")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcd<invalid_format>"
        self._mock_service_key(mocker, "abcde")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcd...<invalid_format>"
        self._mock_service_key(mocker, "abcdefgh")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcd...<invalid_format>"
        self._mock_service_key(mocker, "abcd1efgh")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcd...<invalid_format>"
        self._mock_service_key(mocker, "CyUuit1W--8RVmUXX6_cVjTWemaUyBh1ruL0nMPiFdrPo1iiRnO31_pwiUCPzdzv9UMHK6I")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "CyUu...<invalid_format>"

    def test_mask_service_key_less_than_9_char_token(self, mocker):
        self._mock_service_key(mocker, ":foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == ":foo-bar"
        self._mock_service_key(mocker, "a:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "a:foo-bar"
        self._mock_service_key(mocker, "ab:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "ab:foo-bar"
        self._mock_service_key(mocker, "abc:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abc:foo-bar"
        self._mock_service_key(mocker, "abcd:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcd:foo-bar"
        self._mock_service_key(mocker, "abcde:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcde:foo-bar"
        self._mock_service_key(mocker, "abcdef:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcdef:foo-bar"
        self._mock_service_key(mocker, "abcdefg:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcdefg:foo-bar"
        self._mock_service_key(mocker, "abcdefgh:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcdefgh:foo-bar"

    def test_mask_service_key_9_or_more_char_token(self, mocker):
        self._mock_service_key(mocker, "abcd1efgh:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcd...efgh:foo-bar"
        self._mock_service_key(mocker, "abcd12efgh:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcd...efgh:foo-bar"
        self._mock_service_key(mocker, "abcd123efgh:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcd...efgh:foo-bar"
        self._mock_service_key(mocker, "abcd1234567890efgh:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "abcd...efgh:foo-bar"
        self._mock_service_key(mocker, "CyUuit1W--8RVmUXX6_cVjTWemaUyBh1ruL0nMPiFdrPo1iiRnO31_pwiUCPzdzv9UMHK6I:foo-bar")
        assert apm_config.SolarWindsApmConfig().mask_service_key() == "CyUu...HK6I:foo-bar"

    def test_config_mask_service_key(self, mocker):
        self._mock_service_key(mocker, "valid-and-long:key")
        assert apm_config.SolarWindsApmConfig()._config_mask_service_key().get("service_key") == "vali...long:key"

    def test_str(self, mocker):
        self._mock_service_key(mocker, "valid-and-long:key")
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
        # Save any debug_level in os for later
        old_debug_level = os.environ.get("SW_APM_DEBUG_LEVEL", None)
        if old_debug_level:
            del os.environ["SW_APM_DEBUG_LEVEL"]
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("debug_level", "not-valid-level")
        assert test_config.get("debug_level") == 2
        assert "Ignore config option" in caplog.text
        # Restore old debug_level
        if old_debug_level:
            os.environ["SW_APM_DEBUG_LEVEL"] = old_debug_level

    # pylint:disable=unused-argument
    def test_set_config_value_default_log_trace_id(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("log_trace_id", "not-valid-mode")
        assert test_config.get("log_trace_id") == "never"
        assert "Ignore config option" in caplog.text
