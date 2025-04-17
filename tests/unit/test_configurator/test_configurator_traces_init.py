# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from solarwinds_apm import configurator
from solarwinds_apm.exporter import SolarWindsSpanExporter

class TestConfiguratorTracingInit:
    def setup_each_test(
        self,
        mocker,
        mock_apmconfig,
        exporters=None,
        otlp_protocol=None,
        otlp_traces_protocol=None,
    ):
        env_vars = {}
        if otlp_protocol:
            env_vars["OTEL_EXPORTER_OTLP_PROTOCOL"] = otlp_protocol
        if otlp_traces_protocol:
            env_vars["OTEL_EXPORTER_OTLP_TRACES_PROTOCOL"] = otlp_traces_protocol
        mocker.patch.dict(os.environ, env_vars, clear=True)

        mocker.patch(
            "solarwinds_apm.configurator.SolarWindsApmConfig",
            return_value=mock_apmconfig,
        )

        # Mock Otel components
        mock_tracerprovider = mocker.Mock()
        mock_tracerprovider_instance = mocker.Mock()
        mock_tracerprovider.return_value = mock_tracerprovider_instance
        mocker.patch(
            "solarwinds_apm.configurator.SolarwindsTracerProvider",
            new=mock_tracerprovider,
        )
        mock_set_tracer_provider = mocker.patch(
            "solarwinds_apm.configurator.set_tracer_provider",
        )
        mock_apm_sampler = mocker.Mock()
        mock_resource = mocker.Mock()

        return {
            "mock_tracerprovider": mock_tracerprovider,
            "mock_tracerprovider_instance": mock_tracerprovider_instance,
            "mock_set_tracer_provider": mock_set_tracer_provider,
            "mock_apm_sampler": mock_apm_sampler,
            "mock_resource": mock_resource,
        }

    def test_custom_init_tracing_none(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_bsprocessor,
        mock_ssprocessor,
    ):
        mocks = self.setup_each_test(
            mocker,
            mock_apmconfig_enabled,
        )

        # Test
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._custom_init_tracing(
            exporters={},
            id_generator=None,
            sampler=mocks["mock_apm_sampler"],
            resource=mocks["mock_resource"],
        )

        mocks["mock_tracerprovider"].assert_called_once_with(
            id_generator=None,
            sampler=mocks["mock_apm_sampler"],
            resource=mocks["mock_resource"],
        )
        mocks["mock_set_tracer_provider"].assert_called_once()
        mocks["mock_tracerprovider_instance"].add_span_processor.assert_not_called()
        mock_bsprocessor.assert_not_called()
        mock_ssprocessor.assert_not_called()

    def test_custom_init_tracing_not_is_lambda(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_bsprocessor,
        mock_ssprocessor,
    ):
        mocks = self.setup_each_test(
            mocker,
            mock_apmconfig_enabled,
        )

        # Mock span exporter class
        class MockExporter():
            def __init__(self, *args, **kwargs):
                pass

        # Spy on MockExporter
        mock_exporter_spy = mocker.spy(MockExporter, "__init__")

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._custom_init_tracing(
            exporters={"valid_exporter": MockExporter},
            id_generator=None,
            sampler=mocks["mock_apm_sampler"],
            resource=mocks["mock_apm_sampler"],
        )
        mocks["mock_tracerprovider"].assert_called_once_with(
            id_generator=None,
            sampler=mocks["mock_apm_sampler"],
            resource=mocks["mock_apm_sampler"],
        )
        mocks["mock_set_tracer_provider"].assert_called_once()
        mocks["mock_tracerprovider_instance"].add_span_processor.assert_called_once_with(
            mock_bsprocessor.return_value,
        )
        mock_exporter_spy.assert_called_once()
        mock_bsprocessor.assert_called_once()
        mock_ssprocessor.assert_not_called()

    def test_custom_init_tracing_is_lambda(
        self,
        mocker,
        mock_apmconfig_enabled_is_lambda,
        mock_bsprocessor,
        mock_ssprocessor,
    ):
        mocks = self.setup_each_test(
            mocker,
            mock_apmconfig_enabled_is_lambda,
        )

        # Mock span exporter class
        class MockExporter():
            def __init__(self, *args, **kwargs):
                pass

        # Spy on MockExporter
        mock_exporter_spy = mocker.spy(MockExporter, "__init__")

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._custom_init_tracing(
            exporters={"valid_exporter": MockExporter},
            id_generator=None,
            sampler=mocks["mock_apm_sampler"],
            resource=mocks["mock_resource"],
        )
        mocks["mock_tracerprovider"].assert_called_once_with(
            id_generator=None,
            sampler=mocks["mock_apm_sampler"],
            resource=mocks["mock_resource"],
        )
        mocks["mock_set_tracer_provider"].assert_called_once()
        mocks["mock_tracerprovider_instance"].add_span_processor.assert_called_once_with(
            mock_ssprocessor.return_value,
        )
        mock_exporter_spy.assert_called_once()
        mock_ssprocessor.assert_called_once()
        mock_bsprocessor.assert_not_called()
