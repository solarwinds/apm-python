import pytest  # pylint: disable=unused-import
from unittest.mock import call

from solarwinds_apm.response_propagator import SolarWindsTraceResponsePropagator


class TestSwTraceResponsePropagator():
    def mock_otel_trace_and_sw(self, mocker, valid_span_context=True) -> None:
        """Shared mocks for OTel trace and some sw parts"""
        # Mock sw parts external to response propagator inject
        mock_traceparent = mocker.Mock()
        mock_traceparent.configure_mock(return_value="my_x_trace")
        mock_w3ctransformer_cls = mocker.patch(
            "solarwinds_apm.response_propagator.W3CTransformer"
        )
        mock_w3ctransformer_cls.configure_mock(
            **{
                "traceparent_from_context": mock_traceparent
            }
        )
        mocker.patch(
            "solarwinds_apm.response_propagator.SolarWindsTraceResponsePropagator.recover_response_from_tracestate",
            return_value="my_recovered_response"
        )

        # Mock OTel trace API and current span context
        mock_get_span_context = mocker.Mock()
        mock_get_span_context.configure_mock(
            **{
                "trace_state": "my_trace_state"
            }
        )
        mock_get_current_span = mocker.Mock()
        if valid_span_context:
            mock_get_current_span.configure_mock(
                **{
                    "get_span_context.return_value": mock_get_span_context
                }
            )
        else:
            mock_get_current_span.configure_mock(
                **{
                    "get_span_context.return_value": "INVALID"
                }
            )
        mock_trace = mocker.patch(
            "solarwinds_apm.response_propagator.trace"
        )
        mock_trace.configure_mock(
            **{
                "get_current_span.return_value": mock_get_current_span,
                "INVALID_SPAN_CONTEXT": "INVALID"
            }
        )

    def test_inject_invalid_span_context(self, mocker):
        """The setter should not set anything for response headers"""
        self.mock_otel_trace_and_sw(mocker, False)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
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
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsTraceResponsePropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        SolarWindsTraceResponsePropagator.recover_response_from_tracestate.assert_called_once_with(
            "my_trace_state",
        )
        mock_set.assert_has_calls([
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
                "x-trace,x-trace-options-response"
            ),
        ])

    def test_recover_response_from_tracestate(self, mocker):
        mock_get_key = mocker.Mock()
        mock_get_key.configure_mock(return_value="foo")
        mock_xtraceoptions_cls = mocker.patch(
            "solarwinds_apm.response_propagator.XTraceOptions"
        )
        mock_xtraceoptions_cls.configure_mock(
            **{
                "get_sw_xtraceoptions_response_key": mock_get_key
            }
        )
        result = SolarWindsTraceResponsePropagator().recover_response_from_tracestate(
            {
                "foo": "bar####baz....qux####quux"
            }
        )
        assert result == "bar=baz,qux=quux"
