# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
from __future__ import annotations

import logging
import re
import time
from abc import ABC, abstractmethod
from collections.abc import Sequence

from opentelemetry.context import Context
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.sampling import (
    Attributes,
    Decision,
    Sampler,
    SamplingResult,
)
from opentelemetry.trace import Link, SpanKind, TraceFlags, get_current_span
from opentelemetry.trace.span import Span, TraceState
from typing_extensions import override

from solarwinds_apm.oboe.dice import _Dice
from solarwinds_apm.oboe.metrics import Counters
from solarwinds_apm.oboe.settings import (
    BucketType,
    Flags,
    LocalSettings,
    Settings,
    merge,
)
from solarwinds_apm.oboe.token_bucket import _TokenBucket
from solarwinds_apm.oboe.trace_options import (
    Auth,
    RequestHeaders,
    ResponseHeaders,
    TraceOptionsResponse,
    TraceOptionsWithResponse,
    TriggerTrace,
    parse_trace_options,
    stringify_trace_options_response,
    validate_signature,
)
from solarwinds_apm.w3c_transformer import W3CTransformer

logger = logging.getLogger(__name__)

TRACESTATE_REGEXP = r"^[0-9a-f]{16}-[0-9a-f]{2}$"
DICE_SCALE = 1_000_000

SW_KEYS_ATTRIBUTE = "SWKeys"
PARENT_ID_ATTRIBUTE = "sw.tracestate_parent_id"
TRACESTATE_CAPTURE_ATTRIBUTE = "sw.w3c.tracestate"
SAMPLE_RATE_ATTRIBUTE = "SampleRate"
SAMPLE_SOURCE_ATTRIBUTE = "SampleSource"
BUCKET_CAPACITY_ATTRIBUTE = "BucketCapacity"
BUCKET_RATE_ATTRIBUTE = "BucketRate"
TRIGGERED_TRACE_ATTRIBUTE = "TriggeredTrace"


class SampleState:
    def __init__(
        self,
        decision: Decision,
        attributes: Attributes,
        settings: Settings | None,
        trace_state: str | None,
        headers: RequestHeaders,
        trace_options: TraceOptionsWithResponse | None,
    ):
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
    def settings(self) -> Settings | None:
        return self._settings

    @settings.setter
    def settings(self, value: Settings | None):
        self._settings = value

    @property
    def trace_state(self) -> str | None:
        return self._trace_state

    @trace_state.setter
    def trace_state(self, value: str | None):
        self._trace_state = value

    @property
    def headers(self) -> RequestHeaders:
        return self._headers

    @headers.setter
    def headers(self, value: RequestHeaders):
        self._headers = value

    @property
    def trace_options(self) -> TraceOptionsWithResponse | None:
        return self._trace_options

    @trace_options.setter
    def trace_options(self, value: TraceOptionsWithResponse | None):
        self._trace_options = value

    def __str__(self):
        return (
            f"SampleState{{decision={self.decision}, "
            f"attributes={self.attributes}, "
            f"settings={self.settings}, "
            f"trace_state={self.trace_state}, "
            f"headers={self.headers}, "
            f"trace_options={self.trace_options}}}"
        )


