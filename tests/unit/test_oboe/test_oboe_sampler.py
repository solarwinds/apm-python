# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from collections.abc import Sequence


import pytest
from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider, AlwaysOnExemplarFilter
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.resources import Attributes
from opentelemetry.sdk.trace import RandomIdGenerator
from opentelemetry.trace import SpanKind, Link, TraceState, TraceFlags, get_current_span
from typing_extensions import override

from solarwinds_apm.apm_constants import INTL_SWO_X_OPTIONS_RESPONSE_KEY
from solarwinds_apm.oboe.oboe_sampler import OboeSampler, SW_KEYS_ATTRIBUTE, \
    BUCKET_RATE_ATTRIBUTE, BUCKET_CAPACITY_ATTRIBUTE, SAMPLE_RATE_ATTRIBUTE, SAMPLE_SOURCE_ATTRIBUTE, TRACESTATE_CAPTURE_ATTRIBUTE
from solarwinds_apm.oboe.settings import LocalSettings, Settings, SampleSource, Flags, BucketType, BucketSettings
from solarwinds_apm.oboe.trace_options import RequestHeaders, ResponseHeaders


class MakeRequestHeaders:
    def __init__(self, trigger_trace: bool | None = None, kvs: dict | None = None, signature=None,
                 signature_key: str | None = None):
        self._trigger_trace = trigger_trace
        self._kvs = kvs
        self._signature = signature
        self._signature_key = signature_key

    @property
    def trigger_trace(self) -> bool | None:
        return self._trigger_trace

    @property
    def kvs(self) -> dict | None:
        return self._kvs

    @property
    def signature(self) -> str | None:
        return self._signature

    @property
    def signature_key(self) -> str | None:
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
    headers = RequestHeaders(x_trace_options=";".join(filter(None, [trigger_trace, *kvs, ts])),
                             x_trace_options_signature=None)
    if options.signature:
        key = options.signature_key if options.signature_key else os.urandom(8).hex()
        headers.x_trace_options_signature = hmac.new(str.encode(key), str.encode(headers.x_trace_options),
                                                     hashlib.sha1).hexdigest()
    return headers


def check_counters(sampler, counter_names):
    counters = set(counter_names)
    sampler.metric_reader.collect()
    if counters == set():
        assert sampler.metric_reader.get_metrics_data() is None
    else:
        assert len(sampler.metric_reader.get_metrics_data().resource_metrics) == 1
        assert len(sampler.metric_reader.get_metrics_data().resource_metrics[0].scope_metrics) == 1
        scope_metrics_data = sampler.metric_reader.get_metrics_data().resource_metrics[0].scope_metrics[0].metrics
        assert len(counter_names) == len(scope_metrics_data)
        for m in scope_metrics_data:
            assert m.name in counters
            counters.discard(m.name)
            assert len(m.data.data_points) == 1
            assert m.data.data_points[0].value == 1
        assert counters == set()


class TestSamplerOptions:
    def __init__(self, settings: Settings | None = None, local_settings: LocalSettings | None = None,
                 request_headers: RequestHeaders | None = None):
        self._settings = settings
        self._local_settings = local_settings
        self._request_headers = request_headers

    @property
    def settings(self) -> Settings | None:
        return self._settings

    @property
    def local_settings(self) -> LocalSettings | None:
        return self._local_settings

    @property
    def request_headers(self) -> RequestHeaders | None:
        return self._request_headers


