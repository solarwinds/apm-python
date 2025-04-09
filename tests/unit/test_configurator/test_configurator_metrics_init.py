# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import math
import os
import pytest

from opentelemetry.sdk.metrics.export import (
    MetricExporter,
    MetricReader,
)

from solarwinds_apm import configurator


class TestConfiguratorMetricsInit:
    def test_custom_init_metrics_none(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_pemreader,
        mock_meterprovider,
    ):
        # Mock Otel
        mock_resource = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.configurator.Resource.create",
            return_value=mock_resource,
        )

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._custom_init_metrics(
            exporters_or_readers={},
            resource=mock_resource,
        )
        mock_pemreader.assert_not_called()
        mock_meterprovider.assert_called_once_with(
            resource=mock_resource,
            metric_readers=[],
        )

    def test_custom_init_metrics_exporter_not_is_lambda(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_pemreader,
        mock_meterprovider,
    ):
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig",
            return_value=mock_apmconfig_enabled,
        )

        # Mock Otel
        mock_resource = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.configurator.Resource.create",
            return_value=mock_resource,
        )
        mock_counter = mocker.patch(
            "solarwinds_apm.configurator.Counter"
        )
        mock_updowncounter = mocker.patch(
            "solarwinds_apm.configurator.UpDownCounter"
        )
        mock_histogram = mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_observablecounter = mocker.patch(
            "solarwinds_apm.configurator.ObservableCounter"
        )
        mock_observableupdowncounter = mocker.patch(
            "solarwinds_apm.configurator.ObservableUpDownCounter"
        )
        mock_observablegauge = mocker.patch(
            "solarwinds_apm.configurator.ObservableGauge"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Mock metrics exporter class
        class MockExporter(MetricExporter):
            def __init__(self, *args, **kwargs):
                pass

            def export(self):
                pass
            
            def force_flush(self, *args, **kwargs):
                pass
            
            def shutdown(self, *args, **kwargs):
                pass

        # Spy on MockExporter
        mock_exporter_spy = mocker.spy(MockExporter, "__init__")

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._custom_init_metrics(
            exporters_or_readers={"valid_exporter": MockExporter},
            resource=mock_resource,
        )
        mock_exporter_spy.assert_called_once()
        _, kwargs = mock_exporter_spy.call_args
        assert "preferred_temporality" in kwargs
        assert kwargs["preferred_temporality"] == {
            mock_counter: mock_agg_temp.DELTA,
            mock_updowncounter: mock_agg_temp.DELTA,
            mock_histogram: mock_agg_temp.DELTA,
            mock_observablecounter: mock_agg_temp.DELTA,
            mock_observableupdowncounter: mock_agg_temp.DELTA,
            mock_observablegauge: mock_agg_temp.DELTA,
        }
        mock_pemreader.assert_called_once_with(
            mocker.ANY,  # Allow any instance of MockExporter
        )
        mock_meterprovider.assert_called_once_with(
            resource=mock_resource,
            metric_readers=[mock_pemreader.return_value],
        )

    def test_custom_init_metrics_exporter_is_lambda(
        self,
        mocker,
        mock_apmconfig_enabled_is_lambda,
        mock_pemreader,
        mock_meterprovider,
    ):
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig",
            return_value=mock_apmconfig_enabled_is_lambda,
        )

        # Mock Otel
        mock_resource = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.configurator.Resource.create",
            return_value=mock_resource,
        )
        mock_counter = mocker.patch(
            "solarwinds_apm.configurator.Counter"
        )
        mock_updowncounter = mocker.patch(
            "solarwinds_apm.configurator.UpDownCounter"
        )
        mock_histogram = mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_observablecounter = mocker.patch(
            "solarwinds_apm.configurator.ObservableCounter"
        )
        mock_observableupdowncounter = mocker.patch(
            "solarwinds_apm.configurator.ObservableUpDownCounter"
        )
        mock_observablegauge = mocker.patch(
            "solarwinds_apm.configurator.ObservableGauge"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Mock metrics exporter class
        class MockExporter(MetricExporter):
            def __init__(self, *args, **kwargs):
                pass

            def export(self):
                pass
            
            def force_flush(self, *args, **kwargs):
                pass
            
            def shutdown(self, *args, **kwargs):
                pass

        # Spy on MockExporter
        mock_exporter_spy = mocker.spy(MockExporter, "__init__")

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._custom_init_metrics(
            exporters_or_readers={"valid_exporter": MockExporter},
            resource=mock_resource,
        )
        mock_exporter_spy.assert_called_once()
        _, kwargs = mock_exporter_spy.call_args
        assert "preferred_temporality" in kwargs
        assert kwargs["preferred_temporality"] == {
            mock_counter: mock_agg_temp.DELTA,
            mock_updowncounter: mock_agg_temp.DELTA,
            mock_histogram: mock_agg_temp.DELTA,
            mock_observablecounter: mock_agg_temp.DELTA,
            mock_observableupdowncounter: mock_agg_temp.DELTA,
            mock_observablegauge: mock_agg_temp.DELTA,
        }
        mock_pemreader.assert_called_once_with(
            mocker.ANY,  # Allow any instance of MockExporter
            export_interval_millis=math.inf,
        )
        mock_meterprovider.assert_called_once_with(
            resource=mock_resource,
            metric_readers=[mock_pemreader.return_value],
        )

    def test_custom_init_metrics_reader_not_is_lambda(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_pemreader,
        mock_meterprovider,
    ):
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig",
            return_value=mock_apmconfig_enabled,
        )

        # Mock Otel
        mock_resource = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.configurator.Resource.create",
            return_value=mock_resource,
        )
        mock_counter = mocker.patch(
            "solarwinds_apm.configurator.Counter"
        )
        mock_updowncounter = mocker.patch(
            "solarwinds_apm.configurator.UpDownCounter"
        )
        mock_histogram = mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_observablecounter = mocker.patch(
            "solarwinds_apm.configurator.ObservableCounter"
        )
        mock_observableupdowncounter = mocker.patch(
            "solarwinds_apm.configurator.ObservableUpDownCounter"
        )
        mock_observablegauge = mocker.patch(
            "solarwinds_apm.configurator.ObservableGauge"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Mock metrics reader class
        class MockReader(MetricReader):
            def __init__(self, *args, **kwargs):
                pass

            def _receive_metrics(self, *args, **kwargs):
                pass

            def shutdown(self, *args, **kwargs):
                pass

        # Spy on MockReader
        mock_reader_spy = mocker.spy(MockReader, "__init__")

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._custom_init_metrics(
            exporters_or_readers={"valid_reader": MockReader},
            resource=mock_resource,
        )
        mock_reader_spy.assert_called_once()
        _, kwargs = mock_reader_spy.call_args
        assert "preferred_temporality" in kwargs
        assert kwargs["preferred_temporality"] == {
            mock_counter: mock_agg_temp.DELTA,
            mock_updowncounter: mock_agg_temp.DELTA,
            mock_histogram: mock_agg_temp.DELTA,
            mock_observablecounter: mock_agg_temp.DELTA,
            mock_observableupdowncounter: mock_agg_temp.DELTA,
            mock_observablegauge: mock_agg_temp.DELTA,
        }
        mock_pemreader.assert_not_called()
        mock_meterprovider.assert_called_once()
        args, kwargs = mock_meterprovider.call_args
        metric_readers = kwargs["metric_readers"]
        assert len(metric_readers) == 1
        assert isinstance(metric_readers[0], MockReader)

    def test_custom_init_metrics_reader_is_lambda(
        self,
        mocker,
        mock_apmconfig_enabled_is_lambda,
        mock_pemreader,
        mock_meterprovider,
    ):
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig",
            return_value=mock_apmconfig_enabled_is_lambda,
        )

        # Mock Otel
        mock_resource = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.configurator.Resource.create",
            return_value=mock_resource,
        )
        mock_counter = mocker.patch(
            "solarwinds_apm.configurator.Counter"
        )
        mock_updowncounter = mocker.patch(
            "solarwinds_apm.configurator.UpDownCounter"
        )
        mock_histogram = mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_observablecounter = mocker.patch(
            "solarwinds_apm.configurator.ObservableCounter"
        )
        mock_observableupdowncounter = mocker.patch(
            "solarwinds_apm.configurator.ObservableUpDownCounter"
        )
        mock_observablegauge = mocker.patch(
            "solarwinds_apm.configurator.ObservableGauge"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Mock metrics reader class
        class MockReader(MetricReader):
            def __init__(self, *args, **kwargs):
                pass

            def _receive_metrics(self, *args, **kwargs):
                pass

            def shutdown(self, *args, **kwargs):
                pass

        # Spy on MockReader
        mock_reader_spy = mocker.spy(MockReader, "__init__")

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._custom_init_metrics(
            exporters_or_readers={"valid_reader": MockReader},
            resource=mock_resource,
        )
        mock_reader_spy.assert_called_once()
        _, kwargs = mock_reader_spy.call_args
        assert "preferred_temporality" in kwargs
        assert kwargs["preferred_temporality"] == {
            mock_counter: mock_agg_temp.DELTA,
            mock_updowncounter: mock_agg_temp.DELTA,
            mock_histogram: mock_agg_temp.DELTA,
            mock_observablecounter: mock_agg_temp.DELTA,
            mock_observableupdowncounter: mock_agg_temp.DELTA,
            mock_observablegauge: mock_agg_temp.DELTA,
        }
        mock_pemreader.assert_not_called()
        mock_meterprovider.assert_called_once()
        args, kwargs = mock_meterprovider.call_args
        metric_readers = kwargs["metric_readers"]
        assert len(metric_readers) == 1
        assert isinstance(metric_readers[0], MockReader)
