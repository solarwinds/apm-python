# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm import configurator

# otel fixtures
from .fixtures.trace import get_trace_mocks


class TestConfiguratorSpanProcessors:
    def test_configure_inbound_metrics_span_processor(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_txn_name_manager,
    ):
        trace_mocks = get_trace_mocks(mocker)
        mock_processor = mocker.patch(
            "solarwinds_apm.configurator.SolarWindsInboundMetricsSpanProcessor"
        )

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_inbound_metrics_span_processor(
            mock_txn_name_manager,
            mock_apmconfig_enabled,
        )       
        trace_mocks.get_tracer_provider.assert_called_once()
        trace_mocks.get_tracer_provider().add_span_processor.assert_called_once()
        mock_processor.assert_called_once_with(
            mock_txn_name_manager,
            mock_apmconfig_enabled,
        ) 

    def test_configure_otlp_metrics_span_processor_missing_flag(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_txn_name_manager,
        mock_meter_manager,
    ):
        trace_mocks = get_trace_mocks(mocker)
        mock_processor = mocker.patch(
            "solarwinds_apm.configurator.SolarWindsOTLPMetricsSpanProcessor"
        )

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_otlp_metrics_span_processor(
            mock_txn_name_manager,
            mock_apmconfig_enabled,
            mock_meter_manager,
        )       
        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().add_span_processor.assert_not_called()
        mock_processor.assert_not_called()

    def test_configure_otlp_metrics_span_processor(
        self,
        mocker,
        mock_apmconfig_enabled_expt,
        mock_txn_name_manager,
        mock_meter_manager,
    ):
        trace_mocks = get_trace_mocks(mocker)
        mock_processor = mocker.patch(
            "solarwinds_apm.configurator.SolarWindsOTLPMetricsSpanProcessor"
        )

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_otlp_metrics_span_processor(
            mock_txn_name_manager,
            mock_apmconfig_enabled_expt,
            mock_meter_manager,
        )
        trace_mocks.get_tracer_provider.assert_called_once()
        trace_mocks.get_tracer_provider().add_span_processor.assert_called_once()
        mock_processor.assert_called_once_with(
            mock_txn_name_manager,
            mock_apmconfig_enabled_expt,
            mock_meter_manager,
        ) 