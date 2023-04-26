# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from solarwinds_apm import apm_config

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
        assert resulting_config._calculate_agent_enabled()
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
        assert resulting_config._calculate_agent_enabled()
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
        assert resulting_config._calculate_agent_enabled()
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
        assert resulting_config._calculate_agent_enabled()
        assert resulting_config.service_name == "key-service-name"
        # cnf_dict is dict with kv from fixture
        assert resulting_config.get_cnf_dict() == {"foo": "bar"}

    def test_update_with_cnf_file_prependdomain_invalid(self):
        pass
        # update_transaction_filters was called

    def test_update_with_cnf_file_prependdomain_valid(self):
        pass
    # update_transaction_filters was called

    def test_update_with_cnf_file_values_none(self):
        pass
    # update_transaction_filters was called

    def test_update_with_cnf_file_values_not_none(self):
        pass
    # update_transaction_filters was called