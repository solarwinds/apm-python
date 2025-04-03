# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm import configurator

class TestConfiguratorConfigureOtelComponents:
    def test_configure_otel_components_agent_enabled(
        self,
        mocker,
        mock_fwkv_manager,
        mock_apmconfig_enabled,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_response_time_processor,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_otel_components(
            mock_fwkv_manager,
            mock_apmconfig_enabled,
        )

        # mock_config_serviceentryid_processor.assert_called_once()
        # mock_config_inbound_processor.assert_called_once_with(
        #     mock_apmconfig_enabled,
        # )
        # mock_response_time_processor.assert_called_once_with(
        #     mock_apmconfig_enabled,
        # )
        # mock_config_traces_exp.assert_called_once_with(
        #     mock_fwkv_manager,
        #     mock_apmconfig_enabled,
        # )
        # mock_config_metrics_exp.assert_called_once_with(mock_apmconfig_enabled)
        # mock_config_logs_exp.assert_called_once_with(mock_apmconfig_enabled)
        # mock_config_propagator.assert_called_once()
        # mock_config_response_propagator.assert_called_once()

    def test_configure_otel_components_agent_disabled(
        self,
        mocker,
        mock_fwkv_manager,
        mock_extension,
        mock_apmconfig_disabled,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_response_time_processor,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_otel_components(
            mock_fwkv_manager,
            mock_apmconfig_disabled,
            mock_extension.Reporter,
        )

        mock_config_serviceentryid_processor.assert_not_called()
        mock_config_inbound_processor.assert_not_called()
        mock_response_time_processor.assert_not_called()
        mock_config_traces_exp.assert_not_called()
        mock_config_metrics_exp.assert_not_called()
        mock_config_logs_exp.assert_not_called()
        mock_config_propagator.assert_not_called()
        mock_config_response_propagator.assert_not_called()