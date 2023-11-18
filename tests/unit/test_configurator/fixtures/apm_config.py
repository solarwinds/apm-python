# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest


def get_apmconfig_mocks(mocker, enabled=True, exp_otel_col=True):
    mock_get_otelcol = mocker.Mock()
    if exp_otel_col == True:
        mock_get_otelcol.configure_mock(return_value=True)
    else:
        mock_get_otelcol.configure_mock(return_value=False)

    mock_get_exp = mocker.Mock()
    mock_get_exp.configure_mock(
        return_value=mocker.Mock(
            **{
                "get": mock_get_otelcol
            }
        )
    )

    mock_apmconfig = mocker.Mock()
    mock_apmconfig.configure_mock(
        **{
            "agent_enabled": enabled,
            "get": mock_get_exp
        }
    )
    return mock_apmconfig


@pytest.fixture(name="mock_apmconfig_disabled")
def fixture_mock_apmconfig_disabled(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(mocker, False, False)
    )


@pytest.fixture(name="mock_apmconfig_enabled")
def fixture_mock_apmconfig_enabled(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(mocker, True, False)
    )