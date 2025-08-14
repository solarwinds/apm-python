# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import pytest
from solarwinds_apm.apm_config import SolarWindsApmConfig


class TestSolarWindsApmConfigCalculateMetricsEnabled:
    @pytest.fixture(autouse=True)
    def clear_env_vars(self):
        # Clear environment variables before each test
        os.environ.clear()

    def test_calculate_metrics_enabled_with_env_var_true(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_EXPORT_METRICS_ENABLED": "true"})
        assert SolarWindsApmConfig.calculate_metrics_enabled() is True

    def test_calculate_metrics_enabled_with_env_var_false(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_EXPORT_METRICS_ENABLED": "false"})
        assert SolarWindsApmConfig.calculate_metrics_enabled() is False

    def test_calculate_metrics_enabled_with_config_not_provided_true(self, mocker):
        mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={"export_metrics_enabled": "true"},
        )
        mocker.patch.object(SolarWindsApmConfig, "convert_to_bool", return_value=True)
        assert SolarWindsApmConfig.calculate_metrics_enabled() is True

    def test_calculate_metrics_enabled_with_config_not_provided_false(self, mocker):
        mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={"export_metrics_enabled": "false"},
        )
        mocker.patch.object(SolarWindsApmConfig, "convert_to_bool", return_value=False)
        assert SolarWindsApmConfig.calculate_metrics_enabled() is False

    def test_calculate_metrics_enabled_with_config_not_boolean(self, mocker):
        assert (
            SolarWindsApmConfig.calculate_metrics_enabled(
                cnf_dict={"export_metrics_enabled": "foo-bar"}
            )
            is True
        )

    def test_calculate_metrics_enabled_with_config_not_provided_and_env_var(
        self, mocker
    ):
        mocker.patch.dict(os.environ, {"SW_APM_EXPORT_METRICS_ENABLED": "true"})
        mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={"export_metrics_enabled": "false"},
        )
        assert SolarWindsApmConfig.calculate_metrics_enabled() is True

    def test_calculate_metrics_enabled_with_provided_cnf_dict(self, mocker):
        mock_get_cnf_dict = mocker.patch.object(SolarWindsApmConfig, "get_cnf_dict")
        assert (
            SolarWindsApmConfig.calculate_metrics_enabled(
                cnf_dict={"export_metrics_enabled": True}
            )
            is True
        )
        mock_get_cnf_dict.assert_not_called()
