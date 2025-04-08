# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import math
import os
import pytest

from opentelemetry.sdk.trace.sampling import Sampler

from solarwinds_apm import configurator


class TestConfiguratorMetricsExporter:
    def test_configure_metrics_none(
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

    def test_configure_metrics_exporter_not_is_lambda(
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
        mock_histogram = mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Mock metrics exporter class
        class MockExporter(Sampler):
            def __init__(self, *args, **kwargs):
                pass

            def get_description(self):
                return "foo"
            
            def should_sample(self, *args, **kwargs):
                return "foo"

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._custom_init_metrics(
            exporters_or_readers={"valid_exporter": MockExporter},
            resource=mock_resource,
        )
        mock_pemreader.assert_called_once_with(
            mocker.ANY,  # Allow any instance of MockExporter
        )
        mock_meterprovider.assert_called_once()

    def test_configure_metrics_exporter_is_lambda(
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
        mock_histogram = mocker.patch(
            "solarwinds_apm.configurator.Histogram"
        )
        mock_agg_temp = mocker.patch(
            "solarwinds_apm.configurator.AggregationTemporality"
        )
        mock_agg_temp.DELTA = "foo-delta"

        # Mock metrics exporter class
        class MockExporter(Sampler):
            def __init__(self, *args, **kwargs):
                pass

            def get_description(self):
                return "foo"
            
            def should_sample(self, *args, **kwargs):
                return "foo"

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._custom_init_metrics(
            exporters_or_readers={"valid_exporter": MockExporter},
            resource=mock_resource,
        )
        mock_pemreader.assert_called_once_with(
            mocker.ANY,  # Allow any instance of MockExporter
            export_interval_millis=math.inf,
        )
        mock_meterprovider.assert_called_once()
