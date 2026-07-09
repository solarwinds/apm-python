# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import pytest


from solarwinds_apm import configurator


@pytest.fixture
def setup_caplog():
    apm_logger = logging.getLogger("solarwinds_apm")
    apm_logger.propagate = True


class TestConfiguratorConfigureOtelComponents:
    def test_configure_otel_components_agent_enabled(
        self,
        mocker,
        mock_apmconfig_enabled,

        mock_config_serviceentry_processor,
        mock_response_time_processor,
        mock_custom_init_tracing,
        mock_custom_init_metrics,
        mock_init_logging,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        mock_resource = mocker.Mock()
        mock_apmconfig_enabled.resource = mock_resource
        mock_detector_resource = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.apm_resource.create_detector_resource",
            return_value=mock_detector_resource,
        )
        
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig",
            return_value=mock_apmconfig_enabled,
        )
        mock_apm_sampler = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.configurator.ParentBasedSwSampler",
            return_value=mock_apm_sampler,
        )
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure()

        mock_config_serviceentry_processor.assert_called_once()
        mock_response_time_processor.assert_called_once_with()
        mock_custom_init_tracing.assert_called_once_with(
            exporters={},
            id_generator=None,
            sampler=mock_apm_sampler,
            resource=mock_resource,
        )
        mock_custom_init_metrics.assert_called_once_with(
            exporters_or_readers={},
            resource=mock_resource,
        )
        # Always passes False since logging auto-instrumentation is now handled by
        # opentelemetry-instrumentation-logging via the distro
        mock_init_logging.assert_called_once_with(
            {},
            mock_resource,
            setup_logging_handler=False,
        )
        mock_config_propagator.assert_called_once()
        mock_config_response_propagator.assert_called_once()

    def test_configure_otel_components_agent_disabled(
        self,
        mocker,
        mock_apmconfig_disabled,

        mock_config_serviceentry_processor,
        mock_response_time_processor,
        mock_custom_init_tracing,
        mock_custom_init_metrics,
        mock_init_logging,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        mock_detector_resource = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.apm_resource.create_detector_resource",
            return_value=mock_detector_resource,
        )
        mock_apm_sampler = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.configurator.ParentBasedSwSampler",
            return_value=mock_apm_sampler,
        )
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig",
            return_value=mock_apmconfig_disabled,
        )
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure()

        mock_apm_sampler.assert_not_called()
        mock_config_serviceentry_processor.assert_not_called()
        mock_response_time_processor.assert_not_called()
        mock_custom_init_tracing.assert_not_called()
        mock_custom_init_metrics.assert_not_called()
        mock_init_logging.assert_not_called()
        mock_config_propagator.assert_not_called()
        mock_config_response_propagator.assert_not_called()