class TestSampler(OboeSampler):
    def __init__(self, options: TestSamplerOptions):
        self._metric_reader = InMemoryMetricReader()
        meter_provider = MeterProvider(
            metric_readers=[self._metric_reader],
            exemplar_filter=AlwaysOnExemplarFilter()
        )
        super().__init__(meter_provider=meter_provider)
        self._local_settings = options.local_settings
        self._request_headers = options.request_headers
        if options.settings:
            self.update_settings(options.settings)
        self._response_headers = None

    def _create_parent(self, trace_flags: trace.TraceFlags, is_remote=False, sw=None, other_trace_state=False, xtrace_options_response=False) -> Context | None:
        if trace_flags is None:
            return None
        return trace.set_span_in_context(self._create_parent_span(trace_flags, is_remote, sw, other_trace_state, xtrace_options_response))

    @staticmethod
    def _create_parent_span(trace_flags: trace.TraceFlags, is_remote=False, sw=None, other_trace_state=False, xtrace_options_response=False) -> trace.NonRecordingSpan:
        generator = RandomIdGenerator()
        trace_id = generator.generate_trace_id()
        span_id = generator.generate_span_id()
        trace_state = None
        if isinstance(sw, str) and sw == "inverse":
            trace_state = TraceState(
                [("sw", format(span_id, "016x") + "-0" + ("0" if trace_flags == TraceFlags.SAMPLED else "1"))])
        elif isinstance(sw, bool):
            trace_state = TraceState(
                [("sw", format(span_id, "016x") + "-0" + ("1" if trace_flags == TraceFlags.SAMPLED else "0"))])
        if other_trace_state:
            if trace_state is None:
                trace_state = TraceState()
            trace_state = trace_state.add("vendor1", "value1").add("vendor2", "value2")
        if xtrace_options_response:
            if trace_state is None:
                trace_state = TraceState()
            trace_state = trace_state.add(INTL_SWO_X_OPTIONS_RESPONSE_KEY, "response")

        span_context = trace.SpanContext(trace_id=trace_id, span_id=span_id, is_remote=is_remote,
                                         trace_flags=trace_flags, trace_state=trace_state)
        return trace.NonRecordingSpan(span_context)

    @override
    def local_settings(self,
                       parent_context: "Context" | None,
                       trace_id: int,
                       name: str,
                       kind: SpanKind | None = None,
                       attributes: Attributes = None,
                       links: Sequence["Link"] | None = None,
                       trace_state: "TraceState" | None = None) -> LocalSettings:
        return self._local_settings

    @override
    def request_headers(self,
                        parent_context: "Context" | None,
                        trace_id: int,
                        name: str,
                        kind: SpanKind | None = None,
                        attributes: Attributes = None,
                        links: Sequence["Link"] | None = None,
                        trace_state: "TraceState" | None = None
                        ) -> RequestHeaders:
        return self._request_headers

    @override
    def set_response_headers(self,
                             headers: ResponseHeaders,
                             parent_context: "Context" | None,
                             trace_id: int,
                             name: str,
                             kind: SpanKind | None = None,
                             attributes: Attributes = None,
                             links: Sequence["Link"] | None = None,
                             trace_state: "TraceState" | None = None
                             ) -> "TraceState" | None:
        self._response_headers = headers
        return None

    @property
    def response_headers(self):
        return self._response_headers

    @property
    def metric_reader(self):
        return self._metric_reader

    def __str__(self):
        return f"Test Sampler"


class TestInvalidXTraceOptionsSignature:
    def test_rejects_missing_signature_key(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=1_000_000,
                sample_source=SampleSource.REMOTE,
                flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, signature=True, kvs={"custom-key": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "rejects_missing_signature_key")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()
        assert sample.attributes == {}
        assert "auth=no-signature-key" in sampler.response_headers.x_trace_options_response
        check_counters(sampler, ["trace.service.request_count"])

    def test_rejects_bad_timestamp(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=1_000_000,
                sample_source=SampleSource.REMOTE,
                flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key="key",
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, signature="bad-timestamp", signature_key="key",
                                   kvs={"custom-key": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "rejects_bad_timestamp")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()
        assert sample.attributes == {}
        assert "auth=bad-timestamp" in sampler.response_headers.x_trace_options_response
        check_counters(sampler, ["trace.service.request_count"])

    def test_rejects_bad_signature(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=1_000_000,
                sample_source=SampleSource.REMOTE,
                flags=Flags.SAMPLE_START | Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key="key1",
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, signature=True, signature_key="key2",
                                   kvs={"custom-key": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "rejects_bad_signature")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()
        assert sample.attributes == {}
        assert "auth=bad-signature" in sampler.response_headers.x_trace_options_response
        check_counters(sampler, ["trace.service.request_count"])


class TestMissingSettings:
    def test_does_not_sample(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=None,
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        generator = RandomIdGenerator()
        sample = sampler.should_sample(None, generator.generate_trace_id(), "does_not_sample")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()
        check_counters(sampler, ["trace.service.request_count"])

    def test_expires_after_ttl(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
                flags=Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()) - 60,
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id, "expires_after_ttl")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()
        check_counters(sampler, ["trace.service.request_count"])

    def test_respects_x_trace_options_keys_and_values(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=None,
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(kvs={"custom-key": "value", "sw-keys": "sw-values"}))
        ))
        generator = RandomIdGenerator()
        sample = sampler.should_sample(None, generator.generate_trace_id(), "respects_x_trace_options_keys_and_values")
        assert sample.attributes == {"custom-key": "value", SW_KEYS_ATTRIBUTE: "sw-values"}
        assert "trigger-trace=not-requested" in sampler.response_headers.x_trace_options_response

    def test_ignores_trigger_trace(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=None,
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, kvs={"custom-key": "value", "invalid-keys": "value"}))
        ))
        generator = RandomIdGenerator()
        sample = sampler.should_sample(None, generator.generate_trace_id(), "ignores_trigger_trace")
        assert sample.attributes == {"custom-key": "value"}
        assert "trigger-trace=settings-not-available" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response

