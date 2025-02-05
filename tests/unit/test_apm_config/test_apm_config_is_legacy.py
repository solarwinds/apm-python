# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import pytest

from solarwinds_apm.apm_config import SolarWindsApmConfig

class TestSolarWindsApmConfigIsLegacy:
    def test_calculate_is_legacy_default(self, mocker):
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={}
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is False

    def test_calculate_is_legacy_with_env_var_not_boolean(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "foo-bar"})
        assert SolarWindsApmConfig.calculate_is_legacy() is False

    def test_calculate_is_legacy_with_env_var_false(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "false"})
        assert SolarWindsApmConfig.calculate_is_legacy() is False

    def test_calculate_is_legacy_with_env_var_true(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "true"})
        assert SolarWindsApmConfig.calculate_is_legacy() is True

    def test_calculate_is_legacy_with_unread_config_not_boolean(self, mocker):
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={"legacy": "foo-bar"},
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is False

    def test_calculate_is_legacy_with_unread_config_false(self, mocker):
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={"legacy": "false"},
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is False

    def test_calculate_is_legacy_with_unread_config_true(self, mocker):
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={"legacy": "true"},
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is True

    def test_calculate_is_legacy_with_unread_config_not_bool_env_var_not_bool(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "foo-bar"})
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={"legacy": "foo-bar"},
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is False

    def test_calculate_is_legacy_with_unread_config_false_env_var_false(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "false"})
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={"legacy": "false"},
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is False

    def test_calculate_is_legacy_with_unread_config_false_env_var_true(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "true"})
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={"legacy": "false"},
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is True

    def test_calculate_is_legacy_with_unread_config_not_bool_env_var_true(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "true"})
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={"legacy": "foo-bar"},
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is True

    def test_calculate_is_legacy_with_unread_config_true_env_var_false(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "false"})
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={"legacy": "true"},
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is False

    def test_calculate_is_legacy_with_unread_config_true_env_var_not_bool(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "foo-bar"})
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={"legacy": "true"},
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is True

    def test_calculate_is_legacy_with_unread_config_true_env_var_true(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "true"})
        mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
            return_value={"legacy": "true"},
        )
        assert SolarWindsApmConfig.calculate_is_legacy() is True

    def test_calculate_is_legacy_with_config_not_boolean(self, mocker):
        mock_get_cnf = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
        )
        assert SolarWindsApmConfig.calculate_is_legacy({"legacy": "foo-bar"}) is False
        mock_get_cnf.assert_not_called()

    def test_calculate_is_legacy_with_config_false(self, mocker):
        mock_get_cnf = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
        )
        assert SolarWindsApmConfig.calculate_is_legacy({"legacy": "false"}) is False
        mock_get_cnf.assert_not_called()

    def test_calculate_is_legacy_with_config_true(self, mocker):
        mock_get_cnf = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
        )
        assert SolarWindsApmConfig.calculate_is_legacy({"legacy": "true"}) is True
        mock_get_cnf.assert_not_called()

    def test_calculate_is_legacy_with_config_not_bool_env_var_not_bool(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "foo-bar"})
        mock_get_cnf = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
        )
        assert SolarWindsApmConfig.calculate_is_legacy({"legacy": "foo-bar"}) is False
        mock_get_cnf.assert_not_called()

    def test_calculate_is_legacy_with_config_false_env_var_false(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "false"})
        mock_get_cnf =  mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
        )
        assert SolarWindsApmConfig.calculate_is_legacy({"legacy": "false"}) is False
        mock_get_cnf.assert_not_called()

    def test_calculate_is_legacy_with_config_false_env_var_true(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "true"})
        mock_get_cnf = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
        )
        assert SolarWindsApmConfig.calculate_is_legacy({"legacy": "false"}) is True
        mock_get_cnf.assert_not_called()

    def test_calculate_is_legacy_with_config_not_bool_env_var_true(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "true"})
        mock_get_cnf = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
        )
        assert SolarWindsApmConfig.calculate_is_legacy({"legacy": "foo-bar"}) is True
        mock_get_cnf.assert_not_called()

    def test_calculate_is_legacy_with_config_true_env_var_false(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "false"})
        mock_get_cnf = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
        )
        assert SolarWindsApmConfig.calculate_is_legacy({"legacy": "true"}) is False
        mock_get_cnf.assert_not_called()

    def test_calculate_is_legacy_with_config_true_env_var_not_bool(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "foo-bar"})
        mock_get_cnf = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
        )
        assert SolarWindsApmConfig.calculate_is_legacy({"legacy": "true"}) is True
        mock_get_cnf.assert_not_called()

    def test_calculate_is_legacy_with_config_true_env_var_true(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_LEGACY": "true"})
        mock_get_cnf = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict",
        )
        assert SolarWindsApmConfig.calculate_is_legacy({"legacy": "true"}) is True
        mock_get_cnf.assert_not_called()
