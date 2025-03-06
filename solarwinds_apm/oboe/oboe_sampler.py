# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

import logging
import re
import time
from abc import ABC, abstractmethod
from enum import IntEnum, auto
from typing import Optional, Sequence

from opentelemetry.context import Context
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.sampling import (
    Decision,
    Attributes,
    Sampler,
    SamplingResult,
)
from opentelemetry.trace import Link, SpanKind, get_current_span
from opentelemetry.trace import TraceFlags
from opentelemetry.trace.span import Span
from opentelemetry.trace.span import TraceState
from typing_extensions import override

from solarwinds_apm.oboe.dice import _Dice
from solarwinds_apm.oboe.metrics import Counters
from solarwinds_apm.oboe.settings import BucketType, Flags, LocalSettings, merge, Settings
from solarwinds_apm.oboe.token_bucket import _TokenBucket
from solarwinds_apm.oboe.trace_options import (
    Auth,
    parse_trace_options,
    ResponseHeaders,
    stringify_trace_options_response,
    TriggerTrace,
    validate_signature, TraceOptionsWithResponse,
)
from solarwinds_apm.oboe.trace_options import RequestHeaders, TraceOptionsResponse

TRACESTATE_REGEXP = r"^[0-9a-f]{16}-[0-9a-f]{2}$"
DICE_SCALE = 1_000_000

SW_KEYS_ATTRIBUTE = "SWKeys"
PARENT_ID_ATTRIBUTE = "sw.tracestate_parent_id"
SAMPLE_RATE_ATTRIBUTE = "SampleRate"
SAMPLE_SOURCE_ATTRIBUTE = "SampleSource"
BUCKET_CAPACITY_ATTRIBUTE = "BucketCapacity"
BUCKET_RATE_ATTRIBUTE = "BucketRate"
TRIGGERED_TRACE_ATTRIBUTE = "TriggeredTrace"


class SpanType(IntEnum):
    ROOT = auto()
    ENTRY = auto()
    LOCAL = auto()


class SampleState:
    def __init__(self,
                 decision: Decision,
                 attributes: Attributes,

                 settings: Optional[Settings],
                 trace_state: Optional[str],
                 headers: RequestHeaders,
                 trace_options: Optional[TraceOptionsWithResponse]):
        self._decision = decision
        self._attributes = attributes
        self._settings = settings
        self._trace_state = trace_state
        self._headers = headers
        self._trace_options = trace_options

    @property
    def decision(self) -> Decision:
        return self._decision

    @decision.setter
    def decision(self, value: Decision):
        self._decision = value

    @property
    def attributes(self) -> Attributes:
        return self._attributes

    @attributes.setter
    def attributes(self, value: Attributes):
        self._attributes = value

    @property
    def settings(self) -> Optional[Settings]:
        return self._settings

    @settings.setter
    def settings(self, value: Optional[Settings]):
        self._settings = value

    @property
    def trace_state(self) -> Optional[str]:
        return self._trace_state

    @trace_state.setter
    def trace_state(self, value: Optional[str]):
        self._trace_state = value

    @property
    def headers(self) -> RequestHeaders:
        return self._headers

    @headers.setter
    def headers(self, value: RequestHeaders):
        self._headers = value

    @property
    def trace_options(self) -> Optional[TraceOptionsWithResponse]:
        return self._trace_options

    @trace_options.setter
    def trace_options(self, value: Optional[TraceOptionsWithResponse]):
        self._trace_options = value


def _span_type(parent_span: Optional[Span] = None) -> SpanType:
    parent_span_context = parent_span.get_span_context() if parent_span else None
    if parent_span_context is None or not parent_span_context.is_valid:
        return SpanType.ROOT
    elif parent_span_context.is_remote:
        return SpanType.ENTRY
    else:
        return SpanType.LOCAL


