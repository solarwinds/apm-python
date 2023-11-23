# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest

# ==================================================================
# Configurator Otel fixtures
# ==================================================================

@pytest.fixture(name="mock_set_global_textmap")
def mock_set_global_textmap(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.set_global_textmap",
    )

@pytest.fixture(name="mock_set_global_response_propagator")
def mock_set_global_response_propagator(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.set_global_response_propagator",
    )

@pytest.fixture(name="mock_composite_propagator")
def mock_composite_propagator(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.CompositePropagator",
    )

@pytest.fixture(name="mock_bsprocessor")
def mock_bsprocessor(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.BatchSpanProcessor",
    )

@pytest.fixture(name="mock_pemreader")
def mock_pemreader(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.PeriodicExportingMetricReader",
    )

@pytest.fixture(name="mock_tracerprovider")
def mock_tracerprovider(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.TracerProvider"
    )

# ==================================================================
# Configurator APM Python mocks
# ==================================================================

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
            "get": mock_get_exp,
            "service_name": "foo-service",
        }
    )
    return mock_apmconfig

@pytest.fixture(name="mock_apmconfig_disabled")
def mock_apmconfig_disabled(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(mocker, False, False)
    )

@pytest.fixture(name="mock_apmconfig_enabled")
def mock_apmconfig_enabled(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(mocker, True, False)
    )

@pytest.fixture(name="mock_apmconfig_enabled_expt")
def mock_apmconfig_enabled_expt(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(mocker, True, True)
    )

@pytest.fixture(name="mock_extension")
def mock_extension(mocker):
    return mocker.patch(
        "solarwinds_apm.extension"
    )

@pytest.fixture(name="mock_reporter")
def mock_reporter(mocker):
    return mocker.Mock()

@pytest.fixture(name="mock_fwkv_manager")
def mock_fwkv_manager(mocker):
    return mocker.patch(
        "solarwinds_apm.apm_fwkv_manager.SolarWindsFrameworkKvManager"
    )

@pytest.fixture(name="mock_meter_manager")
def mock_meter_manager(mocker):
    return mocker.patch(
        "solarwinds_apm.apm_meter_manager.SolarWindsMeterManager"
    )

@pytest.fixture(name="mock_txn_name_manager")
def mock_txn_name_manager(mocker):
    return mocker.patch(
        "solarwinds_apm.apm_txname_manager.SolarWindsTxnNameManager"
    )