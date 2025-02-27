import hashlib
import hmac
# import logging
# import typing
# from lib2to3.fixes.fix_import import traverse_imports
# from typing import Optional, Sequence, Union
#
# import pytest
# import os
# from unittest.mock import Mock
# import time
#
# from opentelemetry.context import Context
# from opentelemetry.sdk import trace
# from opentelemetry.sdk.resources import Attributes
# from opentelemetry.sdk.trace import RandomIdGenerator
# from opentelemetry.sdk.trace.sampling import Decision
# from opentelemetry.trace import TraceFlags, TraceState, SpanKind, Link, Span, SpanContext, get_current_span
# from typing_extensions import override
#
# from opentelemetry import context
# from opentelemetry import trace
# from opentelemetry.sdk.trace import sampling
#
#
# from solarwinds_apm.oboe.sampler import OboeSampler, _get_span_type, SpanType, SW_KEYS_ATTRIBUTE
# from solarwinds_apm.oboe.settings import Flags, LocalSettings, Settings, SampleSource
# from solarwinds_apm.oboe.trace_options import RequestHeaders, ResponseHeaders
#
# class MakeSpan:
#     def __init__(self,
#                  name: Optional[str] = None,
#                  trace_id: Optional[str] = None,
#                  span_id: Optional[str] = None,
#                  remote: Optional[bool] = None,
#                  sampled: Optional[bool] = None,
#                  sw: Optional[Union[bool, str]] = None):
#         self._name = name
#         self._trace_id = trace_id
#         self._span_id = span_id
#         self._remote = remote
#         self._sampled = sampled
#         self._sw = sw
#
#     @property
#     def name(self) -> Optional[str]:
#         return self._name
#
#     @name.setter
#     def name(self, value: Optional[str]) -> None:
#         self._name = value
#
#     @property
#     def trace_id(self) -> Optional[str]:
#         return self._trace_id
#
#     @trace_id.setter
#     def trace_id(self, value: Optional[str]) -> None:
#         self._trace_id = value
#
#     @property
#     def span_id(self) -> Optional[str]:
#         return self._span_id
#
#     @span_id.setter
#     def span_id(self, value: Optional[str]) -> None:
#         self._span_id = value
#
#     @property
#     def remote(self) -> Optional[bool]:
#         return self._remote
#
#     @remote.setter
#     def remote(self, value: Optional[bool]) -> None:
#         self._remote = value
#
#     @property
#     def sampled(self) -> Optional[bool]:
#         return self._sampled
#
#     @sampled.setter
#     def sampled(self, value: Optional[bool]) -> None:
#         self._sampled = value
#
#     @property
#     def sw(self) -> Optional[Union[bool, str]]:
#         return self._sw
#
#     @sw.setter
#     def sw(self, value: Optional[Union[bool, str]]) -> None:
#         self._sw = value
#
# def make_span(options : MakeSpan = None) -> Span:
#     final_span_options = MakeSpan(name=options.name if options.name else "span",
#                                   trace_id=options.trace_id if options.trace_id else os.urandom(16).hex(),
#                                   span_id=options.span_id if options.span_id else os.urandom(8).hex(),
#                                   remote=options.remote if options.remote else None,
#                                   sampled=options.sampled if options.sampled else True,
#                                   sw=options.sw if options.sw else None)
#     sw_flags = "01" if final_span_options.sampled else "00"
#     if isinstance(final_span_options.sw, str) and final_span_options.sw == "inverse":
#         sw_flags = "00" if final_span_options.sampled else "01"
#     mock_span = Mock()
#     mock_span.configure_mock(
#         **{
#             "trace_id": final_span_options.trace_id,
#             "span_id": final_span_options.span_id,
#             "is_remote": final_span_options.remote,
#             "trace_flags": TraceFlags.SAMPLED if final_span_options.sampled else TraceFlags.DEFAULT,
#             "trace_state": TraceState([("sw", final_span_options.span_id + "-" + sw_flags)]) if final_span_options.sw else None,
#         }
#     )
#     return mock_span
#
# class MakeSampleParams:
#     def __init__(self,
#                  parent: Optional[Span] = None,
#                  name: Optional[str] = None,
#                  kind: Optional[SpanKind] = None):
#         self._parent = parent
#         self._name = name
#         self._kind = kind
#
#     @property
#     def parent(self) -> Optional[Span]:
#         return self._parent
#
#     @parent.setter
#     def parent(self, value: Optional[Span]):
#         self._parent = value
#
#     @property
#     def name(self) -> Optional[str]:
#         return self._name
#
#     @name.setter
#     def name(self, value: Optional[str]):
#         self._name = value
#
#     @property
#     def kind(self) -> Optional[SpanKind]:
#         return self._kind
#
#     @kind.setter
#     def kind(self, value: Optional[SpanKind]):
#         self._kind = value
#
# def make_sample_params(options : Optional[MakeSampleParams]):
#     object = {
#         "parent": options.parent if options.parent else make_span(MakeSpan(name="parent span")),
#         "name": options.name if options else "child span",
#         "kind": options.kind if options else SpanKind.INTERNAL
#     }
#     return {
#         "parent_context": Context({"current_span": object["parent"]}),
#         "trace_id": object["parent"].get_span_context().trace_id if object["parent"] else os.urandom(16).hex(),
#         "name": object["name"],
#         "kind": object["kind"],
#         "attributes": None,
#         "links": None,
#         "trace_state": None
#     }
#
# def make_request_headers(options=None) -> RequestHeaders:
#     if options is None:
#         options = {}
#     if not options.get("trigger-trace") and not options.get("kvs") and not options.get("signature"):
#         return RequestHeaders()
#     timestamp = int(time.time())
#     if options.get("signature") == "bad-timestamp":
#         timestamp -= 10 * 60
#     ts = f"ts={timestamp}"
#     trigger_trace = "trigger-trace" if options.get("trigger-trace") and options.get("trigger-trace") is True else None
#     kvs = [f"{k}={v}" for k, v in options.get("kvs", {}).items()]
#     x_trace_options = ";".join(filter(None, [trigger_trace, *kvs, ts]))
#     if options.get("signature"):
#         key = options.get("signature-key", os.urandom(8).hex())
#         signature = hmac.new(str.encode(key), str.encode(x_trace_options), hashlib.sha1).hexdigest()
#         return RequestHeaders(x_trace_options=x_trace_options, x_trace_options_signature=signature)
#     return RequestHeaders(x_trace_options=x_trace_options)
#
# def check_counters(counters):
#     remaining = set(counters)
#     # metrics = (await otel.metrics()).flat_map(lambda x: x.scopeMetrics).flat_map(lambda x: x.metrics)
#     # while remaining and metrics:
#     #     metric = metrics.pop()
#     #     name = metric.descriptor.name
#     #     assert name in remaining
#     #     remaining.remove(name)
#     #     assert metric.dataPointType == DataPointType.SUM
#     #     assert len(metric.dataPoints) == 1
#     #     assert metric.dataPoints[0].value == 1
#     # assert not remaining
#     # assert not metrics
#
import os
import logging
import random
import time
from random import sample
from typing import Optional, Sequence, __all__
from unittest.mock import Mock

