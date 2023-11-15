# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest

from solarwinds_apm.apm_meter_manager import SolarWindsMeterManager

class TestApmMeterManager:

    def test_init(
        self,
        mocker,
    ):
        # Mock OTel metrics SDK
        mock_histo = mocker.Mock()
        mock_o_gauge = mocker.Mock()
        mock_meter = mocker.Mock()
        mock_meter.configure_mock(
            **{
                "create_histogram": mock_histo,
                "create_observable_gauge": mock_o_gauge,
            }
        )
        mock_otel_get_meter = mocker.patch(
            "solarwinds_apm.apm_meter_manager.get_meter",
            return_value=mock_meter
        )

        # Mock APM Config
        mock_apm_config = mocker.Mock()

        # Test!
        test_mgr = SolarWindsMeterManager(mock_apm_config)
        mock_otel_get_meter.assert_has_calls(
            [
                mocker.call("sw.apm.request.metrics"),
                mocker.call("sw.apm.sampling.metrics"),
            ]
        )

        # dict of created ObservableGauge name: Python callback name
        o_gauge_calls_dict = {}
        for call in mock_o_gauge.mock_calls:
            _, _, c_kwargs = call
            o_gauge_calls_dict[c_kwargs["name"]] = c_kwargs["callbacks"][0].__name__
        assert o_gauge_calls_dict == {
            "trace.service.tracecount": "consume_tracecount",
            "trace.service.samplecount": "consume_samplecount",
            "trace.service.request_count": "consume_request_count",
            "trace.service.tokenbucket_exhaustion_count": "consume_tokenbucket_exhaustion_count",
            "trace.service.through_trace_count": "consume_through_trace_count",
            "trace.service.triggered_trace_count": "consume_triggered_trace_count",
            "trace.service.sample_rate": "get_last_used_sample_rate",
            "trace.service.sample_source": "get_last_used_sample_source"
        }

        assert mock_histo.mock_calls == [
            mocker.call(
                name="trace.service.response_time",
                description="measures the duration of an inbound HTTP request",
                unit="ms",
            )
        ]
