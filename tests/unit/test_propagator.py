import pytest  # pylint: disable=unused-import
from unittest.mock import call

from opentelemetry.context.context import Context
from opentelemetry.trace.span import TraceState

from solarwinds_apm.propagator import SolarWindsPropagator


class TestSolarWindsPropagator():

    def test_extract_new_context_no_xtraceoptions(self):
        mock_carrier = dict()
        result = SolarWindsPropagator().extract(mock_carrier)
        assert isinstance(result, Context)

    def test_extract_new_context_xtraceoptions_and_signature(self):
        mock_carrier = {
            "x-trace-options": "foo",
            "x-trace-options-signature": "bar"
        }
        result = SolarWindsPropagator().extract(mock_carrier)
        assert result == {
            "sw_xtraceoptions": "foo",
            "sw_signature": "bar"
        }

    def test_extract_new_context_no_xtraceoptions_yes_signature(self):
        mock_carrier = {
            "x-trace-options-signature": "bar"
        }
        result = SolarWindsPropagator().extract(mock_carrier)
        assert result == {
            "sw_signature": "bar"
        }

    def test_extract_existing_context(self):
        mock_carrier = {
            "x-trace-options": "foo",
            "x-trace-options-signature": "bar"
        }
        mock_otel_context = {
            "foo_key": "foo_value",
            "sw_xtraceoptions": "dont_know_why_these_are_here",
            "sw_signature": "but_they_will_be_replaced",
        }
        result = SolarWindsPropagator().extract(mock_carrier, mock_otel_context)
        assert result == {
            "foo_key": "foo_value",
            "sw_xtraceoptions": "foo",
            "sw_signature": "bar"
        }

    def mock_otel_context(self, mocker, valid_span_id=True):
        """Shared mocks for OTel trace context"""
        # Mock OTel trace API and current span context
        mock_get_span_context = mocker.Mock()
        if valid_span_id:
            mock_get_span_context.configure_mock(
                **{
                    "span_id": 0x1000100010001000,
                    "trace_flags": 0x01,
                }
            )
        else:
            mock_get_span_context.configure_mock(
                **{
                    "span_id": 0x0000000000000000,
                    "trace_flags": 0x00,
                }
            )
        mock_get_current_span = mocker.Mock()
        mock_get_current_span.configure_mock(
            **{
                "get_span_context.return_value": mock_get_span_context
            }
        )
        mock_trace = mocker.patch(
            "solarwinds_apm.propagator.trace"
        )
        mock_trace.configure_mock(
            **{
                "get_current_span.return_value": mock_get_current_span,
            }
        )

    def test_inject_no_tracestate_invalid_span_id(self, mocker):
        """No tracestate set in carrier"""
        self.mock_otel_context(mocker, False)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x0000000000000000, trace_flags 0x00
        mock_set.assert_not_called()

    def test_inject_no_tracestate_new_tracestate(self, mocker):
        """New tracestate with sw added to start"""
        self.mock_otel_context(mocker, True)
        mock_carrier = dict()
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x1000100010001000, trace_flags 0x01
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-01")]).to_header(),
            ),
        ])

    def test_inject_existing_tracestate_no_sw(self, mocker):
        """sw added to start, foo=bar kept, xtrace_options_response removed"""
        self.mock_otel_context(mocker, True)
        mock_carrier = {
            "tracestate": "xtrace_options_response=abc123,foo=bar"
        }
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x1000100010001000, trace_flags 0x01
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-01"), ("foo", "bar")]).to_header(),
            ),
        ])

    def test_inject_existing_tracestate_existing_sw(self, mocker):
        """sw updated and moved to start, foo=bar kept, xtrace_options_response removed"""
        self.mock_otel_context(mocker, True)
        mock_carrier = {
            "tracestate": "xtrace_options_response=abc123,foo=bar,sw=some-existing-value",
        }
        mock_context = mocker.Mock()
        mock_setter = mocker.Mock()
        mock_set = mocker.Mock()
        mock_setter.configure_mock(
            **{
                "set": mock_set
            }
        )
        SolarWindsPropagator().inject(
            mock_carrier,
            mock_context,
            mock_setter,
        )
        # OTel context mocked with span_id 0x1000100010001000, trace_flags 0x01
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "1000100010001000-01"), ("foo", "bar")]).to_header(),
            ),
        ])