import pytest
from opentelemetry import trace
from opentelemetry.sdk.resources import Attributes
from opentelemetry.sdk.trace import RandomIdGenerator
from opentelemetry.trace import SpanKind, Link, TraceState, TraceFlags, get_current_span
from typing_extensions import override

from solarwinds_apm.apm_noop import Context
from solarwinds_apm.oboe.oboe_sampler import _span_type, SpanType, OboeSampler, SW_KEYS_ATTRIBUTE, \
    BUCKET_RATE_ATTRIBUTE, BUCKET_CAPACITY_ATTRIBUTE, SAMPLE_RATE_ATTRIBUTE, SAMPLE_SOURCE_ATTRIBUTE
from solarwinds_apm.oboe.settings import LocalSettings, Settings, SampleSource, Flags, BucketType, BucketSettings
from solarwinds_apm.oboe.trace_options import RequestHeaders, ResponseHeaders

class MakeRequestHeaders:
    def __init__(self, trigger_trace: Optional[bool] = None, kvs: Optional[dict] = None, signature = None, signature_key: Optional[str] = None):
        self._trigger_trace = trigger_trace
        self._kvs = kvs
        self._signature = signature
        self._signature_key = signature_key
    @property
    def trigger_trace(self) -> Optional[bool]:
        return self._trigger_trace

    @property
    def kvs(self) -> Optional[dict]:
        return self._kvs

    @property
    def signature(self) -> Optional[str]:
        return self._signature

    @property
    def signature_key(self) -> Optional[str]:
        return self._signature_key


def make_request_headers(options=MakeRequestHeaders()) -> RequestHeaders:
    if options.trigger_trace is None and options.kvs is None and options.signature is None:
        return RequestHeaders(x_trace_options=None, x_trace_options_signature=None)
    timestamp = int(time.time())
    if isinstance(options.signature_key, str) and options.signature == "bad-timestamp":
        timestamp -= 10 * 60
    ts = f"ts={timestamp}"
    trigger_trace = "trigger-trace" if options.trigger_trace else None
    kvs = [f"{k}={v}" for k, v in options.kvs.items() if options.kvs]
    headers = RequestHeaders(x_trace_options=";".join(filter(None, [trigger_trace, *kvs, ts])), x_trace_options_signature=None)
    if options.signature:
        key = options.signature_key if options.signature_key else os.urandom(8).hex()
        headers.x_trace_options_signature = hmac.new(str.encode(key), str.encode(headers.x_trace_options), hashlib.sha1).hexdigest()
    return headers


class TestSpanType:
    def test_identifies_no_parent_as_ROOT(self):
        span_type = _span_type(None)
        assert span_type == SpanType.ROOT
    def test_identifies_invalid_parent_as_ROOT(self):
        mock_get_span_context = Mock()
        mock_get_span_context.configure_mock(
            **{
                "is_valid": False,
            }
        )
        mock_span = Mock()
        mock_span.configure_mock(
            **{
                "get_span_context.return_value": mock_get_span_context
            }
        )
        span_type = _span_type(mock_span)
        assert span_type == SpanType.ROOT
    def test_identifies_remote_parent_as_ENTRY(self):
        mock_get_span_context = Mock()
        mock_get_span_context.configure_mock(
            **{
                "is_remote": True,
            }
        )
        mock_span = Mock()
        mock_span.configure_mock(
            **{
                "get_span_context.return_value": mock_get_span_context
            }
        )
        span_type = _span_type(mock_span)
        assert span_type == SpanType.ENTRY
    def test_identifies_local_parent_as_LOCAL(self):
        mock_get_span_context = Mock()
        mock_get_span_context.configure_mock(
            **{
                "is_remote": False,
            }
        )
        mock_span = Mock()
        mock_span.configure_mock(
            **{
                "get_span_context.return_value": mock_get_span_context
            }
        )
        span_type = _span_type(mock_span)
        assert span_type == SpanType.LOCAL

