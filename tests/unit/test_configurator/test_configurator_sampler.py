# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

import pytest

from solarwinds_apm import configurator

# otel fixtures
from .fixtures.resource import get_resource_mocks
from .fixtures.trace import get_trace_mocks

class TestConfiguratorSampler:
    def test_configure_sampler_disabled(
        self,
        mocker,
        mock_apmconfig_disabled,
        mock_tracerprovider,
    ):
        # Mock Otel
        resource_mocks = get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_sampler(mock_apmconfig_disabled)

        # sets tracer_provider with noop
        trace_mocks["NoOpTracerProvider"].assert_called_once()
        trace_mocks["set_tracer_provider"].assert_called_once()
        
        # resource and real provider not used
        resource_mocks["create"].assert_not_called()
        mock_tracerprovider.assert_not_called()  

    def test_configure_sampler_error(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_tracerprovider,
    ):
        # Mock entry points
        mock_load_entry_point = mocker.patch(
            "solarwinds_apm.configurator.load_entry_point"
        )
        mock_load_entry_point.configure_mock(
            side_effect=Exception("mock error")
        )

        # Mock Otel
        resource_mocks = get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        with pytest.raises(Exception):
            test_configurator._configure_sampler(mock_apmconfig_enabled)

        # no tracer_provider is set
        trace_mocks["NoOpTracerProvider"].assert_not_called()
        trace_mocks["set_tracer_provider"].assert_not_called()
        resource_mocks["create"].assert_not_called()
        mock_tracerprovider.assert_not_called()  

    def test_configure_sampler_default(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_tracerprovider,
    ):
        # Mock entry points
        mock_load_entry_point = mocker.patch(
            "solarwinds_apm.configurator.load_entry_point"
        )

        # Mock Otel
        resource_mocks = get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_sampler(mock_apmconfig_enabled)

        # tracer_provider set with new resource using configured service_name
        trace_mocks["set_tracer_provider"].assert_called_once()
        resource_mocks["create"].assert_has_calls(
            [
                # service name from apmconfig fixture
                mocker.call({"service.name": "foo-service"})
            ]
        )
        mock_tracerprovider.assert_called_once()

        # noop unused
        trace_mocks["NoOpTracerProvider"].assert_not_called()

    def test_configure_sampler_otel_env_var_ignored(
        self,
        mocker,
        mock_apmconfig_enabled,
        mock_tracerprovider,
    ):
        # Save any SAMPLER env var for later
        old_traces_sampler = os.environ.get("OTEL_TRACES_SAMPLER", None)
        if old_traces_sampler:
            del os.environ["OTEL_TRACES_SAMPLER"]

        # Mock entry points
        mock_load_entry_point = mocker.patch(
            "solarwinds_apm.configurator.load_entry_point"
        )

        # Mock Otel
        resource_mocks = get_resource_mocks(mocker)
        trace_mocks = get_trace_mocks(mocker)

        # Mock sw sampler
        mock_sw_sampler = mocker.patch(
            "solarwinds_apm.sampler.ParentBasedSwSampler"
        )

        mocker.patch.dict(
            os.environ,
            {
                "OTEL_TRACES_SAMPLER": "foo_sampler"
            }
        )

        # Test!
        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_sampler(mock_apmconfig_enabled)

        # sampler loaded was solarwinds_sampler, not configured foo_sampler
        mock_load_entry_point.assert_called_once_with(
            "solarwinds_apm",
            "opentelemetry_traces_sampler",
            "solarwinds_sampler",
        )

        # tracer_provider set with new resource using configured service_name
        trace_mocks["set_tracer_provider"].assert_called_once()
        resource_mocks["create"].assert_has_calls(
            [
                # service name from apmconfig fixture
                mocker.call({"service.name": "foo-service"})
            ]
        )
        mock_tracerprovider.assert_called_once()

        # noop unused
        trace_mocks["NoOpTracerProvider"].assert_not_called()

        # Restore old EXPORTER
        if old_traces_sampler:
            os.environ["OTEL_TRACES_SAMPLER"] = old_traces_sampler