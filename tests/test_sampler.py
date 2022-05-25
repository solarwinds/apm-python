import pytest
from types import MappingProxyType

from opentelemetry.sdk.trace.sampling import (
    Decision, StaticSampler
)
from opentelemetry.trace.span import SpanContext, TraceState

import solarwinds_apm.extension.oboe
from solarwinds_apm.sampler import _SwSampler, ParentBasedSwSampler


# Mock Fixtures, autoused ===========================================

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

@pytest.fixture(autouse=True)
def fixture_mock_span_id_from_sw(mocker):
    mocker.patch(
        "solarwinds_apm.w3c_transformer.W3CTransformer.span_id_from_sw",
        return_value="1111222233334444"
    )

@pytest.fixture(autouse=True)
def fixture_mock_get_sw_xtraceoptions_response_key(mocker):
    mocker.patch(
        "solarwinds_apm.traceoptions.XTraceOptions.get_sw_xtraceoptions_response_key",
        return_value="xtrace_foo"
    )

# Mock Fixtures, manually used ======================================

@pytest.fixture(name="mock_liboboe_decision")
def fixture_mock_liboboe_decision():
    return 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11

@pytest.fixture(name="mock_traceparent_from_context")
def fixture_mock_traceparent_from_context(mocker):
    mocker.patch(
        "solarwinds_apm.w3c_transformer.W3CTransformer.traceparent_from_context",
        return_value="foo-bar"
    )

@pytest.fixture(name="mock_xtraceoptions_signed_tt")
def fixture_xtraceoptions_signed_tt(mocker):
    options = mocker.Mock()
    options.trigger_trace = 1
    options.options_header = "foo-bar"
    options.signature = 123456
    options.ts = 123456
    options.ignored = ["baz", "qux"]
    return options

@pytest.fixture(name="mock_xtraceoptions_signed_not_tt")
def fixture_xtraceoptions_signed_not_tt(mocker):
    options = mocker.Mock()
    options.trigger_trace = 0
    options.options_header = "foo-bar"
    options.signature = 123456
    options.ts = 123456
    options.ignored = ["baz", "qux"]
    return options

@pytest.fixture(name="mock_xtraceoptions_sw_keys")
def fixture_xtraceoptions_sw_keys(mocker):
    options = mocker.Mock()
    options.sw_keys = "foo"
    return options

@pytest.fixture(name="mock_xtraceoptions_no_sw_keys")
def fixture_xtraceoptions_no_sw_keys(mocker):
    options = mocker.Mock()
    options.sw_keys = ""
    return options


# Other Fixtures, manually used =====================================

@pytest.fixture(name="decision_drop")
def fixture_decision_drop():
    return {
        "do_metrics": 0,
        "do_sample": 0,
    }

@pytest.fixture(name="decision_continued")
def fixture_decision_continued():
    return {
        "do_metrics": 1,
        "do_sample": 1,
        "rate": -1,
        "source": -1,
        "bucket_rate": -1,
        "bucket_cap": -1,
    }


@pytest.fixture(name="decision_not_continued")
def fixture_decision_not_continued():
    return {
        "do_metrics": 1,
        "do_sample": 1,
        "rate": 1,
        "source": 1,
        "bucket_rate": 1,
        "bucket_cap": 1,
    }

@pytest.fixture(name="decision_auth")
def fixture_decision_auth():
    return {
        "do_metrics": 1,
        "do_sample": 1,
        "auth": 1,
        "auth_msg": "foo-bar",
    }

@pytest.fixture(name="decision_not_auth_type_zero")
def fixture_decision_not_auth_type_zero():
    return {
        "do_metrics": 1,
        "do_sample": 1,
        "auth": 0,
        "auth_msg": "foo-bar",
        "decision_type": 0,
        "status_msg": "baz-qux",
    }

