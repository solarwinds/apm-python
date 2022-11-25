import pytest
from types import MappingProxyType

from opentelemetry.trace.span import TraceState

from solarwinds_apm.sampler import _SwSampler

# pylint: disable=unused-import
from .fixtures.parent_span_context import (
    fixture_parent_span_context_invalid,
    fixture_parent_span_context_valid_remote,
)
from .fixtures.sampler import fixture_swsampler
from .fixtures.span_id_from_sw import fixture_mock_span_id_from_sw
from .fixtures.sw_from_span_and_decision import fixture_mock_sw_from_span_and_decision

# Otel Fixtures =========================================

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

# Decision Fixtures =====================================

@pytest.fixture(name="decision_drop")
def fixture_decision_drop():
    return {
        "do_metrics": 0,
        "do_sample": 0,
    }

@pytest.fixture(name="decision_record_only")
def fixture_decision_record_only():
    return {
        "do_metrics": 1,
        "do_sample": 0,
        "rate": 1,
        "source": 1,
        "bucket_rate": 1,
        "bucket_cap": 1,
    }

@pytest.fixture(name="decision_record_and_sample")
def fixture_decision_record_and_sample():
    return {
        "do_metrics": 1,
        "do_sample": 1,
        "rate": 1,
        "source": 1,
        "bucket_rate": 1,
        "bucket_cap": 1,
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

# XTraceOptions Fixtures ================================

@pytest.fixture(name="mock_xtraceoptions_sw_keys_and_custom_keys_no_tt_unsigned")
def fixture_xtraceoptions_sw_keys_and_custom_keys_no_tt_unsigned(mocker):
    options = mocker.Mock()
    options.sw_keys = "foo"
    options.custom_kvs = {"custom-foo": "awesome-bar"}
    return options

@pytest.fixture(name="mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt")
def fixture_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt(mocker):
    options = mocker.Mock()
    options.sw_keys = "foo"
    options.custom_kvs = {"custom-foo": "awesome-bar"}
    options.trigger_trace = 1
    return options

@pytest.fixture(name="mock_xtraceoptions_no_sw_keys_nor_custom_keys_nor_tt_unsigned")
def fixture_xtraceoptions_no_sw_keys_nor_custom_keys_nor_tt_unsigned(mocker):
    options = mocker.Mock()
    options.sw_keys = ""
    options.custom_kvs = {}
    return options

@pytest.fixture(name="mock_xtraceoptions_no_sw_keys_nor_custom_keys_with_unsigned_tt")
def fixture_xtraceoptions_no_sw_keys_nor_custom_keys_with_unsigned_tt(mocker):
    options = mocker.Mock()
    options.sw_keys = ""
    options.custom_kvs = {}
    options.trigger_trace = 1
    return options


# The Tests =========================================================

class Test_SwSampler_calculate_attributes():
    """
    Separate _SwSampler.calculate_attributes tests for so many 
    possible x-trace-options, x-trace-options-signature, decision cases
    """
    def test_init(self, mocker):
        mock_apm_config = mocker.Mock()
        sampler = _SwSampler(mock_apm_config)
        assert sampler.apm_config == mock_apm_config

    def test_decision_drop_with_no_sw_keys_nor_custom_keys_nor_tt_unsigned(
        self,
        mocker,
        sw_sampler,
        decision_drop,
        mock_xtraceoptions_no_sw_keys_nor_custom_keys_nor_tt_unsigned,
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=mocker.Mock(),
            decision=decision_drop,
            trace_state=mocker.Mock(),
            parent_span_context=mocker.Mock(),
            xtraceoptions=mock_xtraceoptions_no_sw_keys_nor_custom_keys_nor_tt_unsigned,
        ) == None

    def test_decision_drop_with_sw_keys_and_custom_keys_no_tt_unsigned(
        self,
        mocker,
        sw_sampler,
        decision_drop,
        mock_xtraceoptions_sw_keys_and_custom_keys_no_tt_unsigned,
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=mocker.Mock(),
            decision=decision_drop,
            trace_state=mocker.Mock(),
            parent_span_context=mocker.Mock(),
            xtraceoptions=mock_xtraceoptions_sw_keys_and_custom_keys_no_tt_unsigned,
        ) == None

    def test_decision_record_only_with_custom_and_sw_keys_no_tt_unsigned(
        self,
        mocker,
        sw_sampler,
        decision_record_only,
        mock_xtraceoptions_sw_keys_and_custom_keys_no_tt_unsigned,
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=mocker.Mock(),
            decision=decision_record_only,
            trace_state=mocker.Mock(),
            parent_span_context=mocker.Mock(),
            xtraceoptions=mock_xtraceoptions_sw_keys_and_custom_keys_no_tt_unsigned,
        ) == None

    def test_decision_record_and_sample_with_sw_keys_and_custom_keys_no_tt_unsigned(
        self,
        sw_sampler,
        decision_record_and_sample,
        parent_span_context_invalid,
        mock_xtraceoptions_sw_keys_and_custom_keys_no_tt_unsigned,
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=None,
            decision=decision_record_and_sample,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_sw_keys_and_custom_keys_no_tt_unsigned,
        ) == MappingProxyType({
            "BucketCapacity": "1",
            "BucketRate": "1",
            "SampleRate": 1,
            "SampleSource": 1,
            "SWKeys": "foo",
            "custom-foo": "awesome-bar",
        })

    def test_contd_decision_sw_keys_and_custom_keys_and_unsigned_tt(
        self,
        sw_sampler,
        decision_continued,
        parent_span_context_invalid,
        mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=None,
            decision=decision_continued,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt,
        ) == MappingProxyType({
            "BucketCapacity": "-1",
            "BucketRate": "-1",
            "SampleRate": -1,
            "SampleSource": -1,
            "TriggeredTrace": True,
            "SWKeys": "foo",
            "custom-foo": "awesome-bar",
        })

    def test_contd_decision_with_no_sw_keys_nor_custom_keys_nor_tt_unsigned(
        self,
        sw_sampler,
        decision_continued,
        parent_span_context_invalid,
        mock_xtraceoptions_no_sw_keys_nor_custom_keys_nor_tt_unsigned
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=None,
            decision=decision_continued,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_no_sw_keys_nor_custom_keys_nor_tt_unsigned,
        ) == MappingProxyType({
            "BucketCapacity": "-1",
            "BucketRate": "-1",
            "SampleRate": -1,
            "SampleSource": -1,
        })

    def test_contd_decision_with_no_sw_keys_nor_custom_keys_with_unsigned_tt(
        self,
        sw_sampler,
        decision_continued,
        parent_span_context_invalid,
        mock_xtraceoptions_no_sw_keys_nor_custom_keys_with_unsigned_tt
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=None,
            decision=decision_continued,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_no_sw_keys_nor_custom_keys_with_unsigned_tt,
        ) == MappingProxyType({
            "BucketCapacity": "-1",
            "BucketRate": "-1",
            "SampleRate": -1,
            "SampleSource": -1,
            "TriggeredTrace": True,
        })

    def test_not_contd_decision_with_sw_keys_and_custom_keys_and_unsigned_tt(
        self,
        sw_sampler,
        decision_not_continued,
        parent_span_context_invalid,
        mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=None,
            decision=decision_not_continued,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt,
        ) == MappingProxyType({
            "BucketCapacity": "1",
            "BucketRate": "1",
            "SampleRate": 1,
            "SampleSource": 1,
            "TriggeredTrace": True,
            "SWKeys": "foo",
            "custom-foo": "awesome-bar",
        })

    def test_not_contd_decision_with_no_sw_keys_nor_custom_keys_with_unsigned_tt(
        self,
        sw_sampler,
        decision_not_continued,
        parent_span_context_invalid,
        mock_xtraceoptions_no_sw_keys_nor_custom_keys_with_unsigned_tt
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=None,
            decision=decision_not_continued,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_no_sw_keys_nor_custom_keys_with_unsigned_tt
        ) == MappingProxyType({
            "BucketCapacity": "1",
            "BucketRate": "1",
            "SampleRate": 1,
            "SampleSource": 1,
            "TriggeredTrace": True,
        })

    def test_not_contd_decision_with_no_sw_keys_nor_custom_keys_nor_tt_unsigned(
        self,
        sw_sampler,
        decision_not_continued,
        parent_span_context_invalid,
        mock_xtraceoptions_no_sw_keys_nor_custom_keys_nor_tt_unsigned
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=None,
            decision=decision_not_continued,
            trace_state=None,
            parent_span_context=parent_span_context_invalid,
            xtraceoptions=mock_xtraceoptions_no_sw_keys_nor_custom_keys_nor_tt_unsigned
        ) == MappingProxyType({
            "BucketCapacity": "1",
            "BucketRate": "1",
            "SampleRate": 1,
            "SampleSource": 1,
        })

    def test_valid_parent_create_new_attrs_with_sw_keys_and_custom_keys_and_unsigned_tt(
        self,
        sw_sampler,
        decision_continued,
        tracestate_with_sw_and_others,
        parent_span_context_valid_remote,
        mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=None,
            decision=decision_continued,
            trace_state=tracestate_with_sw_and_others,
            parent_span_context=parent_span_context_valid_remote,
            xtraceoptions=mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt,
        ) == MappingProxyType({
            "BucketCapacity": "-1",
            "BucketRate": "-1",
            "SampleRate": -1,
            "SampleSource": -1,
            "TriggeredTrace": True,
            "sw.tracestate_parent_id": "1111222233334444",
            "sw.w3c.tracestate": "foo=bar,sw=123,baz=qux",
            "SWKeys": "foo",
            "custom-foo": "awesome-bar",
        })

    def test_valid_parent_update_attrs_no_tracestate_capture_with_sw_keys_and_custom_keys_and_unsigned_tt(
        self,
        sw_sampler,
        attributes_no_tracestate,
        decision_continued,
        tracestate_with_sw_and_others,
        parent_span_context_valid_remote,
        mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=attributes_no_tracestate,
            decision=decision_continued,
            trace_state=tracestate_with_sw_and_others,
            parent_span_context=parent_span_context_valid_remote,
            xtraceoptions=mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt,
        ) == MappingProxyType({
            "BucketCapacity": "-1",
            "BucketRate": "-1",
            "SampleRate": -1,
            "SampleSource": -1,
            "TriggeredTrace": True,
            "sw.w3c.tracestate": "foo=bar,sw=123,baz=qux",
            "SWKeys": "foo",
            "custom-foo": "awesome-bar",
            "foo": "bar",
            "baz": "qux",
        })

    def test_valid_parent_update_attrs_tracestate_capture_with_sw_keys_and_custom_keys_and_unsigned_tt(
        self,
        sw_sampler,
        attributes_with_tracestate,
        decision_continued,
        tracestate_with_sw_and_others,
        parent_span_context_valid_remote,
        mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt
    ):
        assert sw_sampler.calculate_attributes(
            span_name="foo",
            attributes=attributes_with_tracestate,
            decision=decision_continued,
            trace_state=tracestate_with_sw_and_others,
            parent_span_context=parent_span_context_valid_remote,
            xtraceoptions=mock_xtraceoptions_sw_keys_and_custom_keys_and_unsigned_tt,
        ) == MappingProxyType({
            "BucketCapacity": "-1",
            "BucketRate": "-1",
            "SampleRate": -1,
            "SampleSource": -1,
            "TriggeredTrace": True,
            "sw.w3c.tracestate": "sw=1111222233334444-01,some=other",
            "SWKeys": "foo",
            "custom-foo": "awesome-bar",
            "foo": "bar",
            "baz": "qux",
        })