class TestEntrySpan:
    def test_sw_w3c_tracestate_with_x_trace_options_response(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
                flags=Flags.SAMPLE_START,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True, other_trace_state=True, xtrace_options_response=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "respects_parent_sampled", None, None, None, None)
        assert "vendor2=value2,vendor1=value1" in sample.attributes.get(TRACESTATE_CAPTURE_ATTRIBUTE)
        assert "sw=" in sample.attributes.get(TRACESTATE_CAPTURE_ATTRIBUTE)
        assert INTL_SWO_X_OPTIONS_RESPONSE_KEY not in sample.attributes.get(TRACESTATE_CAPTURE_ATTRIBUTE)

    def test_sw_w3c_tracestate_without_x_trace_options_response(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
                flags=Flags.SAMPLE_START,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True, other_trace_state=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "respects_parent_sampled", None, None, None, None)
        assert "vendor2=value2,vendor1=value1" in sample.attributes.get(TRACESTATE_CAPTURE_ATTRIBUTE)
        assert "sw=" in sample.attributes.get(TRACESTATE_CAPTURE_ATTRIBUTE)
        assert INTL_SWO_X_OPTIONS_RESPONSE_KEY not in sample.attributes.get(TRACESTATE_CAPTURE_ATTRIBUTE)


class TestEntrySpanWithValidSwContextXTraceOptions:
    def test_respects_keys_and_values(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
                flags=Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(kvs={"custom-key": "value", "sw-keys": "sw-values"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "respects_keys_and_values")
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(SW_KEYS_ATTRIBUTE) == "sw-values"
        assert "trigger-trace=not-requested" in sampler.response_headers.x_trace_options_response

    def test_ignores_trigger_trace(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
                flags=Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, kvs={"custom-key": "value", "invalid-keys": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "ignores_trigger_trace")
        assert sample.attributes.get("custom-key") == "value"
        assert "trigger-trace=ignored" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response


class TestEntrySpanWithValidSwContextSampleThroughAlwaysSet:
    @pytest.fixture()
    def sample_through_always_set(self):
        return TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
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
        sample = sample_through_always_set.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                                         "respects_parent_sampled")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("sw.tracestate_parent_id") == format(
            get_current_span(ctxt).get_span_context().span_id, "016x")
        check_counters(sample_through_always_set,
                       ["trace.service.request_count", "trace.service.tracecount", "trace.service.through_trace_count"])

    def test_respects_parent_not_sampled(self, sample_through_always_set):
        ctxt = sample_through_always_set._create_parent(trace_flags=TraceFlags.DEFAULT, is_remote=True, sw=True)
        sample = sample_through_always_set.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                                         "respects_parent_not_sampled")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("sw.tracestate_parent_id") == format(
            get_current_span(ctxt).get_span_context().span_id, "016x")
        check_counters(sample_through_always_set, ["trace.service.request_count"])

    def test_respects_sw_sampled_over_w3c_not_sampled(self, sample_through_always_set):
        ctxt = sample_through_always_set._create_parent(trace_flags=TraceFlags.DEFAULT, is_remote=True, sw="inverse")
        sample = sample_through_always_set.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                                         "respects_sw_sampled_over_w3c_not_sampled")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("sw.tracestate_parent_id") == format(
            get_current_span(ctxt).get_span_context().span_id, "016x")
        check_counters(sample_through_always_set,
                       ["trace.service.request_count", "trace.service.tracecount", "trace.service.through_trace_count"])

    def test_respects_sw_not_sampled_over_w3c_sampled(self, sample_through_always_set):
        ctxt = sample_through_always_set._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True, sw="inverse")
        sample = sample_through_always_set.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                                         "respects_sw_not_sampled_over_w3c_sampled")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("sw.tracestate_parent_id") == format(
            get_current_span(ctxt).get_span_context().span_id, "016x")
        check_counters(sample_through_always_set, ["trace.service.request_count"])


