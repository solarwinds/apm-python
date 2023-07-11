# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import pytest

from opentelemetry.sdk.resources import Resource

from solarwinds_apm import apm_config
from solarwinds_apm.apm_constants import (
    INTL_SWO_AO_COLLECTOR,
    INTL_SWO_AO_STG_COLLECTOR,
)

# pylint: disable=unused-import
from .fixtures.env_vars import fixture_mock_env_vars

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

    def test__init_invalid_service_key_format(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "incorrect_format",
        })
        test_config = apm_config.SolarWindsApmConfig()
        assert not test_config.agent_enabled
        assert test_config.service_name == ""
        assert test_config.get("service_key") == "incorrect_format"

    def test__init_invalid_service_key_format_otel_service_name_and_resource_attrs(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "incorrect_format",
            "OTEL_SERVICE_NAME": "wont_be_used",
            "OTEL_RESOURCE_ATTRIBUTES": "service.name=also_unused"
        })
        test_config = apm_config.SolarWindsApmConfig()
        assert not test_config.agent_enabled
        assert test_config.service_name == ""
        assert test_config.get("service_key") == "incorrect_format"

    def test__init_valid_service_key_format_agent_enabled_false(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "SW_APM_AGENT_ENABLED": "false",
        })
        test_config = apm_config.SolarWindsApmConfig()
        assert not test_config.agent_enabled
        assert test_config.service_name == ""
        assert test_config.get("service_key") == "service_key_with:sw_service_name"

    def test__init_valid_service_key_format_agent_enabled_true_default(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
        })
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.agent_enabled
        assert test_config.service_name == "sw_service_name"
        assert test_config.get("service_key") == "service_key_with:sw_service_name"

    def test__init_valid_service_key_format_agent_enabled_true_explicit(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "SW_APM_AGENT_ENABLED": "true",
        })
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.agent_enabled
        assert test_config.service_name == "sw_service_name"
        assert test_config.get("service_key") == "service_key_with:sw_service_name"

    def test__init_valid_service_key_format_otel_service_name(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "OTEL_SERVICE_NAME": "from_otel_env"
        })
        # Otel picks up os mock if Resource.create here (same as default arg)
        test_config = apm_config.SolarWindsApmConfig(Resource.create())
        assert test_config.agent_enabled
        assert test_config.service_name == "from_otel_env"
        assert test_config.get("service_key") == "service_key_with:from_otel_env"

    def test__init_valid_service_key_format_otel_service_name_and_resource_attrs(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "OTEL_SERVICE_NAME": "from_otel_env",
            "OTEL_RESOURCE_ATTRIBUTES": "service.name=also_from_otel_env_unused"
        })
        # Otel picks up os mock if Resource.create here (same as default arg)
        test_config = apm_config.SolarWindsApmConfig(Resource.create())
        assert test_config.agent_enabled
        assert test_config.service_name == "from_otel_env"
        assert test_config.get("service_key") == "service_key_with:from_otel_env"

    def test__init_valid_service_key_format_otel_resource_attrs(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "OTEL_RESOURCE_ATTRIBUTES": "service.name=also_from_otel_env_used_this_time"
        })
        # Otel picks up os mock if Resource.create here (same as default arg)
        test_config = apm_config.SolarWindsApmConfig(Resource.create())
        assert test_config.agent_enabled
        assert test_config.service_name == "also_from_otel_env_used_this_time"
        assert test_config.get("service_key") == "service_key_with:also_from_otel_env_used_this_time"

    def test__init_valid_service_key_format_empty_otel_service_name(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "OTEL_SERVICE_NAME": "",
        })
        # Otel picks up os mock if Resource.create here (same as default arg)
        test_config = apm_config.SolarWindsApmConfig(Resource.create())
        assert test_config.agent_enabled
        assert test_config.service_name == "sw_service_name"
        assert test_config.get("service_key") == "service_key_with:sw_service_name"

    def test__init_valid_service_key_format_empty_otel_service_name_and_resource_attrs(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "OTEL_SERVICE_NAME": "",
            "OTEL_RESOURCE_ATTRIBUTES": "",
        })
        # Otel picks up os mock if Resource.create here (same as default arg)
        test_config = apm_config.SolarWindsApmConfig(Resource.create())
        assert test_config.agent_enabled
        assert test_config.service_name == "sw_service_name"
        assert test_config.get("service_key") == "service_key_with:sw_service_name"

    def test__init_valid_service_key_format_otel_resource_attrs_without_name(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "OTEL_RESOURCE_ATTRIBUTES": "foo=bar,telemetry.sdk.version=whatever-i-want-baby",
        })
        # Otel picks up os mock if Resource.create here (same as default arg)
        test_config = apm_config.SolarWindsApmConfig(Resource.create())
        assert test_config.agent_enabled
        assert test_config.service_name == "sw_service_name"
        assert test_config.get("service_key") == "service_key_with:sw_service_name"

    def test_calculate_metric_format_no_collector(self, mocker):
        # Save any collector in os for later
        old_collector = os.environ.get("SW_APM_COLLECTOR", None)
        if old_collector:
            del os.environ["SW_APM_COLLECTOR"]
        assert apm_config.SolarWindsApmConfig()._calculate_metric_format() == 2
        # Restore old collector
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector

    def test_calculate_metric_format_not_ao(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": "foo-collector-not-ao"
        })
        assert apm_config.SolarWindsApmConfig()._calculate_metric_format() == 2

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
        # Save any collector and trustedpath in os for later
        old_collector = os.environ.get("SW_APM_COLLECTOR", None)
        if old_collector:
            del os.environ["SW_APM_COLLECTOR"]
        old_trustedpath = os.environ.get("SW_APM_TRUSTEDPATH", None)
        if old_trustedpath:
            del os.environ["SW_APM_TRUSTEDPATH"]
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == ""
        # Restore old collector and trustedpath
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector
        if old_trustedpath:
            os.environ["SW_APM_TRUSTEDPATH"] = old_trustedpath

    def test_calculate_certificates_not_ao(self, mocker):
        # Save any trustedpath in os for later
        old_trustedpath = os.environ.get("SW_APM_TRUSTEDPATH", None)
        if old_trustedpath:
            del os.environ["SW_APM_TRUSTEDPATH"]
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": "foo-collector-not-ao"
        })
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == ""
        # Restore old trustedpath
        if old_trustedpath:
            os.environ["SW_APM_TRUSTEDPATH"] = old_trustedpath

    def test_calculate_certificates_ao_prod_no_trustedpath(self, mocker):
        # Save any trustedpath in os for later
        old_trustedpath = os.environ.get("SW_APM_TRUSTEDPATH", None)
        if old_trustedpath:
            del os.environ["SW_APM_TRUSTEDPATH"]
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": INTL_SWO_AO_COLLECTOR
        })
        mock_get_public_cert = mocker.patch(
            "solarwinds_apm.apm_config.get_public_cert"
        )
        mock_get_public_cert.configure_mock(return_value="foo")
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == "foo"
        # Restore old trustedpath
        if old_trustedpath:
            os.environ["SW_APM_TRUSTEDPATH"] = old_trustedpath

    def test_calculate_certificates_ao_staging_no_trustedpath(self, mocker):
        # Save any trustedpath in os for later
        old_trustedpath = os.environ.get("SW_APM_TRUSTEDPATH", None)
        if old_trustedpath:
            del os.environ["SW_APM_TRUSTEDPATH"]
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": INTL_SWO_AO_STG_COLLECTOR
        })
        mock_get_public_cert = mocker.patch(
            "solarwinds_apm.apm_config.get_public_cert"
        )
        mock_get_public_cert.configure_mock(return_value="foo")
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == "foo"
        # Restore old trustedpath
        if old_trustedpath:
            os.environ["SW_APM_TRUSTEDPATH"] = old_trustedpath

    def test_calculate_certificates_ao_prod_with_port_no_trustedpath(self, mocker):
        # Save any trustedpath in os for later
        old_trustedpath = os.environ.get("SW_APM_TRUSTEDPATH", None)
        if old_trustedpath:
            del os.environ["SW_APM_TRUSTEDPATH"]
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": "{}:123".format(INTL_SWO_AO_COLLECTOR)
        })
        mock_get_public_cert = mocker.patch(
            "solarwinds_apm.apm_config.get_public_cert"
        )
        mock_get_public_cert.configure_mock(return_value="foo")
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == "foo"
        # Restore old trustedpath
        if old_trustedpath:
            os.environ["SW_APM_TRUSTEDPATH"] = old_trustedpath

    def test_calculate_certificates_not_ao_trustedpath_file_missing(self, mocker):
        """Non-AO collector, trustedpath set, but file missing --> use empty string"""
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": "foo-collector-not-ao",
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
        assert apm_config.SolarWindsApmConfig()._calculate_certificates() == ""

    def test_calculate_certificates_ao_prod_trustedpath_file_missing(self, mocker):
        """AO collector, trustedpath set, but file missing --> use bundled cert"""
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

    def test_calculate_certificates_not_ao_trustedpath_file_present(self, mocker):
        """Note: if file exists, same behaviour if file contains valid cert or not"""
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": "foo-collector-not-ao",
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
        assert test_config.get("invalid_key", None) is None
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
        assert test_config.get("tracing_mode") == -1
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_trigger_trace(self, caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("trigger_trace", "not-valid-mode")
        assert test_config.get("trigger_trace") == 1
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

    def test__calculate_service_name_agent_disabled(self):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name(
            False,
            {}
        )
        assert result == ""

    def test__calculate_service_name_no_otel_service_name(
        self,
        mocker,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
        })
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name(
            True,
            Resource.create({"service.name": None})
        )
        assert result == "sw_service_name"

    def test__calculate_service_name_default_unknown_otel_service_name(
        self,
        mocker,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
        })
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name(
            True,
            # default is unknown_service
            Resource.create()
        )
        assert result == "sw_service_name"

    def test__calculate_service_name_use_otel_service_name(
        self,
        mocker,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
        })
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._calculate_service_name(
            True,
            Resource.create({"service.name": "foobar"})
        )
        assert result == "foobar"

    def test__update_service_key_name_not_agent_enabled(self):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._update_service_key_name(
            False,
            "foo",
            "bar"
        )
        assert result == "foo"

    def test__update_service_key_name_empty_service_name(self):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._update_service_key_name(
            True,
            "foo",
            ""
        )
        assert result == "foo"

    def test__update_service_key_name_not_agent_enabled_and_empty_service_name(self):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._update_service_key_name(
            False,
            "foo",
            ""
        )
        assert result == "foo"

    def test__update_service_key_name_agent_enabled_and_service_name_ok(self):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._update_service_key_name(
            True,
            "valid_key_with:foo-service",
            "bar-service"
        )
        assert result == "valid_key_with:bar-service"

    def test__convert_to_bool_bool_true(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config._convert_to_bool(True)

    def test__convert_to_bool_bool_false(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert not test_config._convert_to_bool(False)

    def test__convert_to_bool_int(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config._convert_to_bool(0) is None

    def test__convert_to_bool_str_invalid(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config._convert_to_bool("not-true-nor-false") is None

    def test__convert_to_bool_str_true(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config._convert_to_bool("true")

    def test__convert_to_bool_str_true_mixed_case(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config._convert_to_bool("tRuE")

    def test__convert_to_bool_str_false(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert not test_config._convert_to_bool("false")

    def test__convert_to_bool_str_false_mixed_case(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert not test_config._convert_to_bool("fAlSE")
