import pytest

# unittest cannot reassign members of enum
from opentelemetry.sdk.trace.sampling import Decision, StaticSampler
from opentelemetry.trace.span import SpanContext, TraceState

import solarwinds_apm.extension.oboe
from solarwinds_apm.sampler import _SwSampler, ParentBasedSwSampler


# Mock Fixtures =====================================================

@pytest.fixture(name="mock_xtraceoptions_tt")
def fixture_xtraceoptions_tt(mocker):
    options = mocker.Mock()
    options.trigger_trace = mocker.Mock(return_value=1)
    options.options_header = "foo-bar"
    options.signature = 123456
    options.ts = 123456
    return options

@pytest.fixture(name="mock_liboboe_decision")
def fixture_mock_liboboe_decision():
    return 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11

@pytest.fixture(autouse=True)
def fixture_mock_context_getdecisions(mocker, mock_liboboe_decision):
    mocker.patch(
        'solarwinds_apm.extension.oboe.Context.getDecisions',
        return_value=mock_liboboe_decision
    )

@pytest.fixture(autouse=True)
def fixture_mock_sw_from_span_and_decision(mocker):
    mocker.patch(
        "solarwinds_apm.w3c_transformer.W3CTransformer.sw_from_span_and_decision",
        return_value="1111222233334444-01"
    )

@pytest.fixture(autouse=True)
def fixture_mock_trace_flags_from_int(mocker):
    mocker.patch(
        "solarwinds_apm.w3c_transformer.W3CTransformer.trace_flags_from_int",
        return_value="01"
    )

@pytest.fixture(name="mock_traceparent_from_context")
def fixture_mock_traceparent_from_context(mocker):
    mocker.patch(
        "solarwinds_apm.w3c_transformer.W3CTransformer.traceparent_from_context",
        return_value="foo-bar"
    )

@pytest.fixture(autouse=True)
def fixture_mock_get_sw_xtraceoptions_response_key(mocker):
    mocker.patch(
        "solarwinds_apm.traceoptions.XTraceOptions.get_sw_xtraceoptions_response_key",
        return_value="foo"
    )

# Other Fixtures ====================================================

@pytest.fixture(name="decision_do_sample")
def fixture_decision_do_sample():
    return {
        "do_metrics": 1,
        "do_sample": 1,
    }

@pytest.fixture(name="parent_span_context_invalid")
def fixture_parent_span_context_invalid():
    return SpanContext(
        trace_id=00000000000000000000000000000000,
        span_id=0000000000000000,
        is_remote=False,
        trace_flags=0,
        trace_state=None,
    )

@pytest.fixture(name="parent_span_context_valid_not_remote")
def fixture_parent_span_context_valid_not_remote():
    return SpanContext(
        trace_id=11112222333344445555666677778888,
        span_id=1111222233334444,
        is_remote=False,
        trace_flags=1,
        trace_state=None,
    )

@pytest.fixture(name="parent_span_context_valid_remote")
def fixture_parent_span_context_valid_remote():
    return SpanContext(
        trace_id=11112222333344445555666677778888,
        span_id=1111222233334444,
        is_remote=True,
        trace_flags=1,
        trace_state=TraceState([["sw", "123"]]),
    )

# The Tests =========================================================