class TestEntrySpanWithValidSwContextSampleThroughAlwaysUnset:
    def test_records_but_does_not_sample_when_SAMPLE_START_set(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
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
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "respects_sw_not_sampled_over_w3c_sampled")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        check_counters(sampler, ["trace.service.request_count"])

    def test_does_not_record_or_sample_when_SAMPLE_START_unset(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
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
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "does_not_record_or_sample_when_SAMPLE_START_unset")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()
        check_counters(sampler, ["trace.service.request_count"])


class TestTriggerTraceRequestedTriggeredTraceSetUnsigned:
    def test_records_and_samples_when_there_is_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
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
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, kvs={"custom-key": "value", "sw-keys": "sw-values"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "records_and_samples_when_there_is_capacity")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(SW_KEYS_ATTRIBUTE) == "sw-values"
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 10
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 5
        assert "trigger-trace=ok" in sampler.response_headers.x_trace_options_response
        check_counters(sampler, ["trace.service.request_count", "trace.service.tracecount",
                                 "trace.service.triggered_trace_count"])

    def test_records_but_does_not_sample_when_there_is_no_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
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
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, kvs={"custom-key": "value", "invalid-keys": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "records_but_does_not_sample_when_there_is_no_capacity")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 0
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 0
        assert "trigger-trace=rate-exceeded" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response
        check_counters(sampler, ["trace.service.request_count"])


class TestTriggerTraceRequestedTriggeredTraceSetSigned:
    def test_records_and_samples_when_there_is_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
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
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, signature=True, signature_key="key",
                                   kvs={"custom-key": "value", "sw-keys": "sw-values"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "records_and_samples_when_there_is_capacity")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(SW_KEYS_ATTRIBUTE) == "sw-values"
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 20
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 10
        assert "auth=ok" in sampler.response_headers.x_trace_options_response
        assert "trigger-trace=ok" in sampler.response_headers.x_trace_options_response
        check_counters(sampler, ["trace.service.request_count", "trace.service.tracecount",
                                 "trace.service.triggered_trace_count"])

    def test_records_but_does_not_sample_when_there_is_no_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
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
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, signature=True, signature_key="key",
                                   kvs={"custom-key": "value", "invalid-keys": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "records_but_does_not_sample_when_there_is_no_capacity")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 0
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 0
        assert "trigger-trace=rate-exceeded" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response
        check_counters(sampler, ["trace.service.request_count"])


