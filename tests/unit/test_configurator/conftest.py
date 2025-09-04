# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest

from solarwinds_apm.apm_config import SolarWindsApmConfig

# ==================================================================
# Configurator stdlib fixtures
# ==================================================================

@pytest.fixture(name="mock_sys")
def mock_sys(mocker):
    mock_version_info = mocker.PropertyMock()
    mock_version_info.return_value = [3, 11, 12]
    mock_version = mocker.PropertyMock()
    mock_version.return_value = "foo-runtime"
    mock_exec = mocker.PropertyMock()
    mock_exec.return_value = "/foo/path"

    mock_sys = mocker.patch(
        "solarwinds_apm.configurator.sys"
    )
    type(mock_sys).version_info = mock_version_info
    type(mock_sys).version = mock_version
    type(mock_sys).executable = mock_exec
    type(mock_sys).implementation = mocker.PropertyMock()
    type(mock_sys).implementation.name = "foo-name"

    return mock_sys

@pytest.fixture(name="mock_sys_error_version_info")
def mock_sys_error_version_info(mocker):
    mock_version_info = mocker.PropertyMock()
    mock_version_info.return_value = []
    mock_version = mocker.PropertyMock()
    mock_version.return_value = "foo-runtime"
    mock_exec = mocker.PropertyMock()
    mock_exec.return_value = "/foo/path"

    mock_sys = mocker.patch(
        "solarwinds_apm.configurator.sys"
    )
    type(mock_sys).version_info = mock_version_info
    type(mock_sys).version = mock_version
    type(mock_sys).executable = mock_exec
    type(mock_sys).implementation = mocker.PropertyMock()
    type(mock_sys).implementation.name = "foo-name"

    return mock_sys

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
    mock_bsp = mocker.patch(
        "solarwinds_apm.configurator.BatchSpanProcessor",
    )
    mock_bsp.return_value = mocker.Mock()
    return mock_bsp

@pytest.fixture(name="mock_ssprocessor")
def mock_ssprocessor(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SimpleSpanProcessor",
    )

@pytest.fixture(name="mock_pemreader")
def mock_pemreader(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.PeriodicExportingMetricReader",
    )

@pytest.fixture(name="mock_blprocessor")
def mock_blprocessor(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.BatchLogRecordProcessor",
    )

@pytest.fixture(name="mock_tracerprovider")
def mock_tracerprovider(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarwindsTracerProvider"
    )

@pytest.fixture(name="mock_meterprovider")
def mock_meterprovider(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.MeterProvider",
    )

@pytest.fixture(name="mock_loggerprovider")
def mock_loggerprovider(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.LoggerProvider",
    )

@pytest.fixture(name="mock_logginghandler")
def mock_logginghandler(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.LoggingHandler",
    )

# ==================================================================
# Configurator APM Python ApmConfig mocks
# ==================================================================

def get_apmconfig_mocks(
    mocker,
    enabled=True,
    is_lambda=False,
    md_is_valid=True,
    export_logs_enabled=True,
    export_metrics_enabled=True,
):
    def get_side_effect(param):
        if param == "export_metrics_enabled":
            return export_metrics_enabled
        # TODO NH-101930 remove export_logs_enabled
        elif param == "export_logs_enabled":
            return export_logs_enabled
        elif param == "service_key":
            return "foo:bar"
        else:
            return "foo"

    mock_apmconfig = mocker.Mock()
    mock_apmconfig.configure_mock(
        **{
            "agent_enabled": enabled,
            "get": mocker.Mock(side_effect=get_side_effect),
            "service_name": "foo-service",
            "is_lambda": is_lambda,
            "oboe_api": mocker.Mock(),
            "convert_to_bool": SolarWindsApmConfig.convert_to_bool,
        }
    )
    return mock_apmconfig

@pytest.fixture(name="mock_apmconfig_disabled")
def mock_apmconfig_disabled(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(
            mocker,
            enabled=False,
        )
    )