class TestSamplerOptions:
    def __init__(self, settings: Optional[Settings] = None, local_settings : Optional[LocalSettings] = None, request_headers : Optional[RequestHeaders] = None):
        self._settings = settings
        self._local_settings = local_settings
        self._request_headers = request_headers

    @property
    def settings(self) -> Optional[Settings]:
        return self._settings

    @property
    def local_settings(self) -> Optional[LocalSettings]:
        return self._local_settings

    @property
    def request_headers(self) -> Optional[RequestHeaders]:
        return self._request_headers


class TestSampler(OboeSampler):
    def __init__(self, options : TestSamplerOptions):
        super().__init__(logging.getLogger(__name__))
        self._local_settings = options.local_settings
        self._request_headers = options.request_headers
        if options.settings:
            self.update_settings(options.settings)
        self._response_headers = None

    def _create_parent(self, trace_flags: trace.TraceFlags, is_remote=False, sw=None) -> Optional[Context]:
        if trace_flags is None:
            return None
        return trace.set_span_in_context(self._create_parent_span(trace_flags, is_remote, sw))

    @staticmethod
    def _create_parent_span(trace_flags: trace.TraceFlags, is_remote=False, sw=None) -> trace.NonRecordingSpan:
        generator = RandomIdGenerator()
        trace_id = generator.generate_trace_id()
        span_id = generator.generate_span_id()
        trace_state = None
        if isinstance(sw, str) and sw == "inverse":
            trace_state = TraceState([("sw", format(span_id, "016x") + "-0" + ("0" if trace_flags == TraceFlags.SAMPLED else "1"))])
        elif isinstance(sw, bool):
            trace_state = TraceState([("sw", format(span_id, "016x") + "-0" + ("1" if trace_flags == TraceFlags.SAMPLED else "0"))])
        span_context = trace.SpanContext(trace_id=trace_id,span_id=span_id,is_remote=is_remote,trace_flags=trace_flags,trace_state=trace_state,)
        return trace.NonRecordingSpan(span_context)

    @override
    def local_settings(self,
                       parent_context: Optional["Context"],
                       trace_id: int,
                       name: str,
                       kind: Optional[SpanKind] = None,
                       attributes: Attributes = None,
                       links: Optional[Sequence["Link"]] = None,
                       trace_state: Optional["TraceState"] = None) -> LocalSettings:
        return self._local_settings

    @override
    def request_headers(self,
                        parent_context: Optional["Context"],
                        trace_id: int,
                        name: str,
                        kind: Optional[SpanKind] = None,
                        attributes: Attributes = None,
                        links: Optional[Sequence["Link"]] = None,
                        trace_state: Optional["TraceState"] = None
                        ) -> RequestHeaders:
        return self._request_headers

    @override
    def set_response_headers(self,
                             headers: ResponseHeaders):
        self._response_headers = headers

    @property
    def response_headers(self):
        return self._response_headers

    def __str__(self):
        return f"Test Sampler"

class TestLocalSpan:
    @pytest.fixture
    def local_span(self):
        return TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.OK,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=RequestHeaders(x_trace_options=None, x_trace_options_signature=None)
        ))
    def test_respects_parent_sampled(self, local_span):
        ctxt = local_span._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=False)
        sample = local_span.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "local_span_respects_parent_sampled")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()

    def test_respects_parent_not_sampled(self, local_span):
        ctxt = local_span._create_parent(trace_flags=TraceFlags.DEFAULT, is_remote=False)
        sample = local_span.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "local_span_respects_parent_not_sampled")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()

class TestInvalidXTraceOptionsSignature:
    def test_rejects_missing_signature_key(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=1_000_000,
                sample_source=SampleSource.Remote,
                flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(trigger_trace=True, signature=True, kvs={"custom-key": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "rejects_missing_signature_key")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()
        assert sample.attributes == {}
        assert "auth=no-signature-key" in sampler.response_headers.x_trace_options_response

    def test_rejects_bad_timestamp(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=1_000_000,
                sample_source=SampleSource.Remote,
                flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key="key",
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, signature="bad-timestamp", signature_key="key", kvs={"custom-key": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "rejects_bad_timestamp")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()
        assert sample.attributes == {}
        assert "auth=bad-timestamp" in sampler.response_headers.x_trace_options_response

    def test_rejects_bad_signature(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=1_000_000,
                sample_source=SampleSource.Remote,
                flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key="key1",
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, signature=True, signature_key="key2", kvs={"custom-key": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "rejects_bad_signature")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()
        assert sample.attributes == {}
        assert "auth=bad-signature" in sampler.response_headers.x_trace_options_response

class TestMissingSettings:
    def test_does_not_sample(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=None,
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        generator = RandomIdGenerator()
        sample = sampler.should_sample(None, generator.generate_trace_id(),"does_not_sample")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()

    def test_expires_after_ttl(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key=None,
                timestamp=int(time.time())-60,
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,"expires_after_ttl")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()

    def test_respects_x_trace_options_keys_and_values(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=None,
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(kvs={ "custom-key": "value", "sw-keys": "sw-values" }))
        ))
        generator = RandomIdGenerator()
        sample = sampler.should_sample(None, generator.generate_trace_id(), "respects_x_trace_options_keys_and_values")
        assert sample.attributes == {"custom-key": "value", SW_KEYS_ATTRIBUTE: "sw-values"}
        assert "trigger-trace=not-requested" in sampler.response_headers.x_trace_options_response

    def test_ignores_trigger_trace(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=None,
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(trigger_trace=True, kvs={ "custom-key": "value", "invalid-keys": "value" }))
        ))
        generator = RandomIdGenerator()
        sample = sampler.should_sample(None, generator.generate_trace_id(), "ignores_trigger_trace")
        assert sample.attributes == {"custom-key": "value"}
        assert "trigger-trace=settings-not-available" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response

class TestEntrySpanWithValidSwContextXTraceOptions:
    def test_respects_keys_and_values(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(kvs={ "custom-key": "value", "sw-keys": "sw-values" }))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "respects_keys_and_values")
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(SW_KEYS_ATTRIBUTE) == "sw-values"
        assert "trigger-trace=not-requested" in sampler.response_headers.x_trace_options_response
    def test_ignores_trigger_trace(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(trigger_trace=True, kvs={ "custom-key": "value", "invalid-keys": "value" }))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "ignores_trigger_trace")
        assert sample.attributes.get("custom-key") == "value"
        assert "trigger-trace=ignored" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response