class Test_SwSampler():
    @classmethod
    def setup_class(cls):
        cls.sampler = _SwSampler()

    @classmethod
    def teardown_class(cls):
        pass
        #TODO: needed?

    def test_calculate_liboboe_decision_root_span(
        self,
        parent_span_context_invalid,
        mock_xtraceoptions_tt,
    ):
        self.sampler.calculate_liboboe_decision(
            parent_span_context_invalid,
            mock_xtraceoptions_tt,
        )
        solarwinds_apm.extension.oboe.Context.getDecisions.assert_called_once_with(
            None,
            None,
            -1,
            -1,
            mock_xtraceoptions_tt.trigger_trace,
            -1,
            mock_xtraceoptions_tt.options_header,
            mock_xtraceoptions_tt.signature,
            mock_xtraceoptions_tt.ts
        )

    def test_calculate_liboboe_decision_parent_valid_not_remote(
        self,
        parent_span_context_valid_not_remote,
        mock_xtraceoptions_tt
    ):
        self.sampler.calculate_liboboe_decision(
            parent_span_context_valid_not_remote,
            mock_xtraceoptions_tt,
        )
        solarwinds_apm.extension.oboe.Context.getDecisions.assert_called_once_with(
            None,
            None,
            -1,
            -1,
            mock_xtraceoptions_tt.trigger_trace,
            -1,
            mock_xtraceoptions_tt.options_header,
            mock_xtraceoptions_tt.signature,
            mock_xtraceoptions_tt.ts
        )

    def test_calculate_liboboe_decision_parent_valid_remote(
        self,
        mock_traceparent_from_context,
        parent_span_context_valid_remote,
        mock_xtraceoptions_tt
    ):
        self.sampler.calculate_liboboe_decision(
            parent_span_context_valid_remote,
            mock_xtraceoptions_tt,
        )
        solarwinds_apm.extension.oboe.Context.getDecisions.assert_called_once_with(
            "foo-bar",
            "123",
            -1,
            -1,
            mock_xtraceoptions_tt.trigger_trace,
            -1,
            mock_xtraceoptions_tt.options_header,
            mock_xtraceoptions_tt.signature,
            mock_xtraceoptions_tt.ts
        )

    def test_is_decision_continued_false(self):
        assert not self.sampler.is_decision_continued({
            "rate": 0,
            "source": -1,
            "bucket_rate": -1,
            "bucket_cap": -1,
        })
        assert not self.sampler.is_decision_continued({
            "rate": -1,
            "source": 0,
            "bucket_rate": -1,
            "bucket_cap": -1,
        })
        assert not self.sampler.is_decision_continued({
            "rate": -1,
            "source": -1,
            "bucket_rate": 0,
            "bucket_cap": -1,
        })
        assert not self.sampler.is_decision_continued({
            "rate": -1,
            "source": -1,
            "bucket_rate": -1,
            "bucket_cap": 0,
        })

    def test_is_decision_continued_true(self):
        assert self.sampler.is_decision_continued({
            "rate": -1,
            "source": -1,
            "bucket_rate": -1,
            "bucket_cap": -1,
        })

    def test_otel_decision_from_liboboe(self):
        assert self.sampler.otel_decision_from_liboboe({
            "do_metrics": 0,
            "do_sample": 0,
        }) == Decision.DROP
        assert self.sampler.otel_decision_from_liboboe({
            "do_metrics": 1,
            "do_sample": 0,
        }) == Decision.RECORD_ONLY
        assert self.sampler.otel_decision_from_liboboe({
            "do_metrics": 1,
            "do_sample": 1,
        }) == Decision.RECORD_AND_SAMPLE
        # Shouldn't happen
        assert self.sampler.otel_decision_from_liboboe({
            "do_metrics": 0,
            "do_sample": 1,
        }) == Decision.RECORD_AND_SAMPLE

    def test_create_xtraceoptions_response_value_unsigned_tt(self):
        # trigger_msg ignored vs status
        # with/without ignored
        pass

    def test_create_xtraceoptions_response_value_unsigned_not_tt(self):
        # with/without ignored
        pass

    def test_create_xtraceoptions_response_value_signed_tt(self):
        # trigger_msg ignored vs status
        # with/without ignored
        pass

    def test_create_xtraceoptions_response_value_signed_not_tt(self):
        # with/without ignored
        pass

    def test_create_new_trace_state(
        self,
        mocker,
        decision_do_sample,
        parent_span_context_valid_remote,
        mock_xtraceoptions_tt
    ):
        # Should this be mocked?
        mocker.patch(
            "solarwinds_apm.sampler._SwSampler.create_xtraceoptions_response_value",
            return_value="bar"
        )
        trace_state = self.sampler.create_new_trace_state(decision_do_sample, parent_span_context_valid_remote, mock_xtraceoptions_tt)
        assert trace_state == {
            "sw": "1111222233334444-01",
            "foo": "bar",
        }

    def test_calculate_trace_state_root_span(self):
        pass

    def test_calculate_trace_state_is_remote_create(self):
        pass

    def test_calculate_trace_state_is_remote_update(self):
        # with/without xtraceoptions response
        pass

    def test_remove_response_from_sw(self, mocker):
        ts = TraceState([["bar", "456"],["foo", "123"]])
        assert self.sampler.remove_response_from_sw(ts) == TraceState([["bar", "456"]])

    def test_calculate_attributes_dont_trace(self):
        pass

    def test_calculate_attributes_not_continued_trace(self):
        pass

    def test_calculate_attributes_root_span(self):
        pass

    def test_calculate_attributes_is_remote_create(self):
        pass

    def test_calculate_attributes_is_remote_update(self):
        pass

    def test_calculate_attributes_rm_tracestate_capture(self):
        pass

    def test_should_sample(self):
        pass

    # TODO: test matrix of should_sample root vs is_remote?


class TestParentBasedSwSampler():
    def test_init(self):
        sampler = ParentBasedSwSampler()
        assert type(sampler._root) == _SwSampler
        assert type(sampler._remote_parent_sampled) == _SwSampler
        assert type(sampler._remote_parent_not_sampled) == _SwSampler
        
        assert type(sampler._local_parent_sampled) == StaticSampler
        assert type(sampler._local_parent_not_sampled) == StaticSampler

    # TODO: test matrix of should_sample root vs is_remote?
