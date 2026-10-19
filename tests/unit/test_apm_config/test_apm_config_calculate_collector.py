# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0

import os

import pytest

from solarwinds_apm.apm_config import SolarWindsApmConfig


class TestSolarWindsApmConfigCalculateCollector:
    @pytest.fixture(autouse=True)
    def clear_env_vars(self):
        # Clear environment variables before each test
        os.environ.clear()

    def test_calculate_collector_default(self, mocker):
        assert (
            SolarWindsApmConfig.calculate_collector()
            == "apm.collector.na-01.cloud.solarwinds.com"
        )

    def test_calculate_collector_with_env_var_set(self, mocker):
        mocker.patch.dict(os.environ, {"SW_APM_COLLECTOR": "foo-collector"})
        assert SolarWindsApmConfig.calculate_collector() == "foo-collector"

    def test_calculate_collector_with_config_not_provided(self, mocker):
        mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={"collector": "bar-collector"},
        )
        assert SolarWindsApmConfig.calculate_collector() == "bar-collector"

    def test_calculate_collector_with_config_not_provided_and_env_var(
        self, mocker
    ):
        mocker.patch.dict(os.environ, {"SW_APM_COLLECTOR": "foo-collector"})
        mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={"collector": "bar-collector"},
        )
        assert SolarWindsApmConfig.calculate_collector() == "foo-collector"

    def test_calculate_collector_with_provided_cnf_dict(self, mocker):
        mock_get_cnf_dict = mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={"collector": "bar-collector"},
        )
        assert (
            SolarWindsApmConfig.calculate_collector(
                cnf_dict={"collector": "baz-collector"}
            )
            == "baz-collector"
        )
        mock_get_cnf_dict.assert_not_called()

    def test_calculate_collector_with_provided_cnf_dict_while_env(
        self, mocker
    ):
        mocker.patch.dict(os.environ, {"SW_APM_COLLECTOR": "foo-collector"})
        mock_get_cnf_dict = mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={"collector": "bar-collector"},
        )
        assert (
            SolarWindsApmConfig.calculate_collector(
                cnf_dict={"collector": "baz-collector"}
            )
            == "foo-collector"
        )
        mock_get_cnf_dict.assert_not_called()
