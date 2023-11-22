# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os
import pytest

from solarwinds_apm import configurator

# otel fixtures
from .fixtures.metrics import get_metrics_mocks
from .fixtures.periodic_exporting_metric_reader import mock_pemreader
from .fixtures.resource import mock_resource
from .fixtures.trace import get_trace_mocks

# apm python fixtures
from .fixtures.apm_config import (
    mock_apmconfig_disabled,
    mock_apmconfig_enabled,
    mock_apmconfig_enabled_expt,
)


class TestConfiguratorMetricsExporter:
    def test_configure_metrics_exporter_disabled(
        self,
        mocker,
        mock_apmconfig_disabled,
        mock_pemreader,
    ):
        # Mock Otel
        mock_metrics, mock_set_meter_provider, mock_meter_provider = get_metrics_mocks(mocker)

        mock_trace, mock_get_tracer_provider, mock_add_span_processor, mock_tracer = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_metrics_exporter(
            mock_apmconfig_disabled,
        )
        mock_pemreader.assert_not_called()
        mock_get_tracer_provider.assert_not_called()
        mock_tracer.assert_not_called()
        mock_set_meter_provider.assert_not_called()
        mock_meter_provider.assert_not_called()


    def test_configure_metrics_exporter_flag_not_set(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_pemreader,
    ):
        # Mock Otel
        mock_metrics, mock_set_meter_provider, mock_meter_provider = get_metrics_mocks(mocker)

        mock_trace, mock_get_tracer_provider, mock_add_span_processor, mock_tracer = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_metrics_exporter(
            mock_apmconfig_enabled,
        )
        mock_pemreader.assert_not_called()
        mock_get_tracer_provider.assert_not_called()
        mock_tracer.assert_not_called()
        mock_set_meter_provider.assert_not_called()
        mock_meter_provider.assert_not_called()

    def test_configure_metrics_exporter_none(
        self,
        mocker,
        mock_apmconfig_enabled_expt,
        mock_pemreader,
    ):
        # Save any EXPORTER env var for later
        old_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_metrics_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]

        # Mock Otel
        mock_metrics, mock_set_meter_provider, mock_meter_provider = get_metrics_mocks(mocker)

        mock_trace, mock_get_tracer_provider, mock_add_span_processor, mock_tracer = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_metrics_exporter(
            mock_apmconfig_enabled_expt,
        )
        mock_pemreader.assert_not_called()
        mock_get_tracer_provider.assert_not_called()
        mock_tracer.assert_not_called()
        mock_metrics.assert_not_called()
        mock_set_meter_provider.assert_not_called()
        mock_meter_provider.assert_not_called()

        # Restore old EXPORTER
        if old_metrics_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_metrics_exporter

    def test_configure_metrics_exporter_invalid(
        self,
        mocker,
        mock_apmconfig_enabled_expt,
        mock_pemreader,
        mock_resource,
    ):
        # Save any EXPORTER env var for later
        old_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_metrics_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]

        # Mock entry points
        mock_iter_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.iter_entry_points"
        )
        mock_iter_entry_points.configure_mock(
            side_effect=StopIteration("mock error")
        )
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_METRICS_EXPORTER": "invalid_exporter"
            }
        )

        # Mock Otel
        mock_metrics, mock_set_meter_provider, mock_meter_provider = get_metrics_mocks(mocker)

        mock_trace, mock_get_tracer_provider, mock_add_span_processor, mock_tracer = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        with pytest.raises(Exception):
            test_configurator._configure_metrics_exporter(
                mock_apmconfig_enabled_expt,
            )
        mock_pemreader.assert_not_called()
        mock_get_tracer_provider.assert_not_called()
        mock_tracer.assert_not_called()
        mock_set_meter_provider.assert_not_called()
        mock_meter_provider.assert_not_called()

        # Restore old EXPORTER
        if old_metrics_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_metrics_exporter

    def test_configure_metrics_exporter_valid(
        self,
        mocker,
        mock_apmconfig_enabled_expt,
        mock_pemreader,
        mock_resource,
    ):
        # Save any EXPORTER env var for later
        old_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_metrics_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]

        # Mock entry points
        mock_exporter_class = mocker.MagicMock()
        mock_exporter_entry_point = mocker.Mock()
        mock_exporter_entry_point.configure_mock(
            **{
                "load": mock_exporter_class
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
                "OTEL_METRICS_EXPORTER": "valid_exporter"
            }
        )

        # Mock Otel
        mock_metrics, mock_set_meter_provider, mock_meter_provider = get_metrics_mocks(mocker)

        mock_trace, mock_get_tracer_provider, mock_add_span_processor, mock_tracer = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_metrics_exporter(
            mock_apmconfig_enabled_expt,
        )
        mock_pemreader.assert_called_once()
        mock_get_tracer_provider.assert_called_once()
        mock_tracer.assert_called_once()
        mock_set_meter_provider.assert_called_once()
        mock_meter_provider.assert_called_once()

        # Restore old EXPORTER
        if old_metrics_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_metrics_exporter
