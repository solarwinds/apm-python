import pytest

# unittest cannot reassign members of enum
from opentelemetry.sdk.trace.sampling import Decision

from solarwinds_apm.sampler import _SwSampler, ParentBasedSwSampler


@pytest.fixture(name="mock_decision_do_sample")
def fixture_decision():
    return {
        "do_metrics": 1,
        "do_sample": 1,
    }

@pytest.fixture(name="mock_parent_span_context")
def fixture_parent_span_context(mocker):
    span_context = mocker.Mock()
    span_context_attrs = {
        "trace_id": 11112222333344445555666677778888,
        "span_id": 1111222233334444,
        "trace_flags": 1,      
    }
    span_context.configure_mock(**span_context_attrs)
    return span_context

@pytest.fixture(name="mock_xtraceoptions_tt")
def fixture_xtraceoptions(mocker):
    options = mocker.Mock()
    options.trigger_trace = mocker.Mock(return_value=True)
    return options


class Test_SwSampler():
    @classmethod
    def setup_class(cls):
        cls.sampler = _SwSampler()

    @classmethod
    def teardown_class(cls):
        pass
        #TODO: needed?

    def test_calculate_liboboe_decision_root_span(self):
        # with/without xtraceoptions
        pass

    def test_calculate_liboboe_decision_parent_is_remote(self):
        # with/without xtraceoptions
        pass

    # TODO: test matrix of liboboe inputs/outputs?

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
        mock_decision_do_sample,
        mock_parent_span_context,
        mock_xtraceoptions_tt
    ):
        mocker.patch(
            "solarwinds_apm.w3c_transformer.W3CTransformer.sw_from_span_and_decision",
            return_value="1111222233334444-01"
        )
        mocker.patch(
            "solarwinds_apm.w3c_transformer.W3CTransformer.trace_flags_from_int",
            return_value="01"
        )
        mocker.patch(
            "solarwinds_apm.traceoptions.XTraceOptions.get_sw_xtraceoptions_response_key",
            return_value="foo"
        )
        # Should this be mocked?
        mocker.patch(
            "solarwinds_apm.sampler._SwSampler.create_xtraceoptions_response_value",
            return_value="bar"
        )
        trace_state = self.sampler.create_new_trace_state(mock_decision_do_sample, mock_parent_span_context, mock_xtraceoptions_tt)
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

    def test_remove_response_from_sw(self):
        pass

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
        from opentelemetry.sdk.trace.sampling import StaticSampler
        assert type(sampler._local_parent_sampled) == StaticSampler
        assert type(sampler._local_parent_not_sampled) == StaticSampler

    # TODO: test matrix of should_sample root vs is_remote?
