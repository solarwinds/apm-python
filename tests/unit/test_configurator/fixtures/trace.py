# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest


def get_trace_mocks(mocker):
    mock_add_span_processor = mocker.Mock()

    mock_get_tracer_provider = mocker.Mock()
    mock_get_tracer_provider.configure_mock(
        return_value=mocker.Mock(
            **{
                "add_span_processor": mock_add_span_processor
            }
        )
    )

    mock_trace = mocker.Mock()
    mock_trace.configure_mock(
        return_value=mocker.Mock(
            **{
                "get_tracer_provider": mock_get_tracer_provider
            }
        )
    )
    # return mock_trace, mock_get_tracer_provider, mock_add_span_processor
    return mock_trace


@pytest.fixture(name="mock_trace")
def fixture_mock_trace(mocker):
    return mocker.patch(
        "solarwinds_apm.configurator.trace",
        return_value=get_trace_mocks(mocker)
    )
