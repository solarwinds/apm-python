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
        assert resulting_config.service_name == "key"
        # cnf_dict is none
        assert resulting_config.get_cnf_dict() is None

    def test_get_cnf_dict_custom_path_no_file(
        self,
        mocker,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
            "SW_APM_CONFIG_FILE": "nothing-is-here",
        })
        # use key from env var, agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.service_name == "key-service-name"
        # cnf_dict is none
        assert resulting_config.get_cnf_dict() is None

    # pylint:disable=unused-argument
    def test_get_cnf_dict_not_valid_json(
        self,
        mocker,
        fixture_cnf_file_invalid_json,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
            "SW_APM_CONFIG_FILE": "nothing-is-here",
        })
        # use key from env var, agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.service_name == "key-service-name"
        # cnf_dict is none
        assert resulting_config.get_cnf_dict() is None

    # pylint:disable=unused-argument
    def test_get_cnf_dict(
        self,
        mocker,
        fixture_cnf_file,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
            "SW_APM_CONFIG_FILE": "nothing-is-here",
        })
        # use key from env var, agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.service_name == "key-service-name"
        # cnf_dict is dict with kv from fixture
        assert resulting_config.get_cnf_dict() == {"foo": "bar"}

    def test_update_with_cnf_file_prependdomain_invalid(
        self,
        mocker,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
        })
        mock_update_txn_filters = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.update_transaction_filters"
        )
        some_cnf_dict = {
            "transaction": {
                "prependDomain": "not-valid-boolean"
            }
        }
        mock_get_cnf_dict = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict"
        )
        mock_get_cnf_dict.configure_mock(
            return_value=some_cnf_dict
        )
        # use key from env var, agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.service_name == "key-service-name"
        # config does not include prepend_domain from mock
        assert resulting_config.get("transaction.prepend_domain_name") == False
        # update_transaction_filters was called
        mock_update_txn_filters.assert_called_once_with(some_cnf_dict)

    def test_update_with_cnf_file_prependdomain_valid(
        self,
        mocker,
    ):
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key-service-name",
        })
        mock_update_txn_filters = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.update_transaction_filters"
        )
        some_cnf_dict = {
            "transaction": {
                "prependDomain": True
            }
        }
        mock_get_cnf_dict = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict"
        )
        mock_get_cnf_dict.configure_mock(
            return_value=some_cnf_dict
        )
        # use key from env var, agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.service_name == "key-service-name"
        # config includes prepend_domain from mock
        assert resulting_config.get("transaction.prepend_domain_name") == True
        # update_transaction_filters was called
        mock_update_txn_filters.assert_called_once_with(some_cnf_dict)

    # pylint:disable=unused-argument
    def test_update_with_cnf_file_all_valid(
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
        # use key from env var (Python APM only uses key from here),
        # agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.service_name == "key-service-name"
        # config includes snake_case versions of mock's camelCase keys
        # and valid values
        assert resulting_config.agent_enabled == True
        assert resulting_config.get("tracing_mode") == 1
        assert resulting_config.get("trigger_trace") == "enabled"
        assert resulting_config.get("collector") == "foo-bar"
        assert resulting_config.get("reporter") == "udp"
        assert resulting_config.get("debug_level") == 6
        assert resulting_config.get("hostname_alias") == "foo-bar"
        assert resulting_config.get("trustedpath") == "foo-bar"
        assert resulting_config.get("events_flush_interval") == 2
        assert resulting_config.get("max_request_size_bytes") == 2
        assert resulting_config.get("ec2_metadata_timeout") == 1234
        assert resulting_config.get("max_flush_wait_time") == 2
        assert resulting_config.get("max_transactions") == 2
        assert resulting_config.get("logname") == "foo-bar"
        assert resulting_config.get("trace_metrics") == 2
        assert resulting_config.get("token_bucket_capacity") == 2
        assert resulting_config.get("token_bucket_rate") == 2
        assert resulting_config.get("bufsize") == 2
        assert resulting_config.get("histogram_precision") == 2
        assert resulting_config.get("reporter_file_single") == 2
        assert resulting_config.get("enable_sanitize_sql") == True
        assert resulting_config.get("log_trace_id") == "always"
        assert resulting_config.get("proxy") == "http://foo-bar"
        assert resulting_config.get("transaction.prepend_domain_name") == True
        assert resulting_config.get("is_grpc_clean_hack_enabled") == True

        # update_transaction_filters was called
        mock_update_txn_filters.assert_called_once_with(fixture_cnf_dict)
        # Restore old collector
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector

    def test_update_with_cnf_file_mostly_invalid(
        self,
        mocker,
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
            "reporter": "not-ssl-or-anything",
            "debugLevel": "foo",
            "serviceKey": "not-good-to-put-here-and-wont-be-used",
            "hostnameAlias": False,
            "trustedpath": False,
            "eventsFlushInterval": "foo",
            "maxRequestSizeBytes": "foo",
            "ec2MetadataTimeout": 999999999,
            "maxFlushWaitTime": "foo",
            "maxTransactions": "foo",
            "logname": False,
            "traceMetrics": "foo",
            "tokenBucketCapacity": "foo",
            "tokenBucketRate": "foo",
            "bufsize": "foo",
            "histogramPrecision": "foo",
            "reporterFileSingle": "foo",
            "enableSanitizeSql": "foo",
            "log_trace_id": "not-never-always-etc",
            "proxy": "foo",
            "transaction": {
                "prependDomain": "foo"
            },
            "isGrpcCleanHackEnabled": "foo",
        }
        mock_get_cnf_dict = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict"
        )
        mock_get_cnf_dict.configure_mock(
            return_value=mostly_invalid_cnf_dict
        )
        # use key from env var (Python APM only uses key from here),
        # agent enabled, nothing has errored
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.agent_enabled == True
        assert resulting_config.service_name == "key-service-name"
        # config includes snake_case versions of mock's camelCase keys
        # and default values because invalid ones ignored
        assert resulting_config.get("tracing_mode") == -1
        assert resulting_config.get("trigger_trace") == "enabled"
        assert resulting_config.get("reporter") == ""
        assert resulting_config.get("debug_level") == 2
        assert resulting_config.get("events_flush_interval") == -1
        assert resulting_config.get("max_request_size_bytes") == -1
        assert resulting_config.get("ec2_metadata_timeout") == 1000
        assert resulting_config.get("max_flush_wait_time") == -1
        assert resulting_config.get("max_transactions") == -1
        assert resulting_config.get("trace_metrics") == -1
        assert resulting_config.get("token_bucket_capacity") == -1
        assert resulting_config.get("token_bucket_rate") == -1
        assert resulting_config.get("bufsize") == -1
        assert resulting_config.get("histogram_precision") == -1
        assert resulting_config.get("reporter_file_single") == 0
        assert resulting_config.get("enable_sanitize_sql") == True
        assert resulting_config.get("log_trace_id") == "never"
        assert resulting_config.get("proxy") == ""
        assert resulting_config.get("transaction.prepend_domain_name") == False
        assert resulting_config.get("is_grpc_clean_hack_enabled") == False
        # Meanwhile these are pretty open
        assert resulting_config.get("collector") == "False"
        assert resulting_config.get("hostname_alias") == "False"
        assert resulting_config.get("trustedpath") == "False"
        assert resulting_config.get("logname") == "False"

        # update_transaction_filters was called
        mock_update_txn_filters.assert_called_once_with(mostly_invalid_cnf_dict)
        # Restore old collector
        if old_collector:
            os.environ["SW_APM_COLLECTOR"] = old_collector

    # pylint:disable=unused-argument
    def test_update_with_cnf_file_and_all_validenv_vars(
        self,
        mocker,
    ):
        pass