class OboeSampler(Sampler, ABC):
    def __init__(self, meter_provider: MeterProvider, logger: logging.Logger):
        self._logger = logger
        self._counters = Counters(meter_provider=meter_provider)
        self._buckets = {
            BucketType.DEFAULT: _TokenBucket(),
            BucketType.TRIGGER_RELAXED: _TokenBucket(),
            BucketType.TRIGGER_STRICT: _TokenBucket(),
        }
        self._settings: Optional[Settings] = None

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, new_logger):
        self._logger = new_logger

    @property
    def counters(self):
        return self._counters

    @counters.setter
    def counters(self, new_counters):
        self._counters = new_counters

    @property
    def buckets(self):
        return self._buckets

    @buckets.setter
    def buckets(self, new_buckets):
        self._buckets = new_buckets

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, new_settings):
        self._settings = new_settings

    @override
    def should_sample(
            self,
            parent_context: Optional["Context"],
            trace_id: int,
            name: str,
            kind: Optional[SpanKind] = None,
            attributes: Attributes = None,
            links: Optional[Sequence["Link"]] = None,
            trace_state: Optional["TraceState"] = None,
    ) -> "SamplingResult":
        parent_span = get_current_span(parent_context)
        span_type = _span_type(parent_span)
        self.logger.debug(f"span type is {SpanType(span_type).name}")
        if span_type == SpanType.LOCAL:
            if parent_span and parent_span.get_span_context().trace_flags & TraceFlags.SAMPLED:
                return SamplingResult(decision=Decision.RECORD_AND_SAMPLE)
            else:
                return SamplingResult(decision=Decision.DROP)
        s = SampleState(
            decision=Decision.DROP,
            attributes=attributes if attributes else {},

            settings=self.get_settings(parent_context, trace_id, name, kind, attributes, links, trace_state),
            trace_state=parent_span.get_span_context().trace_state.get("sw") if parent_span else None,
            headers=self.request_headers(parent_context, trace_id, name, kind, attributes, links, trace_state),
            trace_options=None,
        )
        self.counters.request_count.add(1, {}, parent_context)
        if s.headers.x_trace_options:
            parsed = parse_trace_options(s.headers.x_trace_options)
            s.trace_options = TraceOptionsWithResponse(trigger_trace=parsed.trigger_trace,
                                                       timestamp=parsed.timestamp,
                                                       sw_keys=parsed.sw_keys,
                                                       custom=parsed.custom,
                                                       ignored=parsed.ignored,
                                                       response=TraceOptionsResponse(auth=None, trigger_trace=None,
                                                                                     ignored=None))
            self.logger.debug("X-Trace-Options present", s.trace_options)
            if s.headers.x_trace_options_signature:
                s.trace_options.response.auth = validate_signature(
                    s.headers.x_trace_options,
                    s.headers.x_trace_options_signature,
                    s.settings.signature_key if s.settings and s.settings.signature_key else None,
                    s.trace_options.timestamp,
                )
                if s.trace_options.response.auth != Auth.OK:
                    self.logger.debug("X-Trace-Options-Signature invalid; tracing disabled")
                    new_trace_state = self.set_response_headers_from_sample_state(s, parent_context, trace_id, name,
                                                                                  kind, attributes, links, trace_state)
                    return SamplingResult(decision=Decision.DROP, trace_state=new_trace_state)
            if not s.trace_options.trigger_trace:
                s.trace_options.response.trigger_trace = TriggerTrace.NOT_REQUESTED
            if s.trace_options.sw_keys:
                s.attributes[SW_KEYS_ATTRIBUTE] = s.trace_options.sw_keys
            for k, v in s.trace_options.custom.items():
                s.attributes[k] = v
            if len(s.trace_options.ignored) > 0:
                s.trace_options.response.ignored = [k for k, _ in s.trace_options.ignored]
        if not s.settings:
            self.logger.debug("settings unavailable; sampling disabled")
            if s.trace_options and s.trace_options.trigger_trace:
                self.logger.debug("trigger trace requested but settings unavailable")
                s.trace_options.response.trigger_trace = TriggerTrace.SETTINGS_NOT_AVAILABLE
            new_trace_state = self.set_response_headers_from_sample_state(s, parent_context, trace_id, name, kind,
                                                                          attributes, links, trace_state)
            return SamplingResult(decision=Decision.DROP, attributes=s.attributes, trace_state=new_trace_state)
        if s.trace_state and re.match(TRACESTATE_REGEXP, s.trace_state):
            self.logger.debug("context is valid for parent-based sampling")
            self.parent_based_algo(s, parent_context)
        elif s.settings.flags & Flags.SAMPLE_START:
            if s.trace_options and s.trace_options.trigger_trace:
                self.logger.debug("trigger trace requested")
                self.trigger_trace_algo(s, parent_context)
            else:
                self.logger.debug("defaulting to dice roll")
                self.dice_roll_algo(s, parent_context)
        else:
            self.logger.debug("SAMPLE_START is unset; sampling disabled")
            self.disabled_algo(s)
        self.logger.debug("final sampling state", s)
        new_trace_state = self.set_response_headers_from_sample_state(s, parent_context, trace_id, name, kind,
                                                                      attributes, links, trace_state)
        return SamplingResult(decision=s.decision, attributes=s.attributes, trace_state=new_trace_state)

    def parent_based_algo(self, s: SampleState, parent_context: Optional["Context"]):
        s.attributes[PARENT_ID_ATTRIBUTE] = s.trace_state[:16] if s.trace_state else None
        if s.trace_options and s.trace_options.trigger_trace:
            self.logger.debug("trigger trace requested but ignored")
            s.trace_options.response.trigger_trace = TriggerTrace.IGNORED

        if s.settings and s.settings.flags & Flags.SAMPLE_THROUGH_ALWAYS:
            self.logger.debug("SAMPLE_THROUGH_ALWAYS is set; parent-based sampling")
            flags = int(s.trace_state[-2:], 16)
            if flags & TraceFlags.SAMPLED:
                self.logger.debug("parent is sampled; record and sample")
                self.counters.trace_count.add(1, {}, parent_context)
                self.counters.through_trace_count.add(1, {}, parent_context)
                s.decision = Decision.RECORD_AND_SAMPLE
            else:
                self.logger.debug("parent is not sampled; record only")
                s.decision = Decision.RECORD_ONLY
        else:
            self.logger.debug("SAMPLE_THROUGH_ALWAYS is unset; sampling disabled")
            if s.settings and s.settings.flags & Flags.SAMPLE_START:
                self.logger.debug("SAMPLE_START is set; record")
                s.decision = Decision.RECORD_ONLY
            else:
                self.logger.debug("SAMPLE_START is unset; don't record")
                s.decision = Decision.DROP

    def trigger_trace_algo(self, s: SampleState, parent_context: Optional["Context"]):
        if s.settings and s.settings.flags & Flags.TRIGGERED_TRACE:
            self.logger.debug("TRIGGERED_TRACE set; trigger tracing")
            bucket: _TokenBucket
            if s.trace_options and s.trace_options.response.auth:
                self.logger.debug("signed request; using relaxed rate")
                bucket = self.buckets[BucketType.TRIGGER_RELAXED]
            else:
                self.logger.debug("unsigned request; using strict rate")
                bucket = self.buckets[BucketType.TRIGGER_STRICT]
            s.attributes[TRIGGERED_TRACE_ATTRIBUTE] = True
            s.attributes[BUCKET_CAPACITY_ATTRIBUTE] = bucket.capacity
            s.attributes[BUCKET_RATE_ATTRIBUTE] = bucket.rate
            if bucket.consume():
                self.logger.debug("sufficient capacity; record and sample")
                self.counters.triggered_trace_count.add(1, {}, parent_context)
                self.counters.trace_count.add(1, {}, parent_context)
                s.trace_options.response.trigger_trace = TriggerTrace.OK
                s.decision = Decision.RECORD_AND_SAMPLE
            else:
                self.logger.debug("insufficient capacity; record only")
                s.trace_options.response.trigger_trace = TriggerTrace.RATE_EXCEEDED
                s.decision = Decision.RECORD_ONLY
        else:
            self.logger.debug("TRIGGERED_TRACE unset; record only")
            s.trace_options.response.trigger_trace = TriggerTrace.TRIGGER_TRACING_DISABLED
            s.decision = Decision.RECORD_ONLY

    def dice_roll_algo(self, s: SampleState, parent_context: Optional["Context"]):
        dice = _Dice(rate=s.settings.sample_rate if s.settings else 0, scale=DICE_SCALE)
        s.attributes[SAMPLE_RATE_ATTRIBUTE] = dice.rate
        s.attributes[SAMPLE_SOURCE_ATTRIBUTE] = s.settings.sample_source
        self.counters.sample_count.add(1, {}, parent_context)
        if dice.roll():
            self.logger.debug("dice roll success; checking capacity")
            bucket = self.buckets[BucketType.DEFAULT]
            s.attributes[BUCKET_CAPACITY_ATTRIBUTE] = bucket.capacity
            s.attributes[BUCKET_RATE_ATTRIBUTE] = bucket.rate
            if bucket.consume():
                self.logger.debug("sufficient capacity; record and sample")
                self.counters.trace_count.add(1, {}, parent_context)
                s.decision = Decision.RECORD_AND_SAMPLE
            else:
                self.logger.debug("insufficient capacity; record only")
                self.counters.token_bucket_exhaustion_count.add(1, {}, parent_context)
                s.decision = Decision.RECORD_ONLY
        else:
            self.logger.debug("dice roll failure; record only")
            s.decision = Decision.RECORD_ONLY

    def disabled_algo(self, s: SampleState):
        if s.trace_options and s.trace_options.trigger_trace:
            self.logger.debug("trigger trace requested but tracing disabled")
            s.trace_options.response.trigger_trace = TriggerTrace.TRACING_DISABLED

        if s.settings and s.settings.flags & Flags.SAMPLE_THROUGH_ALWAYS:
            self.logger.debug("SAMPLE_THROUGH_ALWAYS is set; record")
            s.decision = Decision.RECORD_ONLY
        else:
            self.logger.debug("SAMPLE_THROUGH_ALWAYS is unset; don't record")
            s.decision = Decision.DROP

    def update_settings(self, settings: Settings):
        if settings.timestamp > (self.settings.timestamp if self.settings else 0):
            self.settings = settings
            for t, b in self.buckets.items():
                if t in self.settings.buckets:
                    b.update(new_capacity=self.settings.buckets[t].capacity, new_rate=self.settings.buckets[t].rate)

    def get_settings(self,
                     parent_context: Optional["Context"],
                     trace_id: int,
                     name: str,
                     kind: Optional[SpanKind] = None,
                     attributes: Attributes = None,
                     links: Optional[Sequence["Link"]] = None,
                     trace_state: Optional["TraceState"] = None
                     ) -> Optional[Settings]:
        if self.settings is None:
            return None
        if time.time() > self.settings.timestamp + self.settings.ttl:
            self.logger.debug("settings expired; removing")
            self.settings = None
            return None
        return merge(self.settings,
                     self.local_settings(parent_context, trace_id, name, kind, attributes, links, trace_state))

    @abstractmethod
    def local_settings(self,
                       parent_context: Optional["Context"],
                       trace_id: int,
                       name: str,
                       kind: Optional[SpanKind] = None,
                       attributes: Attributes = None,
                       links: Optional[Sequence["Link"]] = None,
                       trace_state: Optional["TraceState"] = None,
                       ) -> LocalSettings:
        pass

    @abstractmethod
    def request_headers(self,
                        parent_context: Optional["Context"],
                        trace_id: int,
                        name: str,
                        kind: Optional[SpanKind] = None,
                        attributes: Attributes = None,
                        links: Optional[Sequence["Link"]] = None,
                        trace_state: Optional["TraceState"] = None
                        ) -> RequestHeaders:
        pass

    def set_response_headers_from_sample_state(self,
                                               s: SampleState,
                                               parent_context: Optional["Context"],
                                               trace_id: int,
                                               name: str,
                                               kind: Optional[SpanKind] = None,
                                               attributes: Attributes = None,
                                               links: Optional[Sequence["Link"]] = None,
                                               trace_state: Optional["TraceState"] = None) -> Optional["TraceState"]:
        headers = ResponseHeaders(x_trace_options_response=None)
        if s.trace_options:
            headers.x_trace_options_response = stringify_trace_options_response(s.trace_options.response)
        return self.set_response_headers(headers, parent_context, trace_id, name, kind, attributes, links, trace_state)

    @abstractmethod
    def set_response_headers(self,
                             headers: ResponseHeaders,
                             parent_context: Optional["Context"],
                             trace_id: int,
                             name: str,
                             kind: Optional[SpanKind] = None,
                             attributes: Attributes = None,
                             links: Optional[Sequence["Link"]] = None,
                             trace_state: Optional["TraceState"] = None) -> Optional["TraceState"]:
        pass

    def get_description(self) -> str:
        return f"OboeSampler{{{self._settings}}}"
