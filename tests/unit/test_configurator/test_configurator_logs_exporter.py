# © 2024 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import pytest

from opentelemetry.sdk.environment_variables import (
    _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED,
)

from solarwinds_apm import configurator

# otel fixtures
from .fixtures.logging import get_logging_mocks
from .fixtures.resource import get_resource_mocks
from .fixtures.trace import get_trace_mocks

class TestConfiguratorLogsExporter:
    @pytest.fixture(autouse=True)
    def before_and_after_each(self):
        # Save any env vars for later just in case
        old_otel_ev = os.environ.get(
            _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED
        )
        if old_otel_ev:
            del os.environ[_OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED]
        old_logs_exporter = os.environ.get("OTEL_LOGS_EXPORTER", None)
        if old_logs_exporter:
            del os.environ["OTEL_LOGS_EXPORTER"]

        # Wait for test
        yield

        # Restore old env vars
        if old_logs_exporter:
            os.environ["OTEL_LOGS_EXPORTER"] = old_logs_exporter
        if old_otel_ev:
            os.environ[_OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED] = old_otel_ev

    def test_configure_logs_exporter_otel_false_sw_any(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_blprocessor,
        mock_slprocessor,
        mock_loggerprovider,
        mock_logginghandler,
    ):
        mocker.patch.dict(
            os.environ,
            {
                _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "false"
            }
        )
        trace_mocks = get_trace_mocks(mocker)

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_logs_exporter(
            mock_apmconfig_enabled,
        )

        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_loggerprovider.assert_not_called()
        mock_blprocessor.assert_not_called()
        mock_slprocessor.assert_not_called()
        mock_logginghandler.assert_not_called()

    def test_configure_logs_exporter_otel_none_sw_false(
        self,
        mocker,
        mock_apmconfig_logs_enabled_false,
        mock_blprocessor,
        mock_slprocessor,
        mock_loggerprovider,
        mock_logginghandler,
    ):
        mocker.patch.dict(
            os.environ,
            {
                _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "not-valid-bool-so-evals-to-none"
            }
        )
        trace_mocks = get_trace_mocks(mocker)

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_logs_exporter(
            mock_apmconfig_logs_enabled_false,
        )

        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_loggerprovider.assert_not_called()
        mock_blprocessor.assert_not_called()
        mock_slprocessor.assert_not_called()
        mock_logginghandler.assert_not_called()

    def test_configure_logs_exporter_otel_true_sw_false(
        self,
        mocker,
        mock_apmconfig_logs_enabled_false,
        mock_blprocessor,
        mock_slprocessor,
        mock_loggerprovider,
        mock_logginghandler,
    ):
        mocker.patch.dict(
            os.environ,
            {
                _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "true"
            }
        )
        trace_mocks = get_trace_mocks(mocker)

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_logs_exporter(
            mock_apmconfig_logs_enabled_false,
        )

        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_loggerprovider.assert_not_called()
        mock_blprocessor.assert_not_called()
        mock_slprocessor.assert_not_called()
        mock_logginghandler.assert_not_called()

    def test_configure_logs_exporter_otel_true_sw_none(
        self,
        mocker,
        mock_apmconfig_logs_enabled_none,
        mock_blprocessor,
        mock_slprocessor,
        mock_loggerprovider,
        mock_logginghandler,
    ):
        mocker.patch.dict(
            os.environ,
            {
                _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "true"
            }
        )
        trace_mocks = get_trace_mocks(mocker)

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_logs_exporter(
            mock_apmconfig_logs_enabled_none,
        )

        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_loggerprovider.assert_not_called()
        mock_blprocessor.assert_not_called()
        mock_slprocessor.assert_not_called()
        mock_logginghandler.assert_not_called()

    def test_configure_logs_exporter_otel_true_sw_true_no_exporter(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_blprocessor,
        mock_slprocessor,
        mock_loggerprovider,
        mock_logginghandler,
    ):
        mocker.patch.dict(
            os.environ,
            {
                _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "true",
                "OTEL_LOGS_EXPORTER": "",
            }
        )
        trace_mocks = get_trace_mocks(mocker)

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_logs_exporter(
            mock_apmconfig_enabled,
        )

        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_loggerprovider.assert_not_called()
        mock_blprocessor.assert_not_called()
        mock_slprocessor.assert_not_called()
        mock_logginghandler.assert_not_called()

    def test_configure_logs_exporter_otel_true_sw_true_invalid_exporter(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_blprocessor,
        mock_slprocessor,
        mock_loggerprovider,
        mock_logginghandler,
    ):
        # Mock entry points
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.configurator.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            side_effect=StopIteration("mock error")
        )

        mocker.patch.dict(
            os.environ,
            {
                _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "true",
                "OTEL_LOGS_EXPORTER": "invalid-exporter",
            }
        )
        get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)

        test_configurator = configurator.SolarWindsConfigurator()
        with pytest.raises(Exception):
            test_configurator._configure_logs_exporter(
                mock_apmconfig_enabled,
            )

        trace_mocks.get_tracer_provider.assert_called_once()
        trace_mocks.get_tracer_provider().get_tracer.assert_called_once()
        mock_loggerprovider.assert_called_once()

        mock_blprocessor.assert_not_called()
        mock_slprocessor.assert_not_called()
        mock_logginghandler.assert_not_called()

    def test_configure_logs_exporter_otel_true_sw_true_is_lambda(
        self,
        mocker,
        mock_apmconfig_enabled_is_lambda,
        mock_blprocessor,
        mock_slprocessor,
        mock_loggerprovider,
        mock_logginghandler,
    ):
        # Mock entry points
        mock_exporter = mocker.Mock()
        mock_exporter_class = mocker.Mock()
        mock_exporter_class.configure_mock(return_value=mock_exporter)
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_exporter_class)
        mock_exporter_entry_point = mocker.Mock()
        mock_exporter_entry_point.configure_mock(
            **{
                "load": mock_load,
            }
        )
        mock_points = iter([mock_exporter_entry_point])
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.configurator.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )

        mocker.patch.dict(
            os.environ,
            {
                _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "true",
                "OTEL_LOGS_EXPORTER": "valid-exporter",
            }
        )
        get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)
        get_logging_mocks(mocker)

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_logs_exporter(
            mock_apmconfig_enabled_is_lambda,
        )

        trace_mocks.get_tracer_provider.assert_called_once()
        trace_mocks.get_tracer_provider().get_tracer.assert_called_once()
        mock_loggerprovider.assert_called_once()

        mock_blprocessor.assert_not_called()
        mock_slprocessor.assert_called_once()
        mock_logginghandler.assert_called_once()

    def test_configure_logs_exporter_otel_true_sw_true_not_lambda(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_blprocessor,
        mock_slprocessor,
        mock_loggerprovider,
        mock_logginghandler,
    ):
        # Mock entry points
        mock_exporter = mocker.Mock()
        mock_exporter_class = mocker.Mock()
        mock_exporter_class.configure_mock(return_value=mock_exporter)
        mock_load = mocker.Mock()
        mock_load.configure_mock(return_value=mock_exporter_class)
        mock_exporter_entry_point = mocker.Mock()
        mock_exporter_entry_point.configure_mock(
            **{
                "load": mock_load,
            }
        )
        mock_points = iter([mock_exporter_entry_point])
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.configurator.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            return_value=mock_points
        )

        mocker.patch.dict(
            os.environ,
            {
                _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: "true",
                "OTEL_LOGS_EXPORTER": "valid-exporter",
            }
        )
        get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)
        get_logging_mocks(mocker)

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_logs_exporter(
            mock_apmconfig_enabled,
        )

        trace_mocks.get_tracer_provider.assert_called_once()
        trace_mocks.get_tracer_provider().get_tracer.assert_called_once()
        mock_loggerprovider.assert_called_once()

        mock_blprocessor.assert_called_once()
        mock_slprocessor.assert_not_called()
        mock_logginghandler.assert_called_once()