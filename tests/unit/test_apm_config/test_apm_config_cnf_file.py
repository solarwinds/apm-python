# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from solarwinds_apm import apm_config

# pylint: disable=unused-import
from .fixtures.cnf_dict import fixture_cnf_dict
# pylint: disable=unused-import
from .fixtures.cnf_file import (
    fixture_cnf_file,
    fixture_cnf_file_invalid_json,
)
# pylint: disable=unused-import
from .fixtures.env_vars import fixture_mock_env_vars

class TestSolarWindsApmConfigCnfFile:
    # pylint:disable=unused-argument
    def test_get_cnf_dict_default_path_no_file(
            self,
            mock_env_vars,
        ):
        # use key from env var, agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.get("service_key") == "valid:key"
        # cnf_dict is none
        assert resulting_config.get_cnf_dict() is None

    def test_get_cnf_dict_custom_path_no_file(
        self,
        mocker,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
            "SW_APM_CONFIG_FILE": "nothing-is-here",
        })
        # use key from env var, agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.get("service_key") == "valid:key-service-name"
        # cnf_dict is none
        assert resulting_config.get_cnf_dict() is None

    # pylint:disable=unused-argument
    def test_get_cnf_dict_not_valid_json(
        self,
        mocker,
        fixture_cnf_file_invalid_json,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
            "SW_APM_CONFIG_FILE": "nothing-is-here",
        })
        # use key from env var, agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.get("service_key") == "valid:key-service-name"
        # cnf_dict is none
        assert resulting_config.get_cnf_dict() is None

    # pylint:disable=unused-argument
    def test_get_cnf_dict(
        self,
        mocker,
        fixture_cnf_file,
        mock_env_vars,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
            "SW_APM_CONFIG_FILE": "nothing-is-here",
        })
        # use key from env var, agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.get("service_key") == "valid:key-service-name"
        # cnf_dict is dict with kv from fixture
        assert resulting_config.get_cnf_dict() == {"foo": "bar"}

    # pylint:disable=unused-argument
    def test_update_with_cnf_file_all_valid(
        self,
        mocker,
        fixture_cnf_dict,
        mock_env_vars,
    ):
        # Save any collector in os for later
        old_collector = os.environ.get("SW_APM_COLLECTOR", None)
        if old_collector:
            del os.environ["SW_APM_COLLECTOR"]

        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
        })
        mock_update_txn_filters = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.update_transaction_filters"
        )
        mock_get_cnf_dict = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict"
        )
        mock_get_cnf_dict.configure_mock(
            return_value=fixture_cnf_dict
        )
        mock_apm_logging = mocker.patch(
            "solarwinds_apm.apm_config.apm_logging"
        )
        mock_apm_logging.configure_mock(
            **{
                "set_sw_log_level": mocker.Mock(),
                "ApmLoggingLevel.default_level": mocker.Mock(return_value=2)
            }
        )

        # use key from env var (Python APM only uses key from here),
        # agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.get("service_key") == "valid:key-service-name"
        # config includes snake_case versions of mock's camelCase keys
        # and valid values
        assert resulting_config.agent_enabled == True
        assert resulting_config.get("tracing_mode") == 1
        assert resulting_config.get("trigger_trace") == 1
        assert resulting_config.get("collector") == "foo-bar"
        assert resulting_config.get("debug_level") == 6
        assert resulting_config.get("export_logs_enabled") == True

        # update_transaction_filters was called
        mock_update_txn_filters.assert_called_once_with(fixture_cnf_dict)
        # Restore old collector
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector

    def test_update_with_cnf_file_mostly_invalid(
        self,
        mocker,
        mock_env_vars,
    ):
        # Save any collector in os for later
        old_collector = os.environ.get("SW_APM_COLLECTOR", None)
        if old_collector:
            del os.environ["SW_APM_COLLECTOR"]

        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
        })
        mock_update_txn_filters = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.update_transaction_filters"
        )
        mostly_invalid_cnf_dict = {
            "agentEnabled": "foo",
            "tracingMode": "foo",
            "triggerTrace": "foo",
            "collector": False,
            "debugLevel": "foo",
            "serviceKey": "not-good-to-put-here-and-wont-be-used",
            "tokenBucketCapacity": "foo",
            "tokenBucketRate": "foo",
            "exportLogsEnabled": "foo",
        }
        mock_get_cnf_dict = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict"
        )
        mock_get_cnf_dict.configure_mock(
            return_value=mostly_invalid_cnf_dict
        )
        mock_apm_logging = mocker.patch(
            "solarwinds_apm.apm_config.apm_logging"
        )
        mock_apm_logging.configure_mock(
            **{
                "set_sw_log_level": mocker.Mock(),
                "ApmLoggingLevel.default_level": mocker.Mock(return_value=2)
            }
        )
        # use key from env var (Python APM only uses key from here),
        # agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.get("service_key") == "valid:key-service-name"
        # config includes snake_case versions of mock's camelCase keys
        # and default values because invalid ones ignored
        assert resulting_config.get("tracing_mode") == -1
        assert resulting_config.get("trigger_trace") == 1
        assert resulting_config.get("debug_level") == 2
        assert resulting_config.get("export_logs_enabled") == False
        # Meanwhile these are pretty open
        assert resulting_config.get("collector") == "False"

        # update_transaction_filters was called
        mock_update_txn_filters.assert_called_once_with(mostly_invalid_cnf_dict)
        # Restore old collector
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector

    # pylint:disable=unused-argument
    def test_update_with_cnf_file_and_all_validenv_vars(
        self,
        mocker,
        fixture_cnf_dict,
    ):
        # Save any collector in os for later
        old_collector = os.environ.get("SW_APM_COLLECTOR", None)
        if old_collector:
            del os.environ["SW_APM_COLLECTOR"]

        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
            "SW_APM_AGENT_ENABLED": "false",
            "SW_APM_TRACING_MODE": "disabled",
            "SW_APM_TRIGGER_TRACE": "disabled",
            "SW_APM_COLLECTOR": "other-foo-bar",
            "SW_APM_DEBUG_LEVEL": "5",
            "SW_APM_EXPORT_LOGS_ENABLED": "true",
        })
        mock_update_txn_filters = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.update_transaction_filters"
        )
        mock_get_cnf_dict = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict"
        )
        mock_get_cnf_dict.configure_mock(
            return_value=fixture_cnf_dict
        )
        mock_apm_logging = mocker.patch(
            "solarwinds_apm.apm_config.apm_logging"
        )
        mock_apm_logging.configure_mock(
            **{
                "set_sw_log_level": mocker.Mock(),
                "ApmLoggingLevel.default_level": mocker.Mock(return_value=2)
            }
        )
        resulting_config = apm_config.SolarWindsApmConfig()
        # update_transaction_filters was called
        mock_update_txn_filters.assert_called_once_with(fixture_cnf_dict)

        # use all keys from env var, none from cnf_file
        assert resulting_config.get("service_key") == "valid:key-service-name"

        # Rest of config prioritizes env_var > cnf_file
        assert resulting_config.agent_enabled == False
        assert resulting_config.get("tracing_mode") == 0
        assert resulting_config.get("trigger_trace") == 0
        assert resulting_config.get("collector") == "other-foo-bar"
        assert resulting_config.get("debug_level") == 5
        assert resulting_config.get("export_logs_enabled") == True

        # Restore old collector
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector

    # pylint:disable=unused-argument
    def test_update_with_cnf_file_and_several_invalid_env_vars(
        self,
        mocker,
        fixture_cnf_dict,
    ):
        # Save any collector in os for later
        old_collector = os.environ.get("SW_APM_COLLECTOR", None)
        if old_collector:
            del os.environ["SW_APM_COLLECTOR"]

        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "not-valid-and-agent-will-be-disabled",
            "SW_APM_AGENT_ENABLED": "other-foo-bar",
            "SW_APM_TRACING_MODE": "other-foo-bar",
            "SW_APM_TRIGGER_TRACE": "other-foo-bar",
            "SW_APM_COLLECTOR": "False",
            "SW_APM_DEBUG_LEVEL": "other-foo-bar",
            "SW_APM_EXPORT_LOGS_ENABLED": "not-a-bool",
        })
        mock_update_txn_filters = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.update_transaction_filters"
        )
        mock_get_cnf_dict = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict"
        )
        mock_get_cnf_dict.configure_mock(
            return_value=fixture_cnf_dict
        )
        mock_apm_logging = mocker.patch(
            "solarwinds_apm.apm_config.apm_logging"
        )
        mock_apm_logging.configure_mock(
            **{
                "set_sw_log_level": mocker.Mock(),
                "ApmLoggingLevel.default_level": mocker.Mock(return_value=2)
            }
        )
        resulting_config = apm_config.SolarWindsApmConfig()
        # update_transaction_filters was called
        mock_update_txn_filters.assert_called_once_with(fixture_cnf_dict)

        # even if invalid, only service_key from env var used
        # and APM will be disabled
        assert resulting_config.agent_enabled == False
        assert resulting_config.get("service_key") == "not-valid-and-agent-will-be-disabled"  # the full key does not print to std out and appears masked

        # cnf_file values from fixture_cnf_dict are kept if same env_var invalid
        assert resulting_config.get("tracing_mode") == 1
        assert resulting_config.get("trigger_trace") == 1
        assert resulting_config.get("debug_level") == 6
        assert resulting_config.get("export_logs_enabled") == True

        # These are still valid, so env_var > cnf_file
        assert resulting_config.get("collector") == "False"

        # Restore old collector
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector
