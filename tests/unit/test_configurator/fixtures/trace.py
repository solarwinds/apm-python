# Copyright SolarWinds Worldwide, LLC.
# SPDX-License-Identifier: Apache-2.0


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
        add_span_processor=mock_add_span_processor, get_tracer=mock_get_tracer
    )
    mock_get_tracer_provider = mocker.Mock(return_value=mock_tracer_provider)
    mock_set_tracer_provider = mocker.Mock()
    mock_noop_tracer_provider = mocker.Mock()
    mock_trace = mocker.patch(
        "solarwinds_apm.configurator.trace",
    )
    mock_trace.configure_mock(
        get_tracer_provider=mock_get_tracer_provider,
        set_tracer_provider=mock_set_tracer_provider,
        NoOpTracerProvider=mock_noop_tracer_provider,
    )
    return mock_trace