class TestTriggerTraceRequestedTriggeredTraceUnset:
    def test_record_but_does_not_sample_when_TRIGGERED_TRACE_unset(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
                flags=Flags.SAMPLE_START,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, kvs={"custom-key": "value", "invalid-keys": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "record_but_does_not_sample_when_TRIGGERED_TRACE_unset")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get("custom-key") == "value"
        assert "trigger-trace=trigger-tracing-disabled" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response
        check_counters(sampler, ["trace.service.request_count"])


class TestTriggerTraceRequestedDiceRoll:
    def test_respects_x_trace_options_keys_and_values(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
                flags=Flags.SAMPLE_START,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(kvs={"custom-key": "value", "sw-keys": "sw-values"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.DEFAULT, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "respects_x_trace_options_keys_and_values")
        assert sample.attributes.get("custom-key") == "value"
        assert sample.attributes.get(SW_KEYS_ATTRIBUTE) == "sw-values"
        assert "trigger-trace=not-requested" in sampler.response_headers.x_trace_options_response

    def test_records_and_samples_when_dice_success_and_sufficient_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=1_000_000,
                sample_source=SampleSource.REMOTE,
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
        sample = sampler.should_sample(None, generator.generate_trace_id(),
                                       "records_and_samples_when_dice_success_and_sufficient_capacity")
        assert sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get(SAMPLE_RATE_ATTRIBUTE) == 1_000_000
        assert sample.attributes.get(SAMPLE_SOURCE_ATTRIBUTE) == 6
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 10
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 5
        check_counters(sampler,
                       ["trace.service.request_count", "trace.service.samplecount", "trace.service.tracecount"])

    def test_records_but_does_not_sample_when_dice_success_but_insufficient_capacity(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=1_000_000,
                sample_source=SampleSource.REMOTE,
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
        sample = sampler.should_sample(None, generator.generate_trace_id(),
                                       "records_but_does_not_sample_when_dice_success_but_insufficient_capacity")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get(SAMPLE_RATE_ATTRIBUTE) == 1_000_000
        assert sample.attributes.get(SAMPLE_SOURCE_ATTRIBUTE) == 6
        assert sample.attributes.get(BUCKET_CAPACITY_ATTRIBUTE) == 0
        assert sample.attributes.get(BUCKET_RATE_ATTRIBUTE) == 0
        check_counters(sampler, ["trace.service.request_count", "trace.service.samplecount",
                                 "trace.service.tokenbucket_exhaustion_count"])

    def test_records_but_does_not_sample_when_dice_failure(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
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
        sample = sampler.should_sample(None, generator.generate_trace_id(),
                                       "records_but_does_not_sample_when_dice_failure")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        assert sample.attributes.get(SAMPLE_RATE_ATTRIBUTE) == 0
        assert sample.attributes.get(SAMPLE_SOURCE_ATTRIBUTE) == 2
        assert BUCKET_CAPACITY_ATTRIBUTE not in sample.attributes
        assert BUCKET_RATE_ATTRIBUTE not in sample.attributes
        check_counters(sampler, ["trace.service.request_count", "trace.service.samplecount"])


class TestTriggerTraceRequestedSampleStartUnset:
    def test_ignores_trigger_trace(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
                flags=Flags.OK,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(
                MakeRequestHeaders(trigger_trace=True, kvs={"custom-key": "value", "invalid-keys": "value"}))
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "ignores_trigger_trace")
        assert sample.attributes.get("custom-key") == "value"
        assert "trigger-trace=tracing-disabled" in sampler.response_headers.x_trace_options_response
        assert "ignored=invalid-key" in sampler.response_headers.x_trace_options_response

    def test_records_when_SAMPLE_THROUGH_ALWAYS_set(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
                flags=Flags.SAMPLE_THROUGH_ALWAYS,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=True, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "records_when_SAMPLE_THROUGH_ALWAYS_set")
        assert not sample.decision.is_sampled()
        assert sample.decision.is_recording()
        check_counters(sampler, ["trace.service.request_count"])

    def test_does_not_record_when_SAMPLE_THROUGH_ALWAYS_unset(self):
        sampler = TestSampler(TestSamplerOptions(
            settings=Settings(
                sample_rate=0,
                sample_source=SampleSource.LOCAL_DEFAULT,
                flags=Flags.OK,
                buckets={},
                signature_key=None,
                timestamp=int(time.time()),
                ttl=10
            ),
            local_settings=LocalSettings(trigger_mode=False, tracing_mode=None),
            request_headers=make_request_headers(MakeRequestHeaders())
        ))
        ctxt = sampler._create_parent(trace_flags=TraceFlags.SAMPLED, is_remote=True)
        sample = sampler.should_sample(ctxt, get_current_span(ctxt).get_span_context().trace_id,
                                       "does_not_record_when_SAMPLE_THROUGH_ALWAYS_unset")
        assert not sample.decision.is_sampled()
        assert not sample.decision.is_recording()
        check_counters(sampler, ["trace.service.request_count"])