class OboeSampler(Sampler, ABC):
    def __init__(self, meter_provider: MeterProvider):
        self._counters = Counters(meter_provider=meter_provider)
        self._buckets = {
            BucketType.DEFAULT: _TokenBucket(),
            BucketType.TRIGGER_RELAXED: _TokenBucket(),
            BucketType.TRIGGER_STRICT: _TokenBucket(),
        }
        self._settings: Settings | None = None

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
        parent_context: "Context" | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes = None,
        links: Sequence["Link"] | None = None,
        trace_state: "TraceState" | None = None,
    ) -> "SamplingResult":
        parent_span = get_current_span(parent_context)

        sample_state = self._initialize_sample_state(
            parent_context,
            trace_id,
            name,
            kind,
            attributes,
            links,
            trace_state,
            parent_span,
        )

        # Capture the tracestate from the parent span and store it in the sample state
        if (
            parent_span.get_span_context().is_valid
            and parent_span.get_span_context().trace_state is not None
        ):
            sample_state.attributes[TRACESTATE_CAPTURE_ATTRIBUTE] = (
                W3CTransformer.remove_response_from_sw(
                    parent_span.get_span_context().trace_state
                ).to_header()
            )

        self.counters.request_count.add(1, {}, parent_context)

        if sample_state.headers.x_trace_options:
            result = self._process_trace_options(
                sample_state,
                parent_context,
                trace_id,
                name,
                kind,
                attributes,
                links,
                trace_state,
            )
            if result:
                return result

        if not sample_state.settings:
            return self._handle_no_settings(
                sample_state,
                parent_context,
                trace_id,
                name,
                kind,
                attributes,
                links,
                trace_state,
            )

        if sample_state.trace_state and re.match(
            TRACESTATE_REGEXP, sample_state.trace_state
        ):
            sample_state.decision = self.parent_based_algo(
                sample_state, parent_context
            )
        elif sample_state.settings.flags & Flags.SAMPLE_START:
            self._handle_sample_start(sample_state, parent_context)
        else:
            self.disabled_algo(sample_state)

        logger.debug("final sampling state %s", sample_state)
        new_trace_state = self.set_response_headers_from_sample_state(
            sample_state,
            parent_context,
            trace_id,
            name,
            kind,
            attributes,
            links,
            trace_state,
        )
        return SamplingResult(
            decision=sample_state.decision,
            attributes=sample_state.attributes,
            trace_state=new_trace_state,
        )

    def _initialize_sample_state(
        self,
        parent_context: "Context" | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None,
        attributes: Attributes,
        links: Sequence["Link"] | None,
        trace_state: "TraceState" | None,
        parent_span: Span | None,
    ) -> SampleState:
        """
        Initialize a SampleState object with the given parameters.
        """
        return SampleState(
            decision=Decision.DROP,
            attributes=attributes if attributes else {},
            settings=self.get_settings(
                parent_context,
                trace_id,
                name,
                kind,
                attributes,
                links,
                trace_state,
            ),
            trace_state=(
                parent_span.get_span_context().trace_state.get("sw")
                if parent_span
                else None
            ),
            headers=self.request_headers(
                parent_context,
                trace_id,
                name,
                kind,
                attributes,
                links,
                trace_state,
            ),
            trace_options=None,
        )

    def _process_trace_options(
        self,
        sample_state: SampleState,
        parent_context: "Context" | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes = None,
        links: Sequence["Link"] | None = None,
        trace_state: "TraceState" | None = None,
    ):
        """
        Process the X-Trace-Options header and set the appropriate response
        """
        parsed = parse_trace_options(sample_state.headers.x_trace_options)
        sample_state.trace_options = TraceOptionsWithResponse(
            trigger_trace=parsed.trigger_trace,
            timestamp=parsed.timestamp,
            sw_keys=parsed.sw_keys,
            custom=parsed.custom,
            ignored=parsed.ignored,
            response=TraceOptionsResponse(
                auth=None, trigger_trace=None, ignored=None
            ),
        )
        logger.debug("X-Trace-Options present %s", sample_state.trace_options)
        if sample_state.headers.x_trace_options_signature:
            sample_state.trace_options.response.auth = validate_signature(
                sample_state.headers.x_trace_options,
                sample_state.headers.x_trace_options_signature,
                (
                    sample_state.settings.signature_key
                    if sample_state.settings
                    and sample_state.settings.signature_key
                    else None
                ),
                sample_state.trace_options.timestamp,
            )
            if sample_state.trace_options.response.auth != Auth.OK:
                logger.debug(
                    "X-Trace-Options-Signature invalid; tracing disabled"
                )
                new_trace_state = self.set_response_headers_from_sample_state(
                    sample_state,
                    parent_context,
                    trace_id,
                    name,
                    kind,
                    attributes,
                    links,
                    trace_state,
                )
                return SamplingResult(
                    decision=Decision.DROP, trace_state=new_trace_state
                )
        if not sample_state.trace_options.trigger_trace:
            sample_state.trace_options.response.trigger_trace = (
                TriggerTrace.NOT_REQUESTED
            )
        if sample_state.trace_options.sw_keys:
            sample_state.attributes[SW_KEYS_ATTRIBUTE] = (
                sample_state.trace_options.sw_keys
            )
        for key, value in sample_state.trace_options.custom.items():
            sample_state.attributes[key] = value
        if len(sample_state.trace_options.ignored) > 0:
            sample_state.trace_options.response.ignored = [
                key for key, _ in sample_state.trace_options.ignored
            ]
        return None

    def _handle_no_settings(
        self,
        sample_state: SampleState,
        parent_context: "Context" | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None,
        attributes: Attributes,
        links: Sequence["Link"] | None,
        trace_state: "TraceState" | None,
    ) -> "SamplingResult":
        """
        Handle the case where settings are unavailable.
        """
        logger.warning("settings unavailable; sampling disabled")
        if (
            sample_state.trace_options
            and sample_state.trace_options.trigger_trace
        ):
            logger.debug("trigger trace requested but settings unavailable")
            sample_state.trace_options.response.trigger_trace = (
                TriggerTrace.SETTINGS_NOT_AVAILABLE
            )
        new_trace_state = self.set_response_headers_from_sample_state(
            sample_state,
            parent_context,
            trace_id,
            name,
            kind,
            attributes,
            links,
            trace_state,
        )
        return SamplingResult(
            decision=Decision.DROP,
            attributes=sample_state.attributes,
            trace_state=new_trace_state,
        )

    def _handle_sample_start(
        self, sample_state: SampleState, parent_context: "Context" | None
    ):
        """
        Handle the case where the SAMPLE_START flag is set.
        """
        if (
            sample_state.trace_options
            and sample_state.trace_options.trigger_trace
        ):
            (
                sample_state.trace_options.response.trigger_trace,
                sample_state.decision,
            ) = self.trigger_trace_algo(sample_state, parent_context)
        else:
            sample_state.decision = self.dice_roll_algo(
                sample_state, parent_context
            )

    def parent_based_algo(
        self, s: SampleState, parent_context: "Context" | None
    ):
        """
        Determine the sampling decision based on the parent span.
        """
        s.attributes[PARENT_ID_ATTRIBUTE] = (
            s.trace_state[:16] if s.trace_state else None
        )
        if s.trace_options and s.trace_options.trigger_trace:
            logger.debug("trigger trace requested but ignored")
            s.trace_options.response.trigger_trace = TriggerTrace.IGNORED

        if s.settings and s.settings.flags & Flags.SAMPLE_THROUGH_ALWAYS:
            logger.debug("SAMPLE_THROUGH_ALWAYS is set; parent-based sampling")
            flags = int(s.trace_state[-2:], 16)
            if flags & TraceFlags.SAMPLED:
                logger.debug("parent is sampled; record and sample")
                self.counters.trace_count.add(1, {}, parent_context)
                self.counters.through_trace_count.add(1, {}, parent_context)
                return Decision.RECORD_AND_SAMPLE
            logger.debug("parent is not sampled; record only")
            return Decision.RECORD_ONLY
        logger.debug("SAMPLE_THROUGH_ALWAYS is unset; sampling disabled")
        if s.settings and s.settings.flags & Flags.SAMPLE_START:
            logger.debug("SAMPLE_START is set; record")
            return Decision.RECORD_ONLY
        logger.debug("SAMPLE_START is unset; don't record")
        return Decision.DROP

    def trigger_trace_algo(
        self, s: SampleState, parent_context: "Context" | None
    ):
        """
        Determine the sampling decision based on the TRIGGER_TRACE flag.
        """
        if s.settings and s.settings.flags & Flags.TRIGGERED_TRACE:
            logger.debug("TRIGGERED_TRACE set; trigger tracing")
            bucket: _TokenBucket
            if s.trace_options and s.trace_options.response.auth:
                logger.debug("signed request; using relaxed rate")
                bucket = self.buckets[BucketType.TRIGGER_RELAXED]
            else:
                logger.debug("unsigned request; using strict rate")
                bucket = self.buckets[BucketType.TRIGGER_STRICT]
            s.attributes[TRIGGERED_TRACE_ATTRIBUTE] = True
            s.attributes[BUCKET_CAPACITY_ATTRIBUTE] = bucket.capacity
            s.attributes[BUCKET_RATE_ATTRIBUTE] = bucket.rate
            if bucket.consume():
                logger.debug("sufficient capacity; record and sample")
                self.counters.triggered_trace_count.add(1, {}, parent_context)
                self.counters.trace_count.add(1, {}, parent_context)
                return TriggerTrace.OK, Decision.RECORD_AND_SAMPLE
            logger.debug("insufficient capacity; record only")
            return TriggerTrace.RATE_EXCEEDED, Decision.RECORD_ONLY
        logger.debug("TRIGGERED_TRACE unset; record only")
        return TriggerTrace.TRIGGER_TRACING_DISABLED, Decision.RECORD_ONLY

    def dice_roll_algo(self, s: SampleState, parent_context: "Context" | None):
        """
        Determine the sampling decision based on a dice roll.
        """
        dice = _Dice(
            rate=s.settings.sample_rate if s.settings else 0, scale=DICE_SCALE
        )
        s.attributes[SAMPLE_RATE_ATTRIBUTE] = dice.rate
        s.attributes[SAMPLE_SOURCE_ATTRIBUTE] = s.settings.sample_source
        self.counters.sample_count.add(1, {}, parent_context)
        if dice.roll():
            logger.debug("dice roll success; checking capacity")
            bucket = self.buckets[BucketType.DEFAULT]
            s.attributes[BUCKET_CAPACITY_ATTRIBUTE] = bucket.capacity
            s.attributes[BUCKET_RATE_ATTRIBUTE] = bucket.rate
            if bucket.consume():
                logger.debug("sufficient capacity; record and sample")
                self.counters.trace_count.add(1, {}, parent_context)
                return Decision.RECORD_AND_SAMPLE
            logger.debug("insufficient capacity; record only")
            self.counters.token_bucket_exhaustion_count.add(
                1, {}, parent_context
            )
            return Decision.RECORD_ONLY
        logger.debug("dice roll failure; record only")
        return Decision.RECORD_ONLY

    def disabled_algo(self, s: SampleState):
        """
        Determine the sampling decision when sampling is disabled
        """
        if s.trace_options and s.trace_options.trigger_trace:
            logger.debug("trigger trace requested but tracing disabled")
            s.trace_options.response.trigger_trace = (
                TriggerTrace.TRACING_DISABLED
            )

        if s.settings and s.settings.flags & Flags.SAMPLE_THROUGH_ALWAYS:
            logger.debug("SAMPLE_THROUGH_ALWAYS is set; record")
            s.decision = Decision.RECORD_ONLY
        else:
            logger.debug("SAMPLE_THROUGH_ALWAYS is unset; don't record")
            s.decision = Decision.DROP

    def update_settings(self, settings: Settings):
        """
        Update the sampler settings if the new settings are more recent.
        """
        if settings.timestamp > (
            self.settings.timestamp if self.settings else 0
        ):
            self.settings = settings
            for bucket_type, bucket in self.buckets.items():
                if bucket_type in self.settings.buckets:
                    bucket.update(
                        new_capacity=self.settings.buckets[
                            bucket_type
                        ].capacity,
                        new_rate=self.settings.buckets[bucket_type].rate,
                    )

    def get_settings(
        self,
        parent_context: "Context" | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes = None,
        links: Sequence["Link"] | None = None,
        trace_state: "TraceState" | None = None,
    ) -> Settings | None:
        """
        Get the settings within the ttl if available.
        """
        if self.settings is None:
            return None
        if time.time() > self.settings.timestamp + self.settings.ttl:
            logger.debug("settings expired; removing")
            self.settings = None
            return None
        return merge(
            self.settings,
            self.local_settings(
                parent_context,
                trace_id,
                name,
                kind,
                attributes,
                links,
                trace_state,
            ),
        )

    @abstractmethod
    def local_settings(
        self,
        parent_context: "Context" | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes = None,
        links: Sequence["Link"] | None = None,
        trace_state: "TraceState" | None = None,
    ) -> LocalSettings:
        """
        Interface for inherited class to override
        """

    @abstractmethod
    def request_headers(
        self,
        parent_context: "Context" | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes = None,
        links: Sequence["Link"] | None = None,
        trace_state: "TraceState" | None = None,
    ) -> RequestHeaders:
        """
        Interface for inherited class to override
        """

    def set_response_headers_from_sample_state(
        self,
        s: SampleState,
        parent_context: "Context" | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes = None,
        links: Sequence["Link"] | None = None,
        trace_state: "TraceState" | None = None,
    ) -> "TraceState" | None:
        """
        Set the response headers based on the sample state
        """
        headers = ResponseHeaders(x_trace_options_response=None)
        if s.trace_options:
            headers.x_trace_options_response = (
                stringify_trace_options_response(s.trace_options.response)
            )
        return self.set_response_headers(
            headers,
            parent_context,
            trace_id,
            name,
            kind,
            attributes,
            links,
            trace_state,
        )

    @abstractmethod
    def set_response_headers(
        self,
        headers: ResponseHeaders,
        parent_context: "Context" | None,
        trace_id: int,
        name: str,
        kind: SpanKind | None = None,
        attributes: Attributes = None,
        links: Sequence["Link"] | None = None,
        trace_state: "TraceState" | None = None,
    ) -> "TraceState" | None:
        """
        Interface for inherited class to override
        """

    def get_description(self) -> str:
        return f"OboeSampler{{{self._settings}}}"
