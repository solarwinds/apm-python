# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import pytest
from solarwinds_apm.apm_config import SolarWindsApmConfig

class TestSolarWindsApmConfigCalculateCollector:
    @pytest.fixture(autouse=True)
    def clear_env_vars(self):
        # Clear environment variables before each test
        os.environ.clear()

    def test_calculate_collector_default(self, mocker):
        assert SolarWindsApmConfig.calculate_collector() == "apm.collector.na-01.cloud.solarwinds.com"

    def test_calculate_collector_with_env_var_set(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_COLLECTOR": "foo-collector"})
        assert SolarWindsApmConfig.calculate_collector() == "foo-collector"

    def test_calculate_collector_with_config_not_provided(self, mocker):
        mocker.patch.object(SolarWindsApmConfig, 'get_cnf_dict', return_value={"collector": "bar-collector"})
        assert SolarWindsApmConfig.calculate_collector() == "bar-collector"

    def test_calculate_collector_with_config_not_provided_and_env_var(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_COLLECTOR": "foo-collector"})
        mocker.patch.object(SolarWindsApmConfig, 'get_cnf_dict', return_value={"collector": "bar-collector"})
        assert SolarWindsApmConfig.calculate_collector() == "foo-collector"

    def test_calculate_collector_with_provided_cnf_dict(self, mocker):
        mock_get_cnf_dict = mocker.patch.object(SolarWindsApmConfig, 'get_cnf_dict', return_value={"collector": "bar-collector"})
        assert SolarWindsApmConfig.calculate_collector(cnf_dict={"collector": "baz-collector"}) == "baz-collector"
        mock_get_cnf_dict.assert_not_called()

    def test_calculate_collector_with_provided_cnf_dict_while_env(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_COLLECTOR": "foo-collector"})
        mock_get_cnf_dict = mocker.patch.object(SolarWindsApmConfig, 'get_cnf_dict', return_value={"collector": "bar-collector"})
        assert SolarWindsApmConfig.calculate_collector(cnf_dict={"collector": "baz-collector"}) == "foo-collector"
        mock_get_cnf_dict.assert_not_called()

