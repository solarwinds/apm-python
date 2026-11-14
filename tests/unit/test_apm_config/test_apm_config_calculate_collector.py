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
        collector = "apm.collector.ap-01.cloud.solarwinds.com"
        mocker.patch.dict(os.environ, {"SW_APM_COLLECTOR": collector})
        assert SolarWindsApmConfig.calculate_collector() == collector

    @pytest.mark.parametrize(
        ("collector", "expected"),
        [
            (
                "https://apm.collector.na-01.cloud.solarwinds.com:443",
                "apm.collector.na-01.cloud.solarwinds.com",
            ),
            (
                "APM.COLLECTOR.NA-02.CLOUD.SOLARWINDS.COM",
                "apm.collector.na-02.cloud.solarwinds.com",
            ),
            (
                "https://apm.collector.eu-01.cloud.solarwinds.com/",
                "apm.collector.eu-01.cloud.solarwinds.com",
            ),
            (
                "https://apm.collector.eu-02.cloud.solarwinds.com",
                "apm.collector.eu-02.cloud.solarwinds.com",
            ),
            (
                "apm.collector.na-01.dev-ssp.solarwinds.com",
                "apm.collector.na-01.dev-ssp.solarwinds.com",
            ),
            (
                "apm.collector.na-02.st-ssp.solarwinds.com",
                "apm.collector.na-02.st-ssp.solarwinds.com",
            ),
        ],
    )
    def test_calculate_collector_accepts_documented_regional_hostname_pattern(
        self, collector, expected
    ):
        assert (
            SolarWindsApmConfig.calculate_collector(
                cnf_dict={"collector": collector}
            )
            == expected
        )

    def test_calculate_collector_with_config_not_provided(self, mocker):
        collector = "apm.collector.eu-01.cloud.solarwinds.com"
        mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={"collector": collector},
        )
        assert SolarWindsApmConfig.calculate_collector() == collector

    def test_calculate_collector_with_config_not_provided_and_env_var(
        self, mocker
    ):
        env_collector = "apm.collector.ap-01.cloud.solarwinds.com"
        mocker.patch.dict(os.environ, {"SW_APM_COLLECTOR": env_collector})
        mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={
                "collector": "apm.collector.eu-01.cloud.solarwinds.com"
            },
        )
        assert SolarWindsApmConfig.calculate_collector() == env_collector

    def test_calculate_collector_with_provided_cnf_dict(self, mocker):
        collector = "apm.collector.na-02.cloud.solarwinds.com"
        mock_get_cnf_dict = mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={"collector": "bar-collector"},
        )
        assert (
            SolarWindsApmConfig.calculate_collector(
                cnf_dict={"collector": collector}
            )
            == collector
        )
        mock_get_cnf_dict.assert_not_called()

    def test_calculate_collector_with_provided_cnf_dict_while_env(
        self, mocker
    ):
        env_collector = "apm.collector.ap-01.cloud.solarwinds.com"
        mocker.patch.dict(os.environ, {"SW_APM_COLLECTOR": env_collector})
        mock_get_cnf_dict = mocker.patch.object(
            SolarWindsApmConfig,
            "get_cnf_dict",
            return_value={"collector": "bar-collector"},
        )
        assert (
            SolarWindsApmConfig.calculate_collector(
                cnf_dict={
                    "collector": "apm.collector.na-02.cloud.solarwinds.com"
                }
            )
            == env_collector
        )
        mock_get_cnf_dict.assert_not_called()

    @pytest.mark.parametrize(
        "collector",
        [
            "apm.collector.na-01.cloud.solarwinds.com.evil.example",
            "https://user@apm.collector.na-01.cloud.solarwinds.com",
            "http://apm.collector.na-01.cloud.solarwinds.com",
            "https://apm.collector.na-01.cloud.solarwinds.com:444",
            "https://apm.collector.na-01.cloud.solarwinds.com:abc",
            "https://apm.collector.na-01.cloud.solarwinds.com/v1",
            "https://apm.collector.na-01.cloud.solarwinds.com?next=evil",
            "https://apm.collector.na-01.cloud.solarwinds.com#fragment",
            "apm.collector.na-01.cloud.solarwinds.com.evil",
            "apm.collector.st-ssp.solarwinds.com",
        ],
    )
    def test_calculate_collector_rejects_unsupported_or_malformed_hosts(
        self, collector
    ):
        assert (
            SolarWindsApmConfig.calculate_collector(
                cnf_dict={"collector": collector}
            )
            == SolarWindsApmConfig._CONFIG_COLLECTOR_DEFAULT
        )

    def test_calculate_collector_invalid_environment_value_overrides_config(
        self, mocker
    ):
        mocker.patch.dict(
            os.environ,
            {"SW_APM_COLLECTOR": "https://collector.example"},
        )

        assert (
            SolarWindsApmConfig.calculate_collector(
                cnf_dict={
                    "collector": "apm.collector.eu-01.cloud.solarwinds.com"
                }
            )
            == SolarWindsApmConfig._CONFIG_COLLECTOR_DEFAULT
        )

    def test_to_configuration_validates_effective_sampler_collector(
        self, mocker
    ):
        mocker.patch.dict(os.environ, {}, clear=True)
        apm_config = mocker.Mock()
        apm_config.agent_enabled = True
        apm_config.service_name = "test-service"
        apm_config.get.side_effect = {
            "service_key": "test-token",
            "transaction_filters": [],
            "collector": "https://collector.example",
            "tracing_mode": -1,
            "trigger_trace": 1,
            "transaction_name": None,
        }.get

        configuration = SolarWindsApmConfig.to_configuration(apm_config)

        assert (
            configuration.collector
            == SolarWindsApmConfig._CONFIG_COLLECTOR_DEFAULT
        )
