import pytest

from solarwinds_apm.apm_constants import (
    INTL_SWO_COMMA,
    INTL_SWO_COMMA_W3C_SANITIZED,
    INTL_SWO_EQUALS,
    INTL_SWO_EQUALS_W3C_SANITIZED
)
from solarwinds_apm.response_propagator import SolarWindsTraceResponsePropagator


class TestSwTraceResponsePropagator():
    def test_inject_invalid_span_context(self, mocker):
        pass

    def test_inject_valid_span_context_with_xtraceoptions(self):
        pass

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
