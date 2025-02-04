# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import math
import os
import pytest

from solarwinds_apm import configurator

# otel fixtures
from .fixtures.resource import get_resource_mocks
from .fixtures.trace import get_trace_mocks


class TestConfiguratorMetricsExporter:
    def test_configure_metrics_exporter_sw_enabled_false(
        self,
        mocker,
        mock_apmconfig_metrics_enabled_false,
        mock_pemreader,
        mock_meterprovider,
    ):
        # Mock Otel
        trace_mocks = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_metrics_exporter(
            mock_apmconfig_metrics_enabled_false,
        )
        mock_pemreader.assert_not_called()
        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_meterprovider.assert_not_called()

    def test_configure_metrics_exporter_sw_enabled_none(
        self,
        mocker,
        mock_apmconfig_metrics_enabled_none,
        mock_pemreader,
        mock_meterprovider,
    ):
        # Mock Otel
        trace_mocks = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_metrics_exporter(
            mock_apmconfig_metrics_enabled_none,
        )
        mock_pemreader.assert_not_called()
        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_meterprovider.assert_not_called()

    def test_configure_metrics_exporter_none(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_pemreader,
        mock_meterprovider,
    ):
        # Save any EXPORTER env var for later
        old_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_metrics_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]

        # Mock Otel
        trace_mocks = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_metrics_exporter(
            mock_apmconfig_enabled,
        )
        mock_pemreader.assert_not_called()
        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_meterprovider.assert_not_called()

        # Restore old EXPORTER
        if old_metrics_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_metrics_exporter

    def test_configure_metrics_exporter_invalid(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_pemreader,
        mock_meterprovider,
    ):
        # Save any EXPORTER env var for later
        old_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_metrics_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]

        # Mock entry points
        mock_entry_points = mocker.patch(
            "solarwinds_apm.apm_config.entry_points"
        )
        mock_entry_points.configure_mock(
            side_effect=StopIteration("mock error")
        )
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_METRICS_EXPORTER": "invalid_exporter"
            }
        )

        # Mock Otel
        get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        with pytest.raises(Exception):
            test_configurator._configure_metrics_exporter(
                mock_apmconfig_enabled,
            )
        
        mock_pemreader.assert_not_called()
        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_meterprovider.assert_not_called()

        # Restore old EXPORTER
        if old_metrics_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_metrics_exporter

    def test_configure_metrics_exporter_valid(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_pemreader,
        mock_meterprovider,
    ):
        # Save any EXPORTER env var for later
        old_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_metrics_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]

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
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(
            return_value=mock_points
        )
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_METRICS_EXPORTER": "valid_exporter"
            }
        )

        # Mock Otel
        get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)
        mock_histogram = mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_metrics_exporter(
            mock_apmconfig_enabled,
        )
        mock_exporter_entry_point.load.assert_called_once()
        mock_exporter_entry_point.load.assert_has_calls(
            [
                mocker.call(),
                mocker.call()(
                    preferred_temporality={
                        mock_histogram: "foo-delta"
                    }
                )
            ]
        )
        mock_pemreader.assert_called_once()
        mock_pemreader.assert_has_calls(
            [
                mocker.call(
                    mock_exporter,
                )
            ]
        )
        trace_mocks.get_tracer_provider.assert_called_once()
        trace_mocks.get_tracer_provider().get_tracer.assert_called_once()
        mock_meterprovider.assert_called_once()

        # Restore old EXPORTER
        if old_metrics_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_metrics_exporter

    def test_configure_metrics_exporter_valid_is_lambda(
        self,
        mocker,
        mock_apmconfig_enabled_is_lambda,
        mock_pemreader,
        mock_meterprovider,
    ):
        # Save any EXPORTER env var for later
        old_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_metrics_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]

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
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(
            return_value=mock_points
        )
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_METRICS_EXPORTER": "valid_exporter"
            }
        )

        # Mock Otel
        get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)
        mock_histogram = mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_metrics_exporter(
            mock_apmconfig_enabled_is_lambda,
        )
        mock_exporter_entry_point.load.assert_called_once()
        mock_exporter_entry_point.load.assert_has_calls(
            [
                mocker.call(),
                mocker.call()(
                    preferred_temporality={
                        mock_histogram: "foo-delta"
                    }
                )
            ]
        )
        mock_pemreader.assert_called_once()
        mock_pemreader.assert_has_calls(
            [
                mocker.call(
                    mock_exporter,
                    export_interval_millis=math.inf,
                )
            ]
        )
        trace_mocks.get_tracer_provider.assert_called_once()
        trace_mocks.get_tracer_provider().get_tracer.assert_called_once()
        mock_meterprovider.assert_called_once()

        # Restore old EXPORTER
        if old_metrics_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_metrics_exporter

    def test_configure_metrics_exporter_invalid_valid_mixed(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_pemreader,
        mock_meterprovider,
    ):
        # Save any EXPORTER env var for later
        old_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_metrics_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]

        # Mock entry points
        mock_exporter_entry_point = mocker.Mock()
        mock_exporter_class_invalid = mocker.Mock()
        mock_exporter_class_invalid.configure_mock(
            side_effect=Exception("mock error invalid exporter")
        )
        mock_exporter_entry_point_invalid = mocker.Mock()
        mock_exporter_entry_point_invalid.configure_mock(
            **{
                "load": mock_exporter_class_invalid
            }
        )
        mock_points = iter(
            [
                mock_exporter_entry_point_invalid,
                mock_exporter_entry_point,
            ]
        )
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(
            return_value=mock_points
        )
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_METRICS_EXPORTER": "invalid_exporter,valid_exporter"
            }
        )

        # Mock Otel
        get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)
        mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        with pytest.raises(Exception):
            test_configurator._configure_metrics_exporter(
                mock_apmconfig_enabled,
            )
        # Only called once before exception
        mock_entry_points.assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_metrics_exporter",
                    name="invalid_exporter",
                ),
            ]
        )
        mock_exporter_entry_point_invalid.load.assert_has_calls(
            [
                mocker.call(),
            ]
        )
        # Not called at all
        mock_pemreader.assert_not_called()
        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_meterprovider.assert_not_called()

        # Restore old EXPORTER
        if old_metrics_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_metrics_exporter

    def test_configure_metrics_exporter_valid_invalid_mixed(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_pemreader,
        mock_meterprovider,
    ):
        # Save any EXPORTER env var for later
        old_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_metrics_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]

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
        mock_exporter_class_invalid = mocker.Mock()
        mock_exporter_class_invalid.configure_mock(
            side_effect=Exception("mock error invalid exporter")
        )
        mock_exporter_entry_point_invalid = mocker.Mock()
        mock_exporter_entry_point_invalid.configure_mock(
            **{
                "load": mock_exporter_class_invalid
            }
        )

        mock_points = iter(
            [
                mock_exporter_entry_point,
                mock_exporter_entry_point_invalid,
            ]
        )
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(
            return_value=mock_points
        )
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_METRICS_EXPORTER": "valid_exporter,invalid_exporter"
            }
        )

        # Mock Otel
        get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)
        mock_histogram = mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        with pytest.raises(Exception):
            test_configurator._configure_metrics_exporter(
                mock_apmconfig_enabled,
            )
        mock_entry_points.assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_metrics_exporter",
                    name="valid_exporter",
                ),
                mocker.call(
                    group="opentelemetry_metrics_exporter",
                    name="invalid_exporter",
                ),
            ]
        )
        mock_exporter_entry_point.load.assert_called_once()
        mock_exporter_entry_point.load.assert_has_calls(
            [
                mocker.call(),
                mocker.call()(
                    preferred_temporality={
                        mock_histogram: "foo-delta"
                    }
                )
            ]
        )
        mock_exporter_entry_point_invalid.load.assert_called_once()
        mock_exporter_entry_point_invalid.load.assert_has_calls(
            [
                mocker.call(),
            ]
        )
        # Called for the valid one
        mock_pemreader.assert_called_once()
        mock_pemreader.assert_has_calls(
            [
                mocker.call(
                    mock_exporter,
                )
            ]
        )
        # Rest not called at all
        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_meterprovider.assert_not_called()

        # Restore old EXPORTER
        if old_metrics_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_metrics_exporter

    def test_configure_metrics_exporter_valid_invalid_mixed_is_lambda(
        self,
        mocker,
        mock_apmconfig_enabled_is_lambda,
        mock_pemreader,
        mock_meterprovider,
    ):
        # Save any EXPORTER env var for later
        old_metrics_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_metrics_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]

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
        mock_exporter_class_invalid = mocker.Mock()
        mock_exporter_class_invalid.configure_mock(
            side_effect=Exception("mock error invalid exporter")
        )
        mock_exporter_entry_point_invalid = mocker.Mock()
        mock_exporter_entry_point_invalid.configure_mock(
            **{
                "load": mock_exporter_class_invalid
            }
        )

        mock_points = iter(
            [
                mock_exporter_entry_point,
                mock_exporter_entry_point_invalid,
            ]
        )
        mock_entry_points = mocker.patch(
            "solarwinds_apm.configurator.entry_points"
        )
        mock_entry_points.configure_mock(
            return_value=mock_points
        )
        mocker.patch.dict(
            os.environ,
            {
                "OTEL_METRICS_EXPORTER": "valid_exporter,invalid_exporter"
            }
        )

        # Mock Otel
        get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)
        mock_histogram = mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        with pytest.raises(Exception):
            test_configurator._configure_metrics_exporter(
                mock_apmconfig_enabled_is_lambda,
            )
        mock_entry_points.assert_has_calls(
            [
                mocker.call(
                    group="opentelemetry_metrics_exporter",
                    name="valid_exporter",
                ),
                mocker.call(
                    group="opentelemetry_metrics_exporter",
                    name="invalid_exporter",
                ),
            ]
        )
        mock_exporter_entry_point.load.assert_called_once()
        mock_exporter_entry_point.load.assert_has_calls(
            [
                mocker.call(),
                mocker.call()(
                    preferred_temporality={
                        mock_histogram: "foo-delta"
                    }
                )
            ]
        )
        mock_exporter_entry_point_invalid.load.assert_called_once()
        mock_exporter_entry_point_invalid.load.assert_has_calls(
            [
                mocker.call(),
            ]
        )
        # Called for the valid one
        mock_pemreader.assert_called_once()
        mock_pemreader.assert_has_calls(
            [
                mocker.call(
                    mock_exporter,
                    export_interval_millis=math.inf,
                )
            ]
        )
        # Rest not called at all
        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().get_tracer.assert_not_called()
        mock_meterprovider.assert_not_called()

        # Restore old EXPORTER
        if old_metrics_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_metrics_exporter