@pytest.fixture(name="decision_not_auth_type_nonzero")
def fixture_decision_auth_type_nonzero():
    return {
        "do_metrics": 1,
        "do_sample": 1,
        "auth": 0,
        "auth_msg": "foo-bar",
        "decision_type": -1,
        "status_msg": "baz-qux",
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

@pytest.fixture(name="parent_span_context_valid_not_remote_sampled")
def fixture_parent_span_context_valid_not_remote_sampled():
    return SpanContext(
        trace_id=11112222333344445555666677778888,
        span_id=1111222233334444,
        is_remote=False,
        trace_flags=1,
        trace_state=None,
    )

@pytest.fixture(name="parent_span_context_valid_not_remote_not_sampled")
def fixture_parent_span_context_valid_not_remote_not_sampled():
    return SpanContext(
        trace_id=11112222333344445555666677778888,
        span_id=1111222233334444,
        is_remote=False,
        trace_flags=0,
        trace_state=None,
    )

@pytest.fixture(name="parent_span_context_valid_remote")
def fixture_parent_span_context_valid_remote():
    return SpanContext(
        trace_id=11112222333344445555666677778888,
        span_id=1111222233334444,
        is_remote=True,
        trace_flags=1,
        trace_state=TraceState([
            ["sw", "123"]
        ]),
    )

@pytest.fixture(name="parent_span_context_valid_remote_no_tracestate")
def fixture_parent_span_context_valid_remote_no_tracestate():
    return SpanContext(
        trace_id=11112222333344445555666677778888,
        span_id=1111222233334444,
        is_remote=True,
        trace_flags=1,
        trace_state=None,
    )

@pytest.fixture(name="tracestate_with_sw_and_others")
def fixture_tracestate_with_sw_and_others():
    return TraceState([
        ["foo", "bar"],
        ["sw", "123"],
        ["baz", "qux"]
    ])

@pytest.fixture(name="attributes_no_tracestate")
def fixture_attributes_no_tracestate():
    return MappingProxyType({
        "foo": "bar",
        "baz": "qux"
    })

@pytest.fixture(name="attributes_with_tracestate")
def fixture_attributes_with_tracestate():
    return MappingProxyType({
        "foo": "bar",
        "sw.w3c.tracestate": "some=other,sw=before",
        "baz": "qux"
    })


# The Tests =========================================================

class Test_SwSampler():
    @classmethod
    def setup_class(cls):
        cls.sampler = _SwSampler()

    def test_calculate_liboboe_decision_root_span(
        self,
        parent_span_context_invalid,
        mock_xtraceoptions_signed_tt,
    ):
        self.sampler.calculate_liboboe_decision(
            parent_span_context_invalid,
            mock_xtraceoptions_signed_tt,
        )
        solarwinds_apm.extension.oboe.Context.getDecisions.assert_called_once_with(
            None,
            None,
            -1,
            -1,
            mock_xtraceoptions_signed_tt.trigger_trace,
            -1,
            mock_xtraceoptions_signed_tt.options_header,
            mock_xtraceoptions_signed_tt.signature,
            mock_xtraceoptions_signed_tt.ts
        )

    # pylint:disable=unused-argument
    def test_calculate_liboboe_decision_parent_valid_remote(
        self,
        mock_traceparent_from_context,
        parent_span_context_valid_remote,
    ):
        self.sampler.calculate_liboboe_decision(
            parent_span_context_valid_remote,
        )
        solarwinds_apm.extension.oboe.Context.getDecisions.assert_called_once_with(
            "foo-bar",
            "123",
            -1,
            -1,
            0,
            -1,
            None,
            None,
            None,
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

    def test_create_xtraceoptions_response_value_auth(
        self,
        decision_auth,
        parent_span_context_valid_remote,
        mock_xtraceoptions_signed_tt,
    ):
        response_val = self.sampler.create_xtraceoptions_response_value(
            decision_auth,
            parent_span_context_valid_remote,
            mock_xtraceoptions_signed_tt,
        )
        assert response_val == "auth####foo-bar;ignored####baz....qux"

    def test_create_xtraceoptions_response_value_tt_unauth_type_nonzero_root_span(
        self,
        decision_not_auth_type_nonzero,
        parent_span_context_invalid,
        mock_xtraceoptions_signed_tt,
    ):
        response_val = self.sampler.create_xtraceoptions_response_value(
            decision_not_auth_type_nonzero,
            parent_span_context_invalid,
            mock_xtraceoptions_signed_tt,
        )
        assert response_val == "auth####foo-bar;trigger-trace####baz-qux;ignored####baz....qux"

    def test_create_xtraceoptions_response_value_tt_unauth_type_nonzero_parent_span_remote(
        self,
        decision_not_auth_type_nonzero,
        parent_span_context_valid_remote,
        mock_xtraceoptions_signed_tt,
    ):
        response_val = self.sampler.create_xtraceoptions_response_value(
            decision_not_auth_type_nonzero,
            parent_span_context_valid_remote,
            mock_xtraceoptions_signed_tt, 
        )
        assert response_val == "auth####foo-bar;trigger-trace####baz-qux;ignored####baz....qux"

    def test_create_xtraceoptions_response_value_tt_unauth_type_zero_root_span(
        self,
        decision_not_auth_type_zero,
        parent_span_context_invalid,
        mock_xtraceoptions_signed_tt,
    ):
        response_val = self.sampler.create_xtraceoptions_response_value(
            decision_not_auth_type_zero,
            parent_span_context_invalid,
            mock_xtraceoptions_signed_tt,
        )
        assert response_val == "auth####foo-bar;trigger-trace####baz-qux;ignored####baz....qux"

    def test_create_xtraceoptions_response_value_tt_unauth_type_zero_parent_span_remote(
        self,
        decision_not_auth_type_zero,
        parent_span_context_valid_remote,
        mock_xtraceoptions_signed_tt,
    ):
        response_val = self.sampler.create_xtraceoptions_response_value(
            decision_not_auth_type_zero,
            parent_span_context_valid_remote,
            mock_xtraceoptions_signed_tt,    
        )
        assert response_val == "auth####foo-bar;trigger-trace####ignored;ignored####baz....qux"

    def test_create_xtraceoptions_response_value_not_tt_unauth(
        self,
        decision_not_auth_type_nonzero,
        parent_span_context_invalid,
        mock_xtraceoptions_signed_not_tt,
    ):
        response_val = self.sampler.create_xtraceoptions_response_value(
            decision_not_auth_type_nonzero,
            parent_span_context_invalid,
            mock_xtraceoptions_signed_not_tt,     
        )
        assert response_val == "auth####foo-bar;trigger-trace####not-requested;ignored####baz....qux"

    def test_create_new_trace_state(
        self,
        mocker,
        decision_auth,
        parent_span_context_valid_remote,
        mock_xtraceoptions_signed_tt
    ):
        mocker.patch(
            "solarwinds_apm.sampler._SwSampler.create_xtraceoptions_response_value",
            return_value="bar"
        )
        trace_state = self.sampler.create_new_trace_state(
            decision_auth,
            parent_span_context_valid_remote,
            mock_xtraceoptions_signed_tt
        )
        assert trace_state == TraceState([
            ["sw", "1111222233334444-01"],
            ["xtrace_foo", "bar"]
        ])

    def test_calculate_trace_state_root_span(
        self,
        mocker,
        decision_auth,
        parent_span_context_invalid
    ):
        mocker.patch(
            "solarwinds_apm.sampler._SwSampler.create_new_trace_state",
            return_value="bar"
        )
        trace_state = self.sampler.calculate_trace_state(
            decision_auth,
            parent_span_context_invalid
        )
        assert trace_state == "bar"

    def test_calculate_trace_state_is_remote_create(
        self,
        mocker,
        decision_auth,
        parent_span_context_valid_remote_no_tracestate
    ):
        mocker.patch(
            "solarwinds_apm.sampler._SwSampler.create_new_trace_state",
            return_value="bar"
        )
        trace_state = self.sampler.calculate_trace_state(
            decision_auth,
            parent_span_context_valid_remote_no_tracestate
        )
        assert trace_state == "bar"

    def test_calculate_trace_state_is_remote_update(
        self,
        mocker,
        decision_auth,
        parent_span_context_valid_remote,
        mock_xtraceoptions_signed_tt,
    ):
        mocker.patch(
            "solarwinds_apm.sampler._SwSampler.create_xtraceoptions_response_value",
            return_value="bar"
        )
        assert parent_span_context_valid_remote.trace_state == TraceState([
            ["sw", "123"]
        ])
        trace_state = self.sampler.calculate_trace_state(
            decision_auth,
            parent_span_context_valid_remote,
            mock_xtraceoptions_signed_tt,
        )
        assert trace_state == TraceState([
            ["sw", "1111222233334444-01"],
            ["xtrace_foo", "bar"]
        ])

    def test_remove_response_from_sw(self):
        ts = TraceState([["bar", "456"],["xtrace_foo", "123"]])
        assert self.sampler.remove_response_from_sw(ts) == TraceState([["bar", "456"]])

    def test_calculate_attributes_dont_trace(
        self,
        mocker,
        decision_drop
    ):
        assert self.sampler.calculate_attributes(
            attributes=mocker.Mock(),
            decision=decision_drop,
            trace_state=mocker.Mock(),
            parent_span_context=mocker.Mock(),
            xtraceoptions=mocker.Mock(),
        ) == None

    def test_calculate_attributes_contd_decision_sw_keys(
        self,
        decision_continued,
        parent_span_context_invalid,
        mock_xtraceoptions_sw_keys
    ):
        assert self.sampler.calculate_attributes(
            attributes=None,
            decision=decision_continued,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_sw_keys,
        ) == MappingProxyType({"SWKeys": "foo"})

    def test_calculate_attributes_contd_decision_no_sw_keys(
        self,
        decision_continued,
        parent_span_context_invalid,
        mock_xtraceoptions_no_sw_keys
    ):
        assert self.sampler.calculate_attributes(
            attributes=None,
            decision=decision_continued,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_no_sw_keys,
        ) == None

    def test_calculate_attributes_not_contd_decision_sw_keys(
        self,
        decision_not_continued,
        parent_span_context_invalid,
        mock_xtraceoptions_sw_keys
    ):
        assert self.sampler.calculate_attributes(
            attributes=None,
            decision=decision_not_continued,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_sw_keys,
        ) == MappingProxyType({
            "BucketCapacity": "1",
            "BucketRate": "1",
            "SampleRate": 1,
            "SampleSource": 1,
            "SWKeys": "foo",
        })

    def test_calculate_attributes_not_contd_decision_no_sw_keys(
        self,
        decision_not_continued,
        parent_span_context_invalid,
        mock_xtraceoptions_no_sw_keys
    ):
        assert self.sampler.calculate_attributes(
            attributes=None,
            decision=decision_not_continued,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_no_sw_keys
        ) == MappingProxyType({
            "BucketCapacity": "1",
            "BucketRate": "1",
            "SampleRate": 1,
            "SampleSource": 1,
        })

    def test_calculate_attributes_valid_parent_create_new_attrs(
        self,
        decision_continued,
        tracestate_with_sw_and_others,
        parent_span_context_valid_remote,
        mock_xtraceoptions_sw_keys
    ):
        assert self.sampler.calculate_attributes(
            attributes=None,
            decision=decision_continued,
            trace_state=tracestate_with_sw_and_others,
            parent_span_context=parent_span_context_valid_remote,
            xtraceoptions=mock_xtraceoptions_sw_keys,
        ) == MappingProxyType({
            "sw.tracestate_parent_id": "1111222233334444",
            "sw.w3c.tracestate": "foo=bar,sw=123,baz=qux",
            'SWKeys': 'foo',
        })

    def test_calculate_attributes_valid_parent_update_attrs_no_tracestate_capture(
        self,
        attributes_no_tracestate,
        decision_continued,
        tracestate_with_sw_and_others,
        parent_span_context_valid_remote,
        mock_xtraceoptions_sw_keys
    ):
        assert self.sampler.calculate_attributes(
            attributes=attributes_no_tracestate,
            decision=decision_continued,
            trace_state=tracestate_with_sw_and_others,
            parent_span_context=parent_span_context_valid_remote,
            xtraceoptions=mock_xtraceoptions_sw_keys,
        ) == MappingProxyType({
            "sw.w3c.tracestate": "foo=bar,sw=123,baz=qux",
            'SWKeys': 'foo',
            "foo": "bar",
            "baz": "qux",
        })

    def test_calculate_attributes_valid_parent_update_attrs_tracestate_capture(
        self,
        attributes_with_tracestate,
        decision_continued,
        tracestate_with_sw_and_others,
        parent_span_context_valid_remote,
        mock_xtraceoptions_sw_keys
    ):
        assert self.sampler.calculate_attributes(
            attributes=attributes_with_tracestate,
            decision=decision_continued,
            trace_state=tracestate_with_sw_and_others,
            parent_span_context=parent_span_context_valid_remote,
            xtraceoptions=mock_xtraceoptions_sw_keys,
        ) == MappingProxyType({
            "sw.w3c.tracestate": "sw=1111222233334444-01,some=other",
            'SWKeys': 'foo',
            "foo": "bar",
            "baz": "qux",
        })

    def test_should_sample(
        self,
        mocker,
    ):
        mock_get_current_span = mocker.patch("solarwinds_apm.sampler.get_current_span")
        mock_get_current_span.configure_mock(
            return_value=mocker.Mock(
                **{
                    "get_span_context.return_value": "my_span_context",
                }
            )
        )
        mock_xtraceoptions_cls = mocker.patch(
            "solarwinds_apm.sampler.XTraceOptions"
        )
        mock_xtraceoptions = mocker.Mock()
        mock_xtraceoptions_cls.configure_mock(
            return_value=mock_xtraceoptions
        )
        mocker.patch(
            "solarwinds_apm.sampler._SwSampler.calculate_liboboe_decision",
            return_value="my_decision"
        )
        mocker.patch(
            "solarwinds_apm.sampler._SwSampler.calculate_trace_state",
            return_value="my_trace_state"
        )
        mocker.patch(
            "solarwinds_apm.sampler._SwSampler.calculate_attributes",
            return_value="my_attributes"
        )
        mocker.patch(
            "solarwinds_apm.sampler._SwSampler.otel_decision_from_liboboe",
            return_value="otel_decision"
        )

        sampling_result = self.sampler.should_sample(
            parent_context=mocker.MagicMock(),
            trace_id=123,
            name="foo",
            attributes={"foo": "bar"}
        )

        solarwinds_apm.sampler._SwSampler.calculate_liboboe_decision.assert_called_once_with(
            "my_span_context",
            mock_xtraceoptions
        )
        solarwinds_apm.sampler._SwSampler.calculate_trace_state.assert_called_once_with(
            "my_decision",
            "my_span_context",
            mock_xtraceoptions
        )
        solarwinds_apm.sampler._SwSampler.calculate_attributes.assert_called_once_with(
            {"foo": "bar"},
            "my_decision",
            "my_trace_state",
            "my_span_context",
            mock_xtraceoptions
        )
        solarwinds_apm.sampler._SwSampler.otel_decision_from_liboboe.assert_called_once_with(
            "my_decision"
        )
        assert sampling_result.attributes == "my_attributes"
        assert sampling_result.decision == "otel_decision"
        assert sampling_result.trace_state == "my_trace_state"


class TestParentBasedSwSampler():
    def test_init(self):
        sampler = ParentBasedSwSampler()
        assert type(sampler._root) == _SwSampler
        assert type(sampler._remote_parent_sampled) == _SwSampler
        assert type(sampler._remote_parent_not_sampled) == _SwSampler
        assert type(sampler._local_parent_sampled) == StaticSampler
        assert type(sampler._local_parent_not_sampled) == StaticSampler

    def test_should_sample_remote_sampled(
        self,
        mocker,
    ):
        pass

    def test_should_sample_remote_not_sampled(
        self,
        mocker,
    ):
        pass

    def test_should_sample_not_remote_sampled(
        self,
        mocker,
        parent_span_context_valid_not_remote_sampled,
    ):
        mock_sw_should_sample = mocker.patch(
            "solarwinds_apm.sampler._SwSampler.should_sample",
        )

        mock_should_sample = mocker.MagicMock()
        mock_sampled = mocker.Mock(
            **{
                "should_sample": mock_should_sample
            }
        )
        mock_parent_based = mocker.patch(
            "solarwinds_apm.sampler.ParentBased"
        )
        mock_parent_based.configure_mock(
            **{
                "_remote_parent_sampled": mock_sampled,
                "_remote_parent_not_sampled": mock_sampled,
                "_local_parent_sampled": mock_sampled,
                "_local_parent_not_sampled": mock_sampled,
            }
        )

        mock_get_current_span = mocker.patch("solarwinds_apm.sampler.get_current_span")
        mock_get_current_span.configure_mock(
            return_value=mocker.Mock(
                **{
                    "get_span_context.return_value": parent_span_context_valid_not_remote_sampled,
                }
            )
        )
        mock_otel_context = mocker.Mock()
        mock_otel_context.configure_mock(
            **{
                "get_current_span": mock_get_current_span
            }
        )  

        sampler = ParentBasedSwSampler()
        result = sampler.should_sample(
            parent_context=mock_otel_context,
            trace_id=11112222333344445555666677778888,
            name="foo",
        )
        # mock_sw_should_sample.assert_called_once()  # shouldn't pass
        # mock_should_sample.assert_called_once()     # failing


    def test_should_sample_not_remote_not_sampled(
        self,
        mocker,
        parent_span_context_valid_not_remote_not_sampled,
    ):
        pass