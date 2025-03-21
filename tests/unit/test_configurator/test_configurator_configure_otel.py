# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from opentelemetry.sdk.environment_variables import (
    _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED,
)

from solarwinds_apm import configurator

class TestConfiguratorConfigureOtelComponents:
    def helper_test_configure_otel_components_logs_enabled(
        self,
        mocker,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_meter_manager,
        mock_extension,
        mock_apmconfig_enabled,
        mock_oboe_api_obj,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_config_otlp_processors,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_logs_handler,
        mock_config_propagator,
        mock_config_response_propagator,

        logging_env,
        logging_assert,
    ):
        mocker.patch.dict(
            os.environ,
            {
                _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: logging_env,
            }
        )
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_otel_components(
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_apmconfig_enabled,
            mock_extension.Reporter,
            mock_oboe_api_obj,
        )

        mock_config_serviceentryid_processor.assert_called_once()
        mock_config_inbound_processor.assert_called_once()
        mock_config_otlp_processors.assert_called_once_with(
            mock_txn_name_manager,
            mock_apmconfig_enabled, 
            mock_oboe_api_obj,
        )
        mock_config_traces_exp.assert_called_once_with(
            mock_extension.Reporter,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_apmconfig_enabled,
        )
        mock_config_metrics_exp.assert_called_once_with(mock_apmconfig_enabled)
        mock_config_logs_exp.assert_called_once_with(mock_apmconfig_enabled)
        if logging_assert:
            mock_config_logs_handler.assert_called_once()
        else:
            mock_config_logs_handler.assert_not_called()
        mock_config_propagator.assert_called_once()
        mock_config_response_propagator.assert_called_once()

    def test_configure_otel_components_logs_enabled_true_by_otel_sw_default(
        self,
        mocker,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_meter_manager,
        mock_extension,
        mock_apmconfig_enabled_export_logs_false,
        mock_oboe_api_obj,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_config_otlp_processors,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_logs_handler,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_meter_manager,
            mock_extension,
            mock_apmconfig_enabled_export_logs_false,
            mock_oboe_api_obj,
            mock_config_serviceentryid_processor,
            mock_config_inbound_processor,
            mock_config_otlp_processors,
            mock_config_traces_exp,
            mock_config_metrics_exp,
            mock_config_logs_exp,
            mock_config_logs_handler,
            mock_config_propagator,
            mock_config_response_propagator,
            "true",
            True,
        )

    def test_configure_otel_components_logs_enabled_otel_none_sw_default(self,
        mocker,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_meter_manager,
        mock_extension,
        mock_apmconfig_enabled_export_logs_false,
        mock_oboe_api_obj,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_config_otlp_processors,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_logs_handler,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_meter_manager,
            mock_extension,
            mock_apmconfig_enabled_export_logs_false,
            mock_oboe_api_obj,
            mock_config_serviceentryid_processor,
            mock_config_inbound_processor,
            mock_config_otlp_processors,
            mock_config_traces_exp,
            mock_config_metrics_exp,
            mock_config_logs_exp,
            mock_config_logs_handler,
            mock_config_propagator,
            mock_config_response_propagator,
            "",
            False,
        )

    def test_configure_otel_components_logs_enabled_otel_none_sw_true(self,
        mocker,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_meter_manager,
        mock_extension,
        mock_apmconfig_enabled,
        mock_oboe_api_obj,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_config_otlp_processors,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_logs_handler,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_meter_manager,
            mock_extension,
            mock_apmconfig_enabled,
            mock_oboe_api_obj,
            mock_config_serviceentryid_processor,
            mock_config_inbound_processor,
            mock_config_otlp_processors,
            mock_config_traces_exp,
            mock_config_metrics_exp,
            mock_config_logs_exp,
            mock_config_logs_handler,
            mock_config_propagator,
            mock_config_response_propagator,
            "",
            True,  # true because SW next in precedence
        )

    def test_configure_otel_components_logs_enabled_otel_false_sw_default(self,
        mocker,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_meter_manager,
        mock_extension,
        mock_apmconfig_enabled_export_logs_false,
        mock_oboe_api_obj,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_config_otlp_processors,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_logs_handler,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_meter_manager,
            mock_extension,
            mock_apmconfig_enabled_export_logs_false,
            mock_oboe_api_obj,
            mock_config_serviceentryid_processor,
            mock_config_inbound_processor,
            mock_config_otlp_processors,
            mock_config_traces_exp,
            mock_config_metrics_exp,
            mock_config_logs_exp,
            mock_config_logs_handler,
            mock_config_propagator,
            mock_config_response_propagator,
            "false",
            False,
        )

    def test_configure_otel_components_logs_enabled_otel_false_sw_true(self,
        mocker,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_meter_manager,
        mock_extension,
        mock_apmconfig_enabled,
        mock_oboe_api_obj,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_config_otlp_processors,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_logs_handler,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_meter_manager,
            mock_extension,
            mock_apmconfig_enabled,
            mock_oboe_api_obj,
            mock_config_serviceentryid_processor,
            mock_config_inbound_processor,
            mock_config_otlp_processors,
            mock_config_traces_exp,
            mock_config_metrics_exp,
            mock_config_logs_exp,
            mock_config_logs_handler,
            mock_config_propagator,
            mock_config_response_propagator,
            "false",
            False,  # should be false because OTEL explicitly false, even if SW true
        )

    def test_configure_otel_components_logs_enabled_otel_invalid(self,
        mocker,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_meter_manager,
        mock_extension,
        mock_apmconfig_enabled_export_logs_false,
        mock_oboe_api_obj,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_config_otlp_processors,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_logs_handler,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_meter_manager,
            mock_extension,
            mock_apmconfig_enabled_export_logs_false,
            mock_oboe_api_obj,
            mock_config_serviceentryid_processor,
            mock_config_inbound_processor,
            mock_config_otlp_processors,
            mock_config_traces_exp,
            mock_config_metrics_exp,
            mock_config_logs_exp,
            mock_config_logs_handler,
            mock_config_propagator,
            mock_config_response_propagator,
            "not-a-bool-string",
            False,
        )

    def test_configure_otel_components_agent_enabled(
        self,
        mocker,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_meter_manager,
        mock_extension,
        mock_apmconfig_enabled,
        mock_oboe_api_obj,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_config_otlp_processors,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_logs_handler,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_otel_components(
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_apmconfig_enabled,
            mock_extension.Reporter,
            mock_oboe_api_obj,
        )

        mock_config_serviceentryid_processor.assert_called_once()
        mock_config_inbound_processor.assert_called_once_with(
            mock_txn_name_manager,
            mock_apmconfig_enabled,
        )
        mock_config_otlp_processors.assert_called_once_with(
            mock_txn_name_manager,
            mock_apmconfig_enabled, 
            mock_oboe_api_obj,
        )
        mock_config_traces_exp.assert_called_once_with(
            mock_extension.Reporter,
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_apmconfig_enabled,
        )
        mock_config_metrics_exp.assert_called_once_with(mock_apmconfig_enabled)
        mock_config_logs_exp.assert_called_once_with(mock_apmconfig_enabled)
        mock_config_logs_handler.assert_called_once()
        mock_config_propagator.assert_called_once()
        mock_config_response_propagator.assert_called_once()

    def test_configure_otel_components_agent_disabled(
        self,
        mocker,
        mock_txn_name_manager,
        mock_fwkv_manager,
        mock_meter_manager,
        mock_extension,
        mock_apmconfig_disabled,
        mock_oboe_api_obj,

        mock_config_serviceentryid_processor,
        mock_config_inbound_processor,
        mock_config_otlp_processors,
        mock_config_traces_exp,
        mock_config_metrics_exp,
        mock_config_logs_exp,
        mock_config_logs_handler,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_otel_components(
            mock_txn_name_manager,
            mock_fwkv_manager,
            mock_apmconfig_disabled,
            mock_extension.Reporter,
            mock_oboe_api_obj,
        )

        mock_config_serviceentryid_processor.assert_not_called()
        mock_config_inbound_processor.assert_not_called()
        mock_config_otlp_processors.assert_not_called()
        mock_config_traces_exp.assert_not_called()
        mock_config_metrics_exp.assert_not_called()
        mock_config_logs_exp.assert_not_called()
        mock_config_logs_handler.assert_not_called()
        mock_config_propagator.assert_not_called()
        mock_config_response_propagator.assert_not_called()