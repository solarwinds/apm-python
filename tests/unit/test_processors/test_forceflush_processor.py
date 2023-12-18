# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from solarwinds_apm.trace import ForceFlushSpanProcessor


class TestForceFlushSpanProcessor:

    def test_on_end(self, mocker):
        mock_meter_flush = mocker.Mock()
        mock_meter_provider = mocker.Mock()
        mock_meter_provider.configure_mock(
            **{
                "force_flush": mock_meter_flush
            }
        )
        mocker.patch(
            "solarwinds_apm.trace.forceflush_processor.get_meter_provider",
            return_value=mock_meter_provider
        )

        mock_tracer_flush = mocker.Mock()
        mock_tracer_provider = mocker.Mock()
        mock_tracer_provider.configure_mock(
            **{
                "force_flush": mock_tracer_flush
            }
        )
        mocker.patch(
            "solarwinds_apm.trace.forceflush_processor.get_tracer_provider",
            return_value=mock_tracer_provider
        )

        ForceFlushSpanProcessor().on_end(mocker.Mock())
        mock_meter_flush.assert_called_once()
        mock_tracer_flush.assert_called_once()
