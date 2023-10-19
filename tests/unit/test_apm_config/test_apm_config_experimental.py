# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from solarwinds_apm import apm_config


def helper_mock_common(mocker):
    mock_iter_entry_points = mocker.patch(
        "solarwinds_apm.apm_config.iter_entry_points"
    )
    mock_points = mocker.MagicMock()
    mock_points.__iter__.return_value = ["foo"]
    mock_iter_entry_points.configure_mock(
        return_value=mock_points
    )

class TestSolarWindsApmConfigExperimental:
    def test_experimental_default(
        self,
        mocker,
    ):
        helper_mock_common(mocker)
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.get("experimental") == {}

    def test_experimental_env_var_otelcol_not_bool(
        self,
        mocker,
    ):
        helper_mock_common(mocker)
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key",
            "SW_APM_EXPERIMENTAL_OTEL_COLLECTOR": "foo"
        })
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.get("experimental") == {}

    def test_experimental_env_var_otelcol_true(
        self,
        mocker,
    ):
        helper_mock_common(mocker)
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key",
            "SW_APM_EXPERIMENTAL_OTEL_COLLECTOR": "true"
        })
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.get("experimental") == {"otel_collector": True}

    def test_experimental_cnf_file_otelcol_not_bool(
        self,
        mocker,
    ):
        helper_mock_common(mocker)
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        mock_get_cnf_dict = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict"
        )
        mock_get_cnf_dict.configure_mock(
            return_value={
                "experimental": {
                    "otel_collector": "foo",
                },
            }
        )
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.get("experimental") == {}

    def test_experimental_cnf_file_otelcol_true(
        self,
        mocker,
    ):
        helper_mock_common(mocker)
        mocker.patch.dict(os.environ, {
            "SW_APM_SERVICE_KEY": "valid:key",
        })
        mock_get_cnf_dict = mocker.patch(
            "solarwinds_apm.apm_config.SolarWindsApmConfig.get_cnf_dict"
        )
        mock_get_cnf_dict.configure_mock(
            return_value={
                "experimental": {
                    "otel_collector": True,
                },
            }
        )
        resulting_config = apm_config.SolarWindsApmConfig()
        assert resulting_config.get("experimental") == {"otel_collector": True}
