# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm import configurator

class TestConfiguratorConfigure:
    def test_configurator_configure(
        self,
        mocker,
        mock_txn_name_manager_init,
        mock_fwkv_manager_init,
        mock_apmconfig_enabled,
        mock_init_sw_reporter,
        mock_config_otel_components,
        mock_report_init,
    ):
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure()

        mock_txn_name_manager_init.assert_called_once()
        mock_fwkv_manager_init.assert_called_once()
        mock_apmconfig_enabled.assert_called_once()

        mock_init_sw_reporter.assert_called_once()
        mock_config_otel_components.assert_called_once()
        mock_report_init.assert_called_once()

    def test_configurator_configure_experimental(
        self,
        mocker,
        mock_txn_name_manager_init,
        mock_fwkv_manager_init,
        mock_apmconfig_experimental_otelcol_init,
        mock_init_sw_reporter,
        mock_config_otel_components,
        mock_report_init,
    ):
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure()

        mock_txn_name_manager_init.assert_called_once()
        mock_fwkv_manager_init.assert_called_once()
        mock_apmconfig_experimental_otelcol_init.assert_called_once()
        
        mock_init_sw_reporter.assert_called_once()
        mock_config_otel_components.assert_called_once()
        mock_report_init.assert_called_once()
