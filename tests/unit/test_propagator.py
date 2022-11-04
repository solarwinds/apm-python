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

    def mock_otel_and_other_sw(self, mocker, valid_span_id=True):
        """Shared mocks for OTel trace and some sw parts"""
        # Mock sw parts external to propagator inject
        mock_sw = mocker.Mock()
        mock_sw.configure_mock(return_value="2000200020002000-01")
        mock_w3ctransformer_cls = mocker.patch(
            "solarwinds_apm.propagator.W3CTransformer"
        )
        mock_w3ctransformer_cls.configure_mock(
            **{
                "sw_from_context": mock_sw
            }
        )

        # Could mock OTel TraceState here but using real instead

        # Mock OTel trace API and current span context
        mock_get_span_context = mocker.Mock()
        if valid_span_id:
            mock_get_span_context.configure_mock(
                **{
                    "span_id": 0x1000100010001000
                }
            )
        else:
            mock_get_span_context.configure_mock(
                **{
                    "span_id": 0x0000000000000000
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
        self.mock_otel_and_other_sw(mocker, False)
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
        mock_set.assert_not_called()

    def test_inject_no_tracestate_new_tracestate(self, mocker):
        self.mock_otel_and_other_sw(mocker, True)
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
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "2000200020002000-01")]).to_header(),
            ),
        ])

    def test_inject_existing_tracestate_no_sw(self, mocker):
        self.mock_otel_and_other_sw(mocker, True)
        mock_carrier = {
            "tracestate": "foo=bar"
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
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "2000200020002000-01"), ("foo", "bar")]).to_header(),
            ),
        ])

    def test_inject_existing_tracestate_existing_sw(self, mocker):
        self.mock_otel_and_other_sw(mocker, True)
        mock_carrier = {
            "tracestate": "foo=bar,sw=some-existing-value",
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
        mock_set.assert_has_calls([
            call(
                mock_carrier,
                "tracestate",
                TraceState([("sw", "2000200020002000-01"), ("foo", "bar")]).to_header(),
            ),
        ])
