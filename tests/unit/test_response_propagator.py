# © 2023 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from unittest.mock import call

from solarwinds_apm.response_propagator import SolarWindsTraceResponsePropagator


class TestSwTraceResponsePropagator:
    def mock_otel_trace_and_sw(self, mocker, valid_span_context=True) -> None:
        """Shared mocks for OTel trace and some sw parts"""
        # Mock sw parts external to response propagator inject
        mock_traceparent = mocker.Mock()
        mock_traceparent.configure_mock(return_value="my_x_trace")
        mock_w3ctransformer_cls = mocker.patch(
            "solarwinds_apm.response_propagator.W3CTransformer"
        )
        mock_w3ctransformer_cls.configure_mock(
            **{"traceparent_from_context": mock_traceparent}
        )
        mocker.patch(
            "solarwinds_apm.response_propagator.SolarWindsTraceResponsePropagator.recover_response_from_tracestate",
            return_value="my_recovered_response",
        )

        # Mock OTel trace API and current span context
        mock_get_span_context = mocker.Mock()
        mock_get_span_context.configure_mock(**{"trace_state": "my_trace_state"})
        mock_get_current_span = mocker.Mock()
        if valid_span_context:
            mock_get_current_span.configure_mock(
                **{"get_span_context.return_value": mock_get_span_context}
            )
        else:
            mock_get_current_span.configure_mock(
                **{"get_span_context.return_value": "INVALID"}
            )
        mock_trace = mocker.patch("solarwinds_apm.response_propagator.trace")
        mock_trace.configure_mock(
            **{
                "get_current_span.return_value": mock_get_current_span,
                "INVALID_SPAN_CONTEXT": "INVALID",
            }
        )

    def test_inject_invalid_span_context(self, mocker):
        """The setter should not set anything for response headers"""
        self.mock_otel_trace_and_sw(mocker, False)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(**{"set": mock_set})
        SolarWindsTraceResponsePropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        SolarWindsTraceResponsePropagator.recover_response_from_tracestate.assert_not_called()
        mock_set.assert_not_called()

    def test_inject_valid_span_context_with_xtraceoptions(self, mocker):
        """The setter recovers x-trace-options response and sets in response headers"""
        self.mock_otel_trace_and_sw(mocker, True)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(**{"set": mock_set})
        SolarWindsTraceResponsePropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        SolarWindsTraceResponsePropagator.recover_response_from_tracestate.assert_called_once_with(
            "my_trace_state",
        )
        mock_set.assert_has_calls(
            [
                call(
                    mock_carrier,
                    "x-trace",
                    "my_x_trace",
                ),
                call(
                    mock_carrier,
                    "x-trace-options-response",
                    "my_recovered_response",
                ),
                call(
                    mock_carrier,
                    "Access-Control-Expose-Headers",
                    "x-trace,x-trace-options-response",
                ),
            ]
        )

    def test_recover_response_from_tracestate(self, mocker):
        result = SolarWindsTraceResponsePropagator().recover_response_from_tracestate(
            {"xtrace_options_response": "bar####baz....qux####quux"}
        )
        assert result == "bar=baz,qux=quux"