class TestEntrySpanWithValidSwContextSampleThroughAlwaysSet:
    @pytest.fixture()
    def sample_through_always_set(self):
        return TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
    def test_respects_parent_sampled(self, sample_through_always_set):
        ctxt = sample_through_always_set._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True)
        sample = sample_through_always_set.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "respects_parent_sampled")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("sw.tracestate_parent_id") == format(get_current_span(ctxt).get_span_context().span_id, "016x")
    def test_respects_parent_not_sampled(self, sample_through_always_set):
        ctxt = sample_through_always_set._create_parent(trace_flags=TraceFlags.DEFAULT, is_remote=True, sw=True)
        sample = sample_through_always_set.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "respects_parent_not_sampled")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("sw.tracestate_parent_id") == format(get_current_span(ctxt).get_span_context().span_id, "016x")
    def test_respects_sw_sampled_over_w3c_not_sampled(self, sample_through_always_set):
        ctxt = sample_through_always_set._create_parent(trace_flags=TraceFlags.DEFAULT, is_remote=True, sw="inverse")
        sample = sample_through_always_set.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "respects_sw_sampled_over_w3c_not_sampled")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("sw.tracestate_parent_id") == format(get_current_span(ctxt).get_span_context().span_id, "016x")
    def test_respects_sw_not_sampled_over_w3c_sampled(self, sample_through_always_set):
        ctxt = sample_through_always_set._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw="inverse")
        sample = sample_through_always_set.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "respects_sw_not_sampled_over_w3c_sampled")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("sw.tracestate_parent_id") == format(get_current_span(ctxt).get_span_context().span_id, "016x")

class TestEntrySpanWithValidSwContextSampleThroughAlwaysUnset:
    def test_records_but_does_not_sample_when_SAMPLE_START_set(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_START,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "respects_sw_not_sampled_over_w3c_sampled")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
    def test_does_not_record_or_sample_when_SAMPLE_START_unset(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.OK,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "does_not_record_or_sample_when_SAMPLE_START_unset")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()

class TestTriggerTraceRequestedTriggeredTraceSetUnsigned:
    def test_records_and_samples_when_there_is_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_START | Flags.TRIGGERED_TRACE,
                buckets={
                    BucketType.TRIGGER_STRICT: BucketSettings(capacity=10, rate=5),
                    BucketType.TRIGGER_RELAXED: BucketSettings(capacity=0, rate=0)
                },
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(trigger_trace=True, kvs={ "custom-key": "value", "sw-keys": "sw-values" }))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,"records_and_samples_when_there_is_capacity")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(SW_KEYS_ATTRIBUTE) == "sw-values"
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 10
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 5
        assert "trigger-trace=ok" in sampler.response_headers.x_trace_options_response
    def test_records_but_does_not_sample_when_there_is_no_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_START | Flags.TRIGGERED_TRACE,
                buckets={
                    BucketType.TRIGGER_STRICT: BucketSettings(capacity=0, rate=0),
                    BucketType.TRIGGER_RELAXED: BucketSettings(capacity=20, rate=10)
                },
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(trigger_trace=True, kvs={ "custom-key": "value", "invalid-keys": "value" }))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "records_but_does_not_sample_when_there_is_no_capacity")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 0
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 0
        assert "trigger-trace=rate-exceeded" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response

class TestTriggerTraceRequestedTriggeredTraceSetSigned:
    def test_records_and_samples_when_there_is_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_START | Flags.TRIGGERED_TRACE,
                buckets={
                    BucketType.TRIGGER_STRICT: BucketSettings(capacity=0, rate=0),
                    BucketType.TRIGGER_RELAXED: BucketSettings(capacity=20, rate=10)
                },
                signature_key="key",
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(trigger_trace=True, signature=True, signature_key="key", kvs={ "custom-key": "value", "sw-keys": "sw-values" }))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,"records_and_samples_when_there_is_capacity")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(SW_KEYS_ATTRIBUTE) == "sw-values"
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 20
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 10
        assert "auth=ok" in sampler.response_headers.x_trace_options_response
        assert "trigger-trace=ok" in sampler.response_headers.x_trace_options_response
    def test_records_but_does_not_sample_when_there_is_no_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_START | Flags.TRIGGERED_TRACE,
                buckets={
                    BucketType.TRIGGER_STRICT: BucketSettings(capacity=10, rate=5),
                    BucketType.TRIGGER_RELAXED: BucketSettings(capacity=0, rate=0)
                },
                signature_key="key",
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(trigger_trace=True, signature=True, signature_key="key", kvs={ "custom-key": "value", "invalid-keys": "value" }))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "records_but_does_not_sample_when_there_is_no_capacity")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 0
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 0
        assert "trigger-trace=rate-exceeded" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response

