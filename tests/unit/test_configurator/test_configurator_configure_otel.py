# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import os
import pytest
import uuid

from opentelemetry.sdk.environment_variables import (
    _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED,
)
from opentelemetry.sdk.resources import Resource

from solarwinds_apm import configurator


@pytest.fixture
def setup_caplog():
    apm_logger = logging.getLogger("solarwinds_apm")
    apm_logger.propagate = True


class TestConfiguratorCreateApmResource:
    def test_create_apm_resource_basic(self, mocker, mock_apmconfig_enabled):
        mocker.patch(
            "solarwinds_apm.configurator.__version__",
            new="1.2.3",
        )
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator.apm_config = mock_apmconfig_enabled
        result = test_configurator._create_apm_resource()

        assert result.attributes["sw.apm.version"] == "1.2.3"
        assert result.attributes["sw.data.module"] == "apm"
        assert result.attributes["service.name"] == "foo-service"
        assert "service.instance.id" in result.attributes
        instance_id = result.attributes["service.instance.id"]
        assert isinstance(instance_id, str)
        # Should not raise ValueError if valid UUID
        uuid.UUID(instance_id)

    def test_create_apm_resource_with_existing_instance_id_use_existing(self, mocker, mock_apmconfig_enabled):
        mocker.patch(
            "solarwinds_apm.configurator.__version__",
            new="1.2.3",
        )
        existing_instance_id = "existing-instance-id"
        # Mock return of Resource.create like a ResourceDetector set service.instance.id
        mock_initial_resource = Resource.create({
            "sw.apm.version": "1.2.3",
            "sw.data.module": "apm",
            "service.name": "foo-service",
            "service.instance.id": existing_instance_id,
        })
        mock_resource_create = mocker.patch(
            "solarwinds_apm.configurator.Resource.create",
            return_value=mock_initial_resource,
        )
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator.apm_config = mock_apmconfig_enabled
        result = test_configurator._create_apm_resource()

        assert result.attributes["service.instance.id"] == existing_instance_id
        mock_resource_create.assert_called_once_with({
            "sw.apm.version": "1.2.3",
            "sw.data.module": "apm",
            "service.name": "foo-service",
        })

    def test_create_apm_resource_without_existing_instance_id_generate_new(self, mocker, mock_apmconfig_enabled):
        mocker.patch(
            "solarwinds_apm.configurator.__version__",
            new="1.2.3",
        )
        mock_uuid = "test-uuid-value"
        mock_uuid4 = mocker.patch(
            "solarwinds_apm.configurator.uuid.uuid4",
            return_value=mock_uuid,
        )
        # Mock return of Resource.create like no resource detectors set instance ID
        mock_initial_resource = Resource.create({
            "sw.apm.version": "1.2.3",
            "sw.data.module": "apm",
            "service.name": "foo-service",
        })
        mocker.patch(
            "solarwinds_apm.configurator.Resource.create",
            return_value=mock_initial_resource,
        )
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator.apm_config = mock_apmconfig_enabled
        result = test_configurator._create_apm_resource()

        assert result.attributes["service.instance.id"] == str(mock_uuid)
        mock_uuid4.assert_called_once()


