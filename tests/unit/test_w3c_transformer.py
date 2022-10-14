import pytest

from solarwinds_apm.w3c_transformer import W3CTransformer


@pytest.fixture(name="span_context")
def fixture_span_context(mocker):
    span_context = mocker.Mock()
    span_context_attrs = {
        "trace_id": 11112222333344445555666677778888,
        "span_id": 1111222233334444,
        "trace_flags": 1,      
    }
    span_context.configure_mock(**span_context_attrs)
    return span_context


class TestW3CTransformer():
    def test_span_from_int(self):
        assert W3CTransformer.span_id_from_int(1111222233334444) \
            == "{:016x}".format(1111222233334444)

    def test_span_id_from_sw(self):
        assert W3CTransformer.span_id_from_sw("foo-bar") == "foo"

    def test_trace_flags_from_int(self):
        assert W3CTransformer.trace_flags_from_int(1) == "01"

    def test_traceparent_from_context(self, span_context):
        assert W3CTransformer.traceparent_from_context(span_context) \
            == "00-{:032x}-{:016x}-{:02x}".format(
                span_context.trace_id,
                span_context.span_id,
                span_context.trace_flags
            )

    def test_sw_from_context(self, span_context):
        assert W3CTransformer.sw_from_context(span_context) \
            == "{:016x}-{:02x}".format(
                span_context.span_id,
                span_context.trace_flags
            )

    def test_sw_from_span_and_decision(self):
        assert W3CTransformer.sw_from_span_and_decision(1234, "01") \
            == "{:016x}-{}".format(1234, "01")
