# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import pytest

def get_trace_mocks(mocker):
    mock_add_span_processor = mocker.Mock()
  
    mock_attributes = mocker.PropertyMock()
    mock_attributes.return_value = {"foo": "bar"}
    mock_resource = mocker.PropertyMock()
    type(mock_resource).attributes = mock_attributes
    mock_tracer = mocker.Mock()
    type(mock_tracer).resource = mock_resource
    mock_get_tracer = mocker.Mock(return_value=mock_tracer)

    mock_tracer_provider = mocker.Mock()
    mock_tracer_provider.configure_mock(
        **{
            "add_span_processor": mock_add_span_processor,
            "get_tracer": mock_get_tracer,
        }
    )
    mock_get_tracer_provider = mocker.Mock(
        return_value=mock_tracer_provider
    )
    mock_set_tracer_provider = mocker.Mock()
    mock_noop_tracer_provider = mocker.Mock()
    mock_trace = mocker.patch(
        "solarwinds_apm.configurator.trace",
    )
    mock_trace.configure_mock(
        **{
            "get_tracer_provider": mock_get_tracer_provider,
            "set_tracer_provider": mock_set_tracer_provider,
            "NoOpTracerProvider": mock_noop_tracer_provider,
        }
    )
    return mock_trace
