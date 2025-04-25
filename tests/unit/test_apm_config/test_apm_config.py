# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import os
import re

import pytest

from opentelemetry.sdk.resources import Resource

from solarwinds_apm import apm_config
from solarwinds_apm.oboe.configuration import Configuration, TransactionSetting

# pylint: disable=unused-import
from .fixtures.env_vars import fixture_mock_env_vars

@pytest.fixture
def setup_caplog():
    apm_logger = logging.getLogger("solarwinds_apm")
    apm_logger.propagate = True


class TestSolarWindsApmConfig:
    """
    Note: mock_env_vars test fixture sets values for OTEL_PROPAGATORS
    and OTEL_TRACES_EXPORTER. SW_APM_SERVICE_KEY is required.
    SW_APM_AGENT_ENABLED is optional.
    """

    @pytest.fixture(autouse=True)
    def before_and_after_each(self):
        # Save any env vars for later just in case
        old_service_key = os.environ.get("SW_APM_SERVICE_KEY", None)
        if old_service_key:
            del os.environ["SW_APM_SERVICE_KEY"]
        old_env_lambda_name = os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        if old_env_lambda_name:
            del os.environ["AWS_LAMBDA_FUNCTION_NAME"]
        old_env_trans_name = os.environ.get("SW_APM_TRANSACTION_NAME")
        if old_env_trans_name:
            del os.environ["SW_APM_TRANSACTION_NAME"]
        old_debug_level = os.environ.get("SW_APM_DEBUG_LEVEL")
        if old_debug_level:
            del os.environ["SW_APM_DEBUG_LEVEL"]
        old_collector = os.environ.get("SW_APM_COLLECTOR", None)
        if old_collector:
            del os.environ["SW_APM_COLLECTOR"]
        old_trustedpath = os.environ.get("SW_APM_TRUSTEDPATH", None)
        if old_trustedpath:
            del os.environ["SW_APM_TRUSTEDPATH"]
        old_expt_logs = os.environ.get("SW_APM_EXPORT_LOGS_ENABLED", None)
        if old_expt_logs:
            del os.environ["SW_APM_EXPORT_LOGS_ENABLED"]
        old_expt_metrics = os.environ.get("SW_APM_EXPORT_METRICS_ENABLED", None)
        if old_expt_metrics:
            del os.environ["SW_APM_EXPORT_METRICS_ENABLED"]

        # Wait for test
        yield

        # Restore old env vars
        if old_service_key:
            os.environ["SW_APM_SERVICE_KEY"] = old_service_key
        if old_env_lambda_name:
            os.environ["AWS_LAMBDA_FUNCTION_NAME"] = old_env_lambda_name
        if old_env_trans_name:
            os.environ["SW_APM_TRANSACTION_NAME"] = old_env_trans_name
        if old_debug_level:
            os.environ["SW_APM_DEBUG_LEVEL"] = old_debug_level
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector
        if old_trustedpath:
            os.environ["SW_APM_TRUSTEDPATH"] = old_trustedpath
        if old_expt_logs:
            os.environ["SW_APM_EXPORT_LOGS_ENABLED"] = old_expt_logs
        if old_expt_metrics:
            os.environ["SW_APM_EXPORT_METRICS_ENABLED"] = old_expt_metrics

    def test__default_collector(self, mocker):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.get("collector") == apm_config.SolarWindsApmConfig._CONFIG_COLLECTOR_DEFAULT

    def test__init_collector(self, mocker):
        mocker.patch.dict(os.environ, {
            "SW_APM_COLLECTOR": "apm.collector.eu-02.cloud.solarwinds.com"
        })
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.get("collector") == "apm.collector.eu-02.cloud.solarwinds.com"

    def _mock_service_key(self, mocker, service_key):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": service_key,
        })

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

    def test__init_valid_service_key_format_agent_enabled_true_default(
        self,
        mocker,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
        })
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.agent_enabled
        assert test_config.service_name == "sw_service_name"
        assert test_config.get("service_key") == "service_key_with:sw_service_name"

    def test__init_valid_service_key_format_agent_enabled_true_explicit(
        self,
        mocker,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "SW_APM_AGENT_ENABLED": "true",
        })
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.agent_enabled
        assert test_config.service_name == "sw_service_name"
        assert test_config.get("service_key") == "service_key_with:sw_service_name"

    def test__init_valid_service_key_format_otel_service_name(
        self,
        mocker,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "OTEL_SERVICE_NAME": "from_otel_env"
        })
        # Otel picks up os mock if Resource.create here (same as default arg)
        test_config = apm_config.SolarWindsApmConfig(Resource.create())
        assert test_config.agent_enabled
        assert test_config.service_name == "from_otel_env"
        assert test_config.get("service_key") == "service_key_with:from_otel_env"

    def test__init_valid_service_key_format_otel_service_name_and_resource_attrs(
        self,
        mocker,
        mock_env_vars,
    ):
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

    def test__init_valid_service_key_format_otel_resource_attrs(
        self,
        mocker,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "OTEL_RESOURCE_ATTRIBUTES": "service.name=also_from_otel_env_used_this_time"
        })
        # Otel picks up os mock if Resource.create here (same as default arg)
        test_config = apm_config.SolarWindsApmConfig(Resource.create())
        assert test_config.agent_enabled
        assert test_config.service_name == "also_from_otel_env_used_this_time"
        assert test_config.get("service_key") == "service_key_with:also_from_otel_env_used_this_time"

    def test__init_valid_service_key_format_empty_otel_service_name(
        self,
        mocker,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "OTEL_SERVICE_NAME": "",
        })
        # Otel picks up os mock if Resource.create here (same as default arg)
        test_config = apm_config.SolarWindsApmConfig(Resource.create())
        assert test_config.agent_enabled
        assert test_config.service_name == "sw_service_name"
        assert test_config.get("service_key") == "service_key_with:sw_service_name"

    def test__init_valid_service_key_format_empty_otel_service_name_and_resource_attrs(
        self,
        mocker,
        mock_env_vars,
    ):
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

    def test__init_valid_service_key_format_otel_resource_attrs_without_name(
        self,
        mocker,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "service_key_with:sw_service_name",
            "OTEL_RESOURCE_ATTRIBUTES": "foo=bar,telemetry.sdk.version=whatever-i-want-baby",
        })
        # Otel picks up os mock if Resource.create here (same as default arg)
        test_config = apm_config.SolarWindsApmConfig(Resource.create())
        assert test_config.agent_enabled
        assert test_config.service_name == "sw_service_name"
        assert test_config.get("service_key") == "service_key_with:sw_service_name"

    def test__init_custom_transction_names_env_vars(self, mocker):
        mocker.patch.dict(
            os.environ,
            {
                "AWS_LAMBDA_FUNCTION_NAME": "foo-lambda",
                "SW_APM_TRANSACTION_NAME": "foo-trans-name",
            },
        )

        config = apm_config.SolarWindsApmConfig()
        assert config.lambda_function_name == "foo-lambda"
        assert config.get("transaction_name") == "foo-trans-name"

    def test_mask_service_key_no_key_empty_default(self, mocker):
        assert apm_config.SolarWindsApmConfig().mask_service_key() == ""

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

    def test_mask_service_key_less_than_9_char_token(
        self,
        mocker,
        mock_env_vars,
    ):
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

    def test_mask_service_key_9_or_more_char_token(
        self,
        mocker,
        mock_env_vars,
    ):
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

    def test_config_mask_service_key(
        self,
        mocker,
        mock_env_vars,
    ):
        self._mock_service_key(mocker, "valid-and-long:key")
        assert apm_config.SolarWindsApmConfig()._config_mask_service_key().get("service_key") == "vali...long:key"

    def test_str(
        self,
        mocker,
        mock_env_vars,
    ):
        self._mock_service_key(mocker, "valid-and-long:key")
        result = str(apm_config.SolarWindsApmConfig())
        assert "vali...long:key" in result
        assert "agent_enabled" in result
        # assert "solarwinds_apm.extension.oboe.Context" in result

    # pylint:disable=unused-argument
    def test_set_config_value_invalid_key(self, caplog, setup_caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("invalid_key", "foo")
        assert test_config.get("invalid_key", None) is None
        assert "Ignore invalid configuration key" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_tracing_mode(self, caplog, setup_caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("tracing_mode", "not-valid-mode")
        assert test_config.get("tracing_mode") == -1
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_trigger_trace(self, caplog, setup_caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("trigger_trace", "not-valid-mode")
        assert test_config.get("trigger_trace") == 1
        assert "Ignore config option" in caplog.text

    # pylint:disable=unused-argument
    def test_set_config_value_default_debug_level(self, caplog, setup_caplog, mock_env_vars):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("debug_level", "not-valid-level")
        assert test_config.get("debug_level") == 2
        assert "Ignore config option" in caplog.text

    def test_set_config_value_default_export_logs_enabled(
        self,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.get("export_logs_enabled") == False

    def test_set_config_value_ignore_export_logs_enabled(
        self,
        caplog,
        setup_caplog,
        mock_env_vars,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("export_logs_enabled", "not-valid")
        assert test_config.get("export_logs_enabled") == False
        assert "Ignore config option" in caplog.text
    def test_set_config_value_set_export_logs_enabled_false(
        self,
        caplog,
        setup_caplog,
        mock_env_vars,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("export_logs_enabled", "false")
        assert test_config.get("export_logs_enabled") == False
        assert "Ignore config option" not in caplog.text

    def test_set_config_value_set_export_logs_enabled_false_mixed_case(
        self,
        caplog,
        setup_caplog,
        mock_env_vars,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("export_logs_enabled", "fALsE")
        assert test_config.get("export_logs_enabled") == False
        assert "Ignore config option" not in caplog.text

    def test_set_config_value_set_export_logs_enabled_true(
        self,
        caplog,
        setup_caplog,
        mock_env_vars,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("export_logs_enabled", "true")
        assert test_config.get("export_logs_enabled") == True
        assert "Ignore config option" not in caplog.text

    def test_set_config_value_set_export_logs_enabled_true_mixed_case(
        self,
        caplog,
        setup_caplog,
        mock_env_vars,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("export_logs_enabled", "tRUe")
        assert test_config.get("export_logs_enabled") == True
        assert "Ignore config option" not in caplog.text

    def test_set_config_value_default_export_metrics_enabled(
        self,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.get("export_metrics_enabled") == True

    def test_set_config_value_ignore_export_metrics_enabled(
        self,
        caplog,
        setup_caplog,
        mock_env_vars,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("export_metrics_enabled", "not-valid")
        assert test_config.get("export_metrics_enabled") == True
        assert "Ignore config option" in caplog.text
    def test_set_config_value_set_export_metrics_enabled_false(
        self,
        caplog,
        setup_caplog,
        mock_env_vars,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("export_metrics_enabled", "false")
        assert test_config.get("export_metrics_enabled") == False
        assert "Ignore config option" not in caplog.text

    def test_set_config_value_set_export_metrics_enabled_false_mixed_case(
        self,
        caplog,
        setup_caplog,
        mock_env_vars,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("export_metrics_enabled", "fALsE")
        assert test_config.get("export_metrics_enabled") == False
        assert "Ignore config option" not in caplog.text

    def test_set_config_value_set_export_metrics_enabled_true(
        self,
        caplog,
        setup_caplog,
        mock_env_vars,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("export_metrics_enabled", "true")
        assert test_config.get("export_metrics_enabled") == True
        assert "Ignore config option" not in caplog.text

    def test_set_config_value_set_export_metrics_enabled_true_mixed_case(
        self,
        caplog,
        setup_caplog,
        mock_env_vars,
    ):
        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("export_metrics_enabled", "tRUe")
        assert test_config.get("export_metrics_enabled") == True
        assert "Ignore config option" not in caplog.text

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

    def test__update_service_key_name_agent_enabled_and_service_name_ok_but_service_key_missing(self):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._update_service_key_name(
            True,
            None,
            "bar-service"
        )
        assert result is None

    def test__update_service_key_name_agent_enabled_and_service_name_ok_but_service_key_empty(self):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._update_service_key_name(
            True,
            "",
            "bar-service"
        )
        assert result == ""

    def test__update_service_key_name_agent_enabled_and_service_name_ok_but_service_key_no_delimiter(self):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._update_service_key_name(
            True,
            "weird-key-no-delimiter",
            "bar-service"
        )
        assert result == "weird-key-no-delimiter"

    def test__update_service_key_name_agent_enabled_and_service_name_ok_service_key_multiple_delimiter(self):
        test_config = apm_config.SolarWindsApmConfig()
        result = test_config._update_service_key_name(
            True,
            "weird-key:with:2-delimiters",
            "bar-service"
        )
        # Updates everything after first delim
        assert result == "weird-key:bar-service"

    def test__validate_log_filepath_none(self, mocker):
        mock_exists = mocker.patch("solarwinds_apm.apm_config.os.path.exists")
        mock_makedirs = mocker.patch("solarwinds_apm.apm_config.os.makedirs")

        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("log_filepath", "")
        test_config._validate_log_filepath()
        mock_exists.assert_not_called()
        mock_makedirs.assert_not_called()
        assert test_config.get("log_filepath") == ""

    def test__validate_log_filepath_no_parent_path(self, mocker):
        mock_exists = mocker.patch("solarwinds_apm.apm_config.os.path.exists")
        mock_makedirs = mocker.patch("solarwinds_apm.apm_config.os.makedirs")

        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("log_filepath", "foo")
        test_config._validate_log_filepath()
        mock_exists.assert_not_called()
        mock_makedirs.assert_not_called()
        assert test_config.get("log_filepath") == "foo"

    def test__validate_log_filepath_path_exists(self, mocker):
        mock_exists = mocker.patch("solarwinds_apm.apm_config.os.path.exists", return_value=True)
        mock_makedirs = mocker.patch("solarwinds_apm.apm_config.os.makedirs")

        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("log_filepath", "/path/to/foo")
        test_config._validate_log_filepath()
        mock_exists.assert_called_once_with("/path/to")
        mock_makedirs.assert_not_called()
        assert test_config.get("log_filepath") == "/path/to/foo"

    def test__validate_log_filepath_create_path(self, mocker):
        mock_exists = mocker.patch("solarwinds_apm.apm_config.os.path.exists", return_value=False)
        mock_makedirs = mocker.patch("solarwinds_apm.apm_config.os.makedirs")

        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("log_filepath", "/path/to/foo")
        test_config._validate_log_filepath()
        mock_exists.assert_called_once_with("/path/to")
        mock_makedirs.assert_called_once_with("/path/to")
        assert test_config.get("log_filepath") == "/path/to/foo"

    def test__validate_log_filepath_cannot_create_reset_settings(self, mocker):
        mock_exists = mocker.patch("solarwinds_apm.apm_config.os.path.exists", return_value=False)
        mock_makedirs = mocker.patch(
            "solarwinds_apm.apm_config.os.makedirs",
            side_effect=FileNotFoundError("mock error")
        )

        test_config = apm_config.SolarWindsApmConfig()
        test_config._set_config_value("log_filepath", "/path/to/foo")
        test_config._validate_log_filepath()
        mock_exists.assert_called_once_with("/path/to")
        mock_makedirs.assert_called_once_with("/path/to")
        assert test_config.get("log_filepath") == ""

    def test_convert_to_bool_bool_true(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.convert_to_bool(True)

    def test_convert_to_bool_bool_false(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert not test_config.convert_to_bool(False)

    def test_convert_to_bool_int(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.convert_to_bool(0) is None

    def test_convert_to_bool_str_invalid(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.convert_to_bool("not-true-nor-false") is None

    def test_convert_to_bool_str_true(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.convert_to_bool("true")

    def test_convert_to_bool_str_true_mixed_case(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert test_config.convert_to_bool("tRuE")

    def test_convert_to_bool_str_false(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert not test_config.convert_to_bool("false")

    def test_convert_to_bool_str_false_mixed_case(self):
        test_config = apm_config.SolarWindsApmConfig()
        assert not test_config.convert_to_bool("fAlSE")

@pytest.fixture
def apm():
    return apm_config.SolarWindsApmConfig()

def test_to_configuration_default(apm):
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert isinstance(config, Configuration)
    assert config.enabled == apm.agent_enabled
    assert config.service == apm.service_name
    assert config.collector == apm.get("collector")
    assert config.headers["Authorization"].startswith("Bearer ")
    assert config.tracing_mode == (apm.get("tracing_mode") != 0)
    assert config.trigger_trace_enabled == (apm.get("trigger_trace") == 1)
    assert config.transaction_name == apm.get("transaction_name")
    assert isinstance(config.transaction_settings, list)

def test_to_configuration_with_service_key(apm):
    apm._set_config_value("service_key", "test_token:test_service")
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert config.headers["Authorization"] == "Bearer test_token"

def test_to_configuration_with_transaction_filters(apm):
    apm._set_config_value("transaction_filters", [
        {"tracing_mode": 1, "regex": re.compile(".*")}
    ])
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert len(config.transaction_settings) == 1
    assert isinstance(config.transaction_settings[0], TransactionSetting)
    assert config.transaction_settings[0].tracing is True

def test_to_configuration_with_disabled_tracing(apm):
    apm._set_config_value("tracing_mode", "disabled")
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert config.tracing_mode is False

def test_to_configuration_with_disabled_trigger_trace(apm):
    apm._set_config_value("trigger_trace", "disabled")
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert config.trigger_trace_enabled is False

def test_to_configuration_with_empty_transaction_filters(apm):
    apm._set_config_value("transaction_filters", [])
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert isinstance(config.transaction_settings, list)
    assert len(config.transaction_settings) == 0

def test_to_configuration_with_multiple_transaction_filters(apm):
    apm._set_config_value("transaction_filters", [
        {"tracing_mode": 1, "regex": re.compile(".*")},
        {"tracing_mode": 0, "regex": re.compile("foo")}
    ])
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert len(config.transaction_settings) == 2
    assert isinstance(config.transaction_settings[0], TransactionSetting)
    assert config.transaction_settings[0].tracing is True
    assert isinstance(config.transaction_settings[1], TransactionSetting)
    assert config.transaction_settings[1].tracing is False

def test_to_configuration_with_invalid_service_key(apm):
    apm._set_config_value("service_key", "invalid_format")
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert config.headers["Authorization"] == "Bearer invalid_format"

def test_to_configuration_with_empty_service_key(apm):
    apm._set_config_value("service_key", "")
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert config.headers["Authorization"] == "Bearer "

def test_to_configuration_with_disabled_agent(apm):
    apm.agent_enabled = False
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert config.enabled is False

def test_to_configuration_with_enabled_agent(apm):
    apm.agent_enabled = True
    config = apm_config.SolarWindsApmConfig.to_configuration(apm_config=apm)
    assert config.enabled is True
