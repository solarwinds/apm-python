# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import os

from solarwinds_apm import configurator

# otel fixtures
from .fixtures.trace import get_trace_mocks


class TestConfiguratorSpanProcessors:
    def test_configure_service_entry_span_processor(
        self,
        mocker,
    ):
        trace_mocks = get_trace_mocks(mocker)
        mocker.patch(
            "solarwinds_apm.configurator.ServiceEntrySpanProcessor"
        )

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_service_entry_span_processor()
        trace_mocks.get_tracer_provider.assert_called_once()
        trace_mocks.get_tracer_provider().add_span_processor.assert_called_once()

    def test_configure_response_time_processor_exporters_not_set(
        self,
        mocker,
        mock_apmconfig_enabled,
    ):
        # Save any exporters in os for later
        old_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]
        mocker.patch.dict(os.environ, {
            "OTEL_METRICS_EXPORTER": "",
        })

        trace_mocks = get_trace_mocks(mocker)
        mock_processor_instance = mocker.Mock()
        mock_rt_processor = mocker.patch(
            "solarwinds_apm.configurator.ResponseTimeProcessor",
            return_value=mock_processor_instance,
        )

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_response_time_processor()
        trace_mocks.get_tracer_provider.assert_not_called()
        trace_mocks.get_tracer_provider().add_span_processor.assert_not_called()
        mock_rt_processor.assert_not_called()

        # Restore the os exporters
        if old_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_exporter

    def test_configure_response_time_processor_exporters_set(
        self,
        mocker,
        mock_apmconfig_enabled,
    ):
        # Save any exporters in os for later
        old_exporter = os.environ.get("OTEL_METRICS_EXPORTER", None)
        if old_exporter:
            del os.environ["OTEL_METRICS_EXPORTER"]
        mocker.patch.dict(os.environ, {
            "OTEL_METRICS_EXPORTER": "foo_exporter",
        })

        trace_mocks = get_trace_mocks(mocker)
        mock_processor_instance = mocker.Mock()
        mock_rt_processor = mocker.patch(
            "solarwinds_apm.configurator.ResponseTimeProcessor",
            return_value=mock_processor_instance,
        )

        test_configurator = configurator.SolarWindsConfigurator()
        test_configurator._configure_response_time_processor()
        trace_mocks.get_tracer_provider.assert_has_calls(
            [
                mocker.call(),
            ]
        )
        trace_mocks.get_tracer_provider().add_span_processor.assert_has_calls(
            [
                mocker.call(mock_processor_instance),
            ]
        )
        mock_rt_processor.assert_called_once()

        # Restore the os exporters
        if old_exporter:
            os.environ["OTEL_METRICS_EXPORTER"] = old_exporter