class TestConfiguratorConfigureOtelComponents:
    def helper_test_configure_otel_components_logs_enabled(
        self,
        mocker,
        mock_apmconfig_enabled,

        mock_config_serviceentry_processor,
        mock_custom_init_tracing,
        mock_custom_init_metrics,
        mock_init_logging,
        mock_config_propagator,
        mock_config_response_propagator,

        logging_env,
        logging_assert,
        mock_convert_to_bool=None,
    ):
        mocker.patch.dict(
            os.environ,
            {
                _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED: logging_env,
            }
        )
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig",
            return_value=mock_apmconfig_enabled,
        )
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig.convert_to_bool",
            return_value=mock_convert_to_bool,
        )
        mock_apm_sampler = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.configurator.ParentBasedSwSampler",
            return_value=mock_apm_sampler,
        )
        mock_resource = mocker.Mock()
        mocker.patch.object(
            configurator.SolarWindsConfigurator,
            "_create_apm_resource",
            return_value=mock_resource,
        )
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure()

        mock_config_serviceentry_processor.assert_called_once()
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
        mock_init_logging.assert_called_once_with(
            {},
            mock_resource,
            logging_assert,
        )
        mock_config_propagator.assert_called_once()
        mock_config_response_propagator.assert_called_once()

    def test_configure_otel_components_logs_enabled_true_by_otel_sw_default(
        self,
        caplog,
        setup_caplog,
        mocker,
        mock_apmconfig_enabled_export_logs_false,

        mock_config_serviceentry_processor,
        mock_custom_init_tracing,
        mock_custom_init_metrics,
        mock_init_logging,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_apmconfig_enabled_export_logs_false,
            mock_config_serviceentry_processor,
            mock_custom_init_tracing,
            mock_custom_init_metrics,
            mock_init_logging,
            mock_config_propagator,
            mock_config_response_propagator,
            "true",
            True,  # True because OTEL log instrumentation set to true
            True,
        )
        assert "Support for SW_APM_EXPORT_LOG_ENABLED / exportLogsEnabled has been dropped" not in caplog.text

    def test_configure_otel_components_logs_enabled_otel_none_sw_default(self,
        mocker,
        caplog,
        setup_caplog,
        mock_apmconfig_enabled_export_logs_false,

        mock_config_serviceentry_processor,
        mock_custom_init_tracing,
        mock_custom_init_metrics,
        mock_init_logging,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_apmconfig_enabled_export_logs_false,
            mock_config_serviceentry_processor,
            mock_custom_init_tracing,
            mock_custom_init_metrics,
            mock_init_logging,
            mock_config_propagator,
            mock_config_response_propagator,
            "",
            None,  # none because OTEL log instrumentation not set
        )
        assert "Support for SW_APM_EXPORT_LOG_ENABLED / exportLogsEnabled has been dropped" not in caplog.text

    def test_configure_otel_components_logs_enabled_otel_none_sw_true(self,
        caplog,
        setup_caplog,
        mocker,
        mock_apmconfig_enabled,

        mock_config_serviceentry_processor,
        mock_custom_init_tracing,
        mock_custom_init_metrics,
        mock_init_logging,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_apmconfig_enabled,
            mock_config_serviceentry_processor,
            mock_custom_init_tracing,
            mock_custom_init_metrics,
            mock_init_logging,
            mock_config_propagator,
            mock_config_response_propagator,
            "",
            None,  # none because OTEL log instrumentation not set
        )
        assert "Support for SW_APM_EXPORT_LOG_ENABLED / exportLogsEnabled has been dropped" in caplog.text

    def test_configure_otel_components_logs_enabled_otel_false_sw_default(self,
        mocker,
        caplog,
        setup_caplog,
        mock_apmconfig_enabled_export_logs_false,

        mock_config_serviceentry_processor,
        mock_custom_init_tracing,
        mock_custom_init_metrics,
        mock_init_logging,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_apmconfig_enabled_export_logs_false,
            mock_config_serviceentry_processor,
            mock_custom_init_tracing,
            mock_custom_init_metrics,
            mock_init_logging,
            mock_config_propagator,
            mock_config_response_propagator,
            "false",
            False,  # False because OTEL log instrumentation False
            False,
        )
        assert "Support for SW_APM_EXPORT_LOG_ENABLED / exportLogsEnabled has been dropped" not in caplog.text

    def test_configure_otel_components_logs_enabled_otel_false_sw_true(self,
        caplog,
        setup_caplog,
        mocker,
        mock_apmconfig_enabled,

        mock_config_serviceentry_processor,
        mock_custom_init_tracing,
        mock_custom_init_metrics,
        mock_init_logging,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_apmconfig_enabled,
            mock_config_serviceentry_processor,
            mock_custom_init_tracing,
            mock_custom_init_metrics,
            mock_init_logging,
            mock_config_propagator,
            mock_config_response_propagator,
            "false",
            False,  # should be false because OTEL explicitly false, even if SW true
            False,
        )
        assert "Support for SW_APM_EXPORT_LOG_ENABLED / exportLogsEnabled has been dropped" in caplog.text

    def test_configure_otel_components_logs_enabled_otel_invalid(self,
        mocker,
        caplog,
        setup_caplog,
        mock_apmconfig_enabled_export_logs_false,

        mock_config_serviceentry_processor,
        mock_custom_init_tracing,
        mock_custom_init_metrics,
        mock_init_logging,
        mock_config_propagator,
        mock_config_response_propagator,
    ):
        self.helper_test_configure_otel_components_logs_enabled(
            mocker,
            mock_apmconfig_enabled_export_logs_false,
            mock_config_serviceentry_processor,
            mock_custom_init_tracing,
            mock_custom_init_metrics,
            mock_init_logging,
            mock_config_propagator,
            mock_config_response_propagator,
            "not-a-bool-string",
            None,  # None because OTEL log instrumentation not valid bool
        )
        assert "Support for SW_APM_EXPORT_LOG_ENABLED / exportLogsEnabled has been dropped" not in caplog.text

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
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig",
            return_value=mock_apmconfig_enabled,
        )
        # Mock return of _OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig.convert_to_bool",
            return_value=False,
        )
        mock_apm_sampler = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.configurator.ParentBasedSwSampler",
            return_value=mock_apm_sampler,
        )
        mock_resource = mocker.Mock()
        mocker.patch.object(
            configurator.SolarWindsConfigurator,
            "_create_apm_resource",
            return_value=mock_resource,
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
        mock_init_logging.assert_called_once_with(
            {},
            mock_resource,
            False,
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
        mock_apm_sampler = mocker.Mock()
        mocker.patch(
            "solarwinds_apm.configurator.ParentBasedSwSampler",
            return_value=mock_apm_sampler,
        )
        mock_resource = mocker.Mock()
        mocker.patch.object(
            configurator.SolarWindsConfigurator,
            "_create_apm_resource",
            return_value=mock_resource,
        )
        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig",
            return_value=mock_apmconfig_disabled,
        )
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure()

        mock_apm_sampler.assert_not_called()
        mock_resource.assert_not_called()
        mock_config_serviceentry_processor.assert_not_called()
        mock_response_time_processor.assert_not_called()
        mock_custom_init_tracing.assert_not_called()
        mock_custom_init_metrics.assert_not_called()
        mock_init_logging.assert_not_called()
        mock_config_propagator.assert_not_called()
        mock_config_response_propagator.assert_not_called()