class TestTriggerTraceRequestedTriggeredTraceUnset:
    def test_record_but_does_not_sample_when_TRIGGERED_TRACE_unset(self):
        sampler= TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_START,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(trigger_trace=True, kvs={"custom-key": "value", "invalid-keys": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "record_but_does_not_sample_when_TRIGGERED_TRACE_unset")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("custom-key") == "value"
        assert "trigger-trace=trigger-tracing-disabled" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response

class TestTriggerTraceRequestedDiceRoll:
    def test_respects_x_trace_options_keys_and_values(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_START,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders(kvs={ "custom-key": "value", "sw-keys": "sw-values" }))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.DEFAULT, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "respects_x_trace_options_keys_and_values")
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(SW_KEYS_ATTRIBUTE) == "sw-values"
        assert "trigger-trace=not-requested" in sampler.response_headers.x_trace_options_response
    def test_records_and_samples_when_dice_success_and_sufficient_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=1_000_000,
                sample_source=SampleSource.Remote,
                flags=Flags.SAMPLE_START,
                buckets={
                    BucketType.DEFAULT: BucketSettings(capacity=10, rate=5),
                },
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        generator = RandomIdGenerator()
        sample = sampler.should_sample(None, generator.generate_trace_id(), "records_and_samples_when_dice_success_and_sufficient_capacity")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get(SAMPLE_RATE_ATTRIBUTE) == 1_000_000
        assert sample.attributes.get(SAMPLE_SOURCE_ATTRIBUTE) == 6
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 10
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 5
    def test_records_but_does_not_sample_when_dice_success_but_insufficient_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=1_000_000,
                sample_source=SampleSource.Remote,
                flags=Flags.SAMPLE_START,
                buckets={
                    BucketType.DEFAULT: BucketSettings(capacity=0, rate=0),
                },
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        generator = RandomIdGenerator()
        sample = sampler.should_sample(None, generator.generate_trace_id(), "records_but_does_not_sample_when_dice_success_but_insufficient_capacity")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get(SAMPLE_RATE_ATTRIBUTE) == 1_000_000
        assert sample.attributes.get(SAMPLE_SOURCE_ATTRIBUTE) == 6
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 0
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 0
    def test_records_but_does_not_sample_when_dice_failure(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LocalDefault,
                flags=Flags.SAMPLE_START,
                buckets={
                    BucketType.DEFAULT: BucketSettings(capacity=10, rate=5)
                },
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        generator = RandomIdGenerator()
        sample = sampler.should_sample(None, generator.generate_trace_id(), "records_but_does_not_sample_when_dice_failure")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get(SAMPLE_RATE_ATTRIBUTE) == 0
        assert sample.attributes.get(SAMPLE_SOURCE_ATTRIBUTE) == 2
        assert BUCKET_CAPACITY_ATTRIBUTE not in sample.attributes
        assert BUCKET_RATE_ATTRIBUTE not in sample.attributes



#
# # def test_respects_parent_sampled():
# #     sampler = TestSampler(
# #         settings=Settings(
# #             sample_rate=0,
# #             sample_source=SampleSource.LocalDefault,
# #             flags=0x0,
# #             buckets={},
# #             timestamp=int(time.time()),
# #             ttl=10
# #         ),
# #         local_settings=LocalSettings(trigger_mode=False),
# #         request_headers=None
# #     )
# #     ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED)
# #     sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "parent span sampled")
# #     assert sample.decision.is_sampled()
# #     assert sample.decision.is_recording()
#     # await check_counters([])
#
# # def test_respects_parent_not_sampled():
# #     sampler = TestSampler(
# #         settings=Settings(
# #             sample_rate=0,
# #             sample_source=SampleSource.LocalDefault,
# #             flags=0x0,
# #             buckets={},
# #             timestamp=int(time.time()),
# #             ttl=10
# #         ),
# #         local_settings=LocalSettings(trigger_mode=False),
# #         request_headers=None
# #     )
# #     ctxt = sampler._create_parent(trace_flags=TraceFlags.DEFAULT)
# #     sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "parent span not sampled")
# #     assert not sample.decision.is_sampled()
# #     assert not sample.decision.is_recording()
#
# def test_rejects_missing_signature_key():
#     sampler = TestSampler(
#         settings=Settings(
#             sample_rate=1_000_000,
#             sample_source=SampleSource.Remote,
#             flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS,
#             buckets={},
#             timestamp=int(time.time()),
#             ttl=10
#         ),
#         local_settings=LocalSettings(trigger_mode=True),
#         request_headers=make_request_headers({
#             "trigger-trace": True,
#             "signature": True,
#             "kvs": {"custom-key": "value"},
#         })
#     )
#     ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
#     sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "rejects missing signature key")
#     assert not sample.decision.is_sampled()
#     assert not sample.decision.is_recording()
#     assert len(sample.attributes) == 0
#     assert "auth=no-signature-key" in sampler.response_headers.x_trace_options_response
#     # await check_counters(["trace.service.request_count"])
#
# def test_rejects_bad_timestamp():
#     sampler = TestSampler(
#         settings=Settings(
#             sample_rate=1_000_000,
#             sample_source=SampleSource.Remote,
#             flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS,
#             buckets={},
#             signature_key="key",
#             timestamp=int(time.time()),
#             ttl=10
#         ),
#         local_settings = LocalSettings(trigger_mode=True),
#         request_headers=make_request_headers({
#             "trigger-trace" : True,
#             "signature" : "bad-timestamp",
#             "signature-key" : "bad-timestamp",
#             "kvs" : {
#                 "custom-key": "value",
#             }
#         })
#     )
#     ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
#     sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,"rejects bad timestamp")
#     assert not sample.decision.is_sampled()
#     assert not sample.decision.is_recording()
#     assert len(sample.attributes) == 0
#     assert "auth=bad-timestamp" in sampler.response_headers.x_trace_options_response
# #
# #     await check_counters(["trace.service.request_count"])
#
# def test_rejects_bad_signature():
#     sampler = TestSampler(
#         settings=Settings(
#             sample_rate=1_000_000,
#             sample_source=SampleSource.Remote,
#             flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS,
#             buckets={},
#             signature_key="key",
#             timestamp=int(time.time()),
#             ttl=10
#         ),
#         local_settings=LocalSettings(trigger_mode=True),
#         request_headers=make_request_headers({
#             "trigger-trace":True,
#             "signature":True,
#             "signature-key":"key2",
#             "kvs":{
#                 "custom-key": "value",
#             }
#         })
#     )
#     ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
#     sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "rejects bad signature")
#     assert not sample.decision.is_sampled()
#     assert not sample.decision.is_recording()
#     assert len(sample.attributes) == 0
#     assert "auth=bad-signature" in sampler.response_headers.x_trace_options_response
#
#     # await check_counters(["trace.service.request_count"])
#
# def test_doesnt_sample():
#     sampler = TestSampler(
#         settings=None,
#         local_settings=LocalSettings(trigger_mode=False),
#         request_headers=RequestHeaders()
#     )
#     sample = sampler.should_sample(None, 0, "doesn't sample")
#     assert not sample.decision.is_sampled()
#     assert not sample.decision.is_recording()
#     # check_counters(["trace.service.request_count"])
#
# def test_expires_after_ttl():
#     sampler = TestSampler(
#         settings=Settings(
#             sample_rate=0,
#             sample_source=SampleSource.LocalDefault,
#             flags=Flags.SAMPLE_THROUGH_ALWAYS,
#             buckets={},
#             timestamp=int(time.time()) - 60,
#             ttl=10
#         ),
#         local_settings=LocalSettings(trigger_mode=False),
#         request_headers=RequestHeaders()
#     )
#     ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
#     sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "expires after ttl")
#     assert not sample.decision.is_sampled()
#     assert not sample.decision.is_recording()
#     # check_counters(["trace.service.request_count"])
# #
# def test_respects_x_trace_options_keys_and_values():
#     sampler = TestSampler(
#         settings=Settings(
#             sample_rate=0,
#             sample_source=SampleSource.LocalDefault,
#             flags=Flags.SAMPLE_THROUGH_ALWAYS,
#             buckets={},
#             timestamp=int(time.time()),
#             ttl=10
#         ),
#         local_settings=LocalSettings(trigger_mode=False),
#         request_headers=make_request_headers({
#             "kvs": {
#                 "custom-key": "value",
#                 "sw-keys": "sw-values"
#             }
#         })
#     )
#     ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
#     sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "respects x trace options keys and values")
#     assert not sample.decision.is_sampled()
#     assert sample.decision.is_recording()
#     assert "custom-key" in sample.attributes
#     assert SW_KEYS_ATTRIBUTE in sample.attributes
#     assert "trigger-trace=not-requested" in sampler.response_headers.x_trace_options_response
#
# def test_ignores_trigger_trace():
#     sampler = TestSampler(
#         settings=Settings(
#             sample_rate=0,
#             sample_source=SampleSource.LocalDefault,
#             flags=Flags.SAMPLE_THROUGH_ALWAYS,
#             buckets={},
#             timestamp=int(time.time()),
#             ttl=120
#         ),
#         local_settings=LocalSettings(trigger_mode=True),
#         request_headers=make_request_headers({
#             "trigger-trace": True,
#             "kvs": {
#                 "custom-key": "value",
#                 "invalid-key": "value"
#             }
#         })
#     )
#     ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
#     sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "ignore trigger trace", SpanKind.INTERNAL, None, None, get_current_span(ctxt).get_span_context().trace_state )
#     assert "custom-key" in sample.attributes
#     assert "trigger-trace=ignored" in sampler.response_headers.x_trace_options_response
#     assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response
#
#
# @pytest.fixture
# def sample_through_always_set():
#     return TestSampler(
#         settings=Settings(
#             sample_rate=0,
#             sample_source=SampleSource.LocalDefault,
#             flags=Flags.SAMPLE_THROUGH_ALWAYS,
#             buckets={},
#             timestamp=int(time.time()),
#             ttl=10
#         ),
#         local_settings=LocalSettings(trigger_mode=False),
#         request_headers=RequestHeaders()
#     )
#
# def test_respects_parent_sampled(sample_through_always_set):
#     ctxt = sample_through_always_set._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
#     sample = sample_through_always_set.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "parent span sampled")
#     assert sample.decision.is_sampled()
#     assert sample.decision.is_recording()
#
# def test_respects_parent_not_sampled(sample_through_always_set):
#     ctxt = sample_through_always_set._create_parent(trace_flags=TraceFlags.DEFAULT, is_remote=True, sw=False)
#     sample = sample_through_always_set.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "parent span not sampled")
#     assert not sample.decision.is_sampled()
#     assert sample.decision.is_recording()
#
#
#
# ############################################################################################
# #
# # def test_entry_span_with_valid_sw_context():
# #     sampler = TestSampler(
# #         settings={
# #             "sampleRate": 0,
# #             "sampleSource": SampleSource.LocalDefault,
# #             "flags": Flags.SAMPLE_THROUGH_ALWAYS,
# #             "buckets": {},
# #             "timestamp": round(time.time()),
# #             "ttl": 10
# #         },
# #         localSettings={"triggerMode": False},
# #         requestHeaders={}
# #     )
# #     parent = make_span(remote=True, sw=True, sampled=True)
# #     params = make_sample_params(parent=parent)
# #     sample = sampler.should_sample(*params)
# #     assert sample.decision == SamplingDecision.RECORD_AND_SAMPLED
# #     assert "sw.tracestate_parent_id" in sample.attributes
# #     check_counters([
# #         "trace.service.request_count",
# #         "trace.service.tracecount",
# #         "trace.service.through_trace_count"
# #     ])
# #
# # def test_sample_through_always_unset():
# #     sampler = TestSampler(
# #         settings={
# #             "sampleRate": 0,
# #             "sampleSource": SampleSource.LocalDefault,
# #             "flags": 0x0,
# #             "buckets": {},
# #             "timestamp": round(time.time()),
# #             "ttl": 10
# #         },
# #         localSettings={"triggerMode": False},
# #         requestHeaders={}
# #     )
# #     parent = make_span(remote=True, sw=True, sampled=True)
# #     params = make_sample_params(parent=parent)
# #     sample = sampler.should_sample(*params)
# #     assert sample.decision == SamplingDecision.NOT_RECORD
# #     check_counters(["trace.service.request_count"])
# #
# # def test_trigger_trace_requested():
# #     sampler = TestSampler(
# #         settings={
# #             "sampleRate": 0,
# #             "sampleSource": SampleSource.LocalDefault,
# #             "flags": Flags.SAMPLE_START | Flags.TRIGGERED_TRACE,
# #             "buckets": {
# #                 "TriggerStrict": {"capacity": 10, "rate": 5},
# #                 "TriggerRelaxed": {"capacity": 0, "rate": 0}
# #             },
# #             "timestamp": round(time.time()),
# #             "ttl": 10
# #         },
# #         localSettings={"triggerMode": True},
# #         requestHeaders=make_request_headers(
# #             triggerTrace=True,
# #             kvs={"custom-key": "value", "sw-keys": "sw-values"}
# #         )
# #     )
# #     parent = make_span(remote=True, sampled=True)
# #     params = make_sample_params(parent=parent)
# #     sample = sampler.should_sample(*params)
# #     assert sample.decision == SamplingDecision.RECORD_AND_SAMPLED
# #     assert "custom-key" in sample.attributes
# #     assert "sw-values" in sample.attributes
# #     assert "BucketCapacity" in sample.attributes
# #     assert "BucketRate" in sample.attributes
# #     assert "trigger-trace=ok" in sampler.response_headers["X-Trace-Options-Response"]
# #     check_counters([
# #         "trace.service.request_count",
# #         "trace.service.tracecount",
# #         "trace.service.triggered_trace_count"
# #     ])
# #
# # def test_dice_roll():
# #     sampler = TestSampler(
# #         settings={
# #             "sampleRate": 1_000_000,
# #             "sampleSource": SampleSource.Remote,
# #             "flags": Flags.SAMPLE_START,
# #             "buckets": {BucketType.DEFAULT: {"capacity": 10, "rate": 5}},
# #             "timestamp": round(time.time()),
# #             "ttl": 10
# #         },
# #         localSettings={"triggerMode": False},
# #         requestHeaders={}
# #     )
# #     params = make_sample_params(parent=False)
# #     sample = sampler.should_sample(*params)
# #     assert sample.decision == SamplingDecision.RECORD_AND_SAMPLED
# #     assert "SampleRate" in sample.attributes
# #     assert "SampleSource" in sample.attributes
# #     assert "BucketCapacity" in sample.attributes
# #     assert "BucketRate" in sample.attributes
# #     check_counters([
# #         "trace.service.request_count",
# #         "trace.service.samplecount",
# #         "trace.service.tracecount"
# #     ])
# #
# # def test_missing_settings():
# #     sampler = TestSampler(
# #         settings=False,
# #         localSettings={'triggerMode': False},
# #         requestHeaders={}
# #     )
# #
# #     params = make_sample_params(parent=False)
# #     sample = sampler.should_sample(*params)
# #     assert sample.decision == SamplingDecision.NOT_RECORD
# #     check_counters(["trace.service.request_count"])
# #
# # def test_expires_after_ttl():
# #     sampler = TestSampler(
# #         settings={
# #             'sampleRate': 0,
# #             'sampleSource': SampleSource.LocalDefault,
# #             'flags': Flags.SAMPLE_THROUGH_ALWAYS,
# #             'buckets': {},
# #             'timestamp': round(time.time()) - 60,
# #             'ttl': 10
# #         },
# #         localSettings={'triggerMode': False},
# #         requestHeaders={}
# #     )
# #
# #     parent = make_span(remote=True, sw=True, sampled=True)
# #     params = make_sample_params(parent=parent)
# #
# #     sleep(10)
# #     sample = sampler.should_sample(*params)
# #     assert sample.decision == SamplingDecision.NOT_RECORD
# #     check_counters(["trace.service.request_count"])
# #
# # def test_respects_x_trace_options_keys_and_values():
# #     sampler = TestSampler(
# #         settings=False,
# #         localSettings={'triggerMode': False},
# #         requestHeaders=make_request_headers(
# #             kvs={"custom-key": "value", "sw-keys": "sw-values"}
# #         )
# #     )
# #
# #     params = make_sample_params(parent=False)
# #     sample = sampler.should_sample(*params)
# #     assert "custom-key" in sample.attributes
# #     assert "sw-values" in sample.attributes
# #     assert "trigger-trace=not-requested" in sampler.response_headers["X-Trace-Options-Response"]
# #
# # def test_ignores_trigger_trace():
# #     sampler = TestSampler(
# #         settings=False,
# #         localSettings={'triggerMode': True},
# #         requestHeaders=make_request_headers(
# #             triggerTrace=True,
# #             kvs={"custom-key": "value", "invalid-key": "value"}
# #         )
# #     )
# #
# #     params = make_sample_params(parent=False)
# #     sample = sampler.should_sample(*params)
# #     assert "custom-key" in sample.attributes
# #     assert "trigger-trace=settings-not-available" in sampler.response_headers["X-Trace-Options-Response"]
# #     assert "ignored=invalid-key" in sampler.response_headers["X-Trace-Options-Response"]
# #
# # def test_entry_span_with_valid_sw_context():
# #     sampler = TestSampler(
# #         settings={
# #             'sampleRate': 0,
# #             'sampleSource': SampleSource.LocalDefault,
# #             'flags': Flags.SAMPLE_THROUGH_ALWAYS,
# #             'buckets': {},
# #             'timestamp': round(time.time()),
# #             'ttl': 10
# #         },
# #         localSettings={'triggerMode': False},
# #         requestHeaders={}
# #     )
# #
# #     parent = make_span(remote=True, sw=True, sampled=True)
# #     params = make_sample_params(parent=parent)
# #
# #     sample = sampler.should_sample(*params)
# #     assert sample.decision == SamplingDecision.RECORD_AND_SAMPLED
# #     assert "sw.tracestate_parent_id" in sample.attributes
# #     check_counters([
# #         "trace.service.request_count",
# #         "trace.service.tracecount",
# #         "trace.service.through_trace_count"
# #     ])
# #
# # def test_sample_through_always_unset():
# #     sampler = TestSampler(
# #         settings={
# #             'sampleRate': 0,
# #             'sampleSource': SampleSource.LocalDefault,
# #             'flags': 0x0,
# #             'buckets': {},
# #             'timestamp': round(time.time()),
# #             'ttl': 10
# #         },
# #         localSettings={'triggerMode': False},
# #         requestHeaders={}
# #     )
# #
# #     parent = make_span(remote=True, sw=True, sampled=True)
# #     params = make_sample_params(parent=parent)
# #
# #     sample = sampler.should_sample(*params)
# #     assert sample.decision == SamplingDecision.NOT_RECORD
# #     check_counters(["trace.service.request_count"])
# #
# # def test_trigger_trace_requested():
# #     sampler = TestSampler(
# #         settings={
# #             'sampleRate': 0,
# #             'sampleSource': SampleSource.LocalDefault,
# #             'flags': Flags.SAMPLE_START | Flags.TRIGGERED_TRACE,
# #             'buckets': {
# #                 'TriggerStrict': {'capacity': 10, 'rate': 5},
# #                 'TriggerRelaxed': {'capacity': 0, 'rate': 0}
# #             },
# #             'timestamp': round(time.time()),
# #             'ttl': 10
# #         },
# #         localSettings={'triggerMode': True},
# #         requestHeaders=make_request_headers(
# #             triggerTrace=True,
# #             kvs={"custom-key": "value", "sw-keys": "sw-values"}
# #         )
# #     )
# #
# #     parent = make_span(remote=True, sampled=True)
# #     params = make_sample_params(parent=parent)
# #
# #     sample = sampler.should_sample(*params)
# #     assert sample.decision == SamplingDecision.RECORD_AND_SAMPLED
# #     assert "custom-key" in sample.attributes
# #     assert "sw-values" in sample.attributes
# #     assert "BucketCapacity" in sample.attributes
# #     assert "BucketRate" in sample.attributes
# #     assert "trigger-trace=ok" in sampler.response_headers["X-Trace-Options-Response"]
# #     check_counters([
# #         "trace.service.request_count",
# #         "trace.service.tracecount",
# #         "trace.service.triggered_trace_count"
# #     ])
# #
# # def test_dice_roll():
# #     sampler = TestSampler(
# #         settings={
# #             'sampleRate': 1_000_000,
# #             'sampleSource': SampleSource.Remote,
# #             'flags': Flags.SAMPLE_START,
# #             'buckets': {BucketType.DEFAULT: {'capacity': 10, 'rate': 5}},
# #             'timestamp': round(time.time()),
# #             'ttl': 10
# #         },
# #         localSettings={'triggerMode': False},
# #         requestHeaders={}
# #     )
# #
# #     params = make_sample_params(parent=False)
# #     sample = sampler.should_sample(*params)
# #     assert sample.decision == SamplingDecision.RECORD_AND_SAMPLED
# #     assert "SampleRate" in sample.attributes
# #     assert "SampleSource" in sample.attributes
# #     assert "BucketCapacity" in sample.attributes
# #     assert "BucketRate" in sample.attributes
# #     check_counters([
# #         "trace.service.request_count",
# #         "trace.service.samplecount",
# #         "trace.service.tracecount"
# #     ])