@pytest.fixture(name="mock_apmconfig_enabled")
def mock_apmconfig_enabled(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(
            mocker,
        )
    )

@pytest.fixture(name="mock_apmconfig_enabled_export_logs_false")
def mock_apmconfig_enabled_export_logs_false(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(
            mocker,
            export_logs_enabled=False
        )
    )

@pytest.fixture(name="mock_apmconfig_enabled_md_invalid")
def mock_apmconfig_enabled_md_invalid(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(
            mocker,
            md_is_valid=False,
        )
    )

@pytest.fixture(name="mock_apmconfig_enabled_is_lambda")
def mock_apmconfig_enabled_is_lambda(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(
            mocker,
            is_lambda=True,
        )
    )

@pytest.fixture(name="mock_apmconfig_logs_enabled_false")
def mock_apmconfig_logs_enabled_false(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(
            mocker,
            export_logs_enabled=False
        )
    )

@pytest.fixture(name="mock_apmconfig_logs_enabled_none")
def mock_apmconfig_logs_enabled_none(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(
            mocker,
            export_logs_enabled=None
        )
    )

@pytest.fixture(name="mock_apmconfig_metrics_enabled_false")
def mock_apmconfig_metrics_enabled_false(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(
            mocker,
            export_metrics_enabled=False,
        )
    )

@pytest.fixture(name="mock_apmconfig_metrics_enabled_none")
def mock_apmconfig_metrics_enabled_none(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsApmConfig",
        get_apmconfig_mocks(
            mocker,
            export_metrics_enabled=None,
        )
    )

@pytest.fixture(name="mock_apmconfig_enabled_reporter_settings")
def mock_apmconfig_enabled_reporter_settings(mocker):
    mock_apmconfig = mocker.Mock()
    mock_apmconfig.configure_mock(
        **{
            "agent_enabled": True,
            "certificates": "foo-certs",
            "get": mocker.Mock(return_value="foo"),
            "service_name": "foo-service",
            "metric_format": "bar"
        }
    )
    return mock_apmconfig

# ==================================================================
# Configurator APM Python configurator mocks
# ==================================================================

def add_fw_versions(input_dict):
    input_dict.update({"foo-fw": "bar-version"})
    return input_dict

@pytest.fixture(name="mock_fw_versions")
def mock_fw_versions(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsConfigurator._add_all_instrumented_python_framework_versions",
        side_effect=add_fw_versions
    )

@pytest.fixture(name="mock_config_serviceentry_processor")
def mock_config_serviceentry_processor(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsConfigurator._configure_service_entry_span_processor"
    )

@pytest.fixture(name="mock_response_time_processor")
def mock_response_time_processor(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsConfigurator._configure_response_time_processor"
    )

@pytest.fixture(name="mock_custom_init_tracing")
def mock_custom_init_tracing(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsConfigurator._custom_init_tracing"
    )

@pytest.fixture(name="mock_custom_init_metrics")
def mock_custom_init_metrics(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsConfigurator._custom_init_metrics"
    )

@pytest.fixture(name="mock_init_logging")
def mock_init_logging(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator._init_logging"
    )

@pytest.fixture(name="mock_config_propagator")
def mock_config_propagator(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsConfigurator._configure_propagator"
    )

@pytest.fixture(name="mock_config_response_propagator")
def mock_config_response_propagator(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsConfigurator._configure_response_propagator"
    )

@pytest.fixture(name="mock_init_sw_reporter")
def mock_init_sw_reporter(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsConfigurator._initialize_solarwinds_reporter"
    )

@pytest.fixture(name="mock_create_init")
def mock_create_init(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsConfigurator._create_init_event"
    )

@pytest.fixture(name="mock_create_init_fail")
def mock_create_init_fail(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.SolarWindsConfigurator._create_init_event",
        return_value=None,
    )

# ==================================================================
# Configurator APM Python other mocks
# ==================================================================

@pytest.fixture(name="mock_apm_version")
def mock_apm_version(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.__version__",
        new="0.0.0",
    )
