""" This module provides a SolarWinds-specific sampler.

The custom sampler will fetch sampling configurations for the SolarWinds backend.
"""

import logging
from types import MappingProxyType
from typing import Optional, Sequence

from opentelemetry.context.context import Context as OtelContext
from opentelemetry.sdk.trace.sampling import (Decision, ParentBased, Sampler,
                                              SamplingResult)
from opentelemetry.trace import Link, SpanKind, get_current_span
from opentelemetry.trace.span import SpanContext, TraceState
from opentelemetry.util.types import Attributes

from opentelemetry_distro_solarwinds import (
    COMMA_W3C_SANITIZED,
    EQUALS_W3C_SANITIZED,
    SW_TRACESTATE_KEY
)
from opentelemetry_distro_solarwinds.extension.oboe import Context
from opentelemetry_distro_solarwinds.traceoptions import XTraceOptions
from opentelemetry_distro_solarwinds.w3c_transformer import W3CTransformer

logger = logging.getLogger(__name__)


class _LiboboeDecision():
    """Convenience representation of a liboboe decision"""
    def __init__(
        self,
        do_metrics: int,
        do_sample: int,
        sample_rate: int,
        sample_source: int,
        bucket_rate: float,
        bucket_cap: float,
        decision_type: int,
        auth: int,
        status_msg: str,
        auth_msg: str,
        status: int,
    ):
        self.do_metrics = do_metrics
        self.do_sample = do_sample
        self.sample_rate = sample_rate
        self.sample_source = sample_source
        self.bucket_rate = bucket_rate
        self.bucket_cap = bucket_cap
        self.decision_type = decision_type
        self.auth = auth
        self.status_msg = status_msg
        self.auth_msg = auth_msg
        self.status = status


class _SwSampler(Sampler):
    """SolarWinds custom opentelemetry sampler which obeys configuration options provided by the NH/AO Backend."""

    _SW_TRACESTATE_CAPTURE_KEY = "sw.w3c.tracestate"
    _SW_TRACESTATE_ROOT_KEY = "sw.tracestate_parent_id"
    _XTRACEOPTIONS_RESP_AUTH = "auth"
    _XTRACEOPTIONS_RESP_IGNORED = "ignored"
    _XTRACEOPTIONS_RESP_TRIGGER_IGNORED = "ignored"
    _XTRACEOPTIONS_RESP_TRIGGER_NOT_REQUESTED = "not-requested"
    _XTRACEOPTIONS_RESP_TRIGGER_TRACE = "trigger-trace"

    def get_description(self) -> str:
        return "SolarWinds custom opentelemetry sampler"

    def calculate_liboboe_decision(
        self,
        parent_span_context: SpanContext,
        parent_context: Optional[OtelContext] = None,
        xtraceoptions: Optional[XTraceOptions] = None,
    ) -> _LiboboeDecision:
        """Calculates oboe trace decision based on parent span context."""
        tracestring = None
        if parent_span_context.is_valid and parent_span_context.is_remote:
            tracestring = W3CTransformer.traceparent_from_context(
                parent_span_context
            )
        sw_member_value = parent_span_context.trace_state.get(SW_TRACESTATE_KEY)

        # TODO: local config --> enable/disable tracing, sample_rate, tt mode
        tracing_mode = -1
        sample_rate = -1
        trigger_tracing_mode_disabled = -1

        logger.debug("parent_context is {}".format(parent_context))
        logger.debug("xtraceoptions is {}".format(dict(xtraceoptions)))

        options = None
        trigger_trace = 0
        signature = None
        timestamp = None
        if xtraceoptions:
            options = xtraceoptions.to_options_header()
            trigger_trace = xtraceoptions.trigger_trace
            signature = xtraceoptions.signature
            timestamp = xtraceoptions.ts

        logger.debug(
            "Creating new oboe decision with "
            "tracestring: {}, "
            "sw_member_value: {}, "
            "tracing_mode: {}, "
            "sample_rate: {}, "
            "trigger_trace: {}, "
            "trigger_tracing_mode_disabled: {}, "
            "options: {}, "
            "signature: {}, "
            "timestamp: {}".format(
            tracestring,
            sw_member_value,
            tracing_mode,
            sample_rate,
            trigger_trace,
            trigger_tracing_mode_disabled,
            options,
            signature,
            timestamp
        ))
        do_metrics, do_sample, \
            rate, source, bucket_rate, bucket_cap, decision_type, \
            auth, status_msg, auth_msg, status = Context.getDecisions(
                tracestring,
                sw_member_value,
                tracing_mode,
                sample_rate,
                trigger_trace,
                trigger_tracing_mode_disabled,
                options,
                signature,
                timestamp
            )
        logger.debug(
            "Got liboboe decision outputs "
            "do_metrics: {}, "
            "do_sample: {}, "
            "rate: {}, "
            "source: {}, "
            "bucket_rate: {}, "
            "bucket_cap: {}, "
            "type: {}, "
            "auth: {}, "
            "status_msg: {}, "
            "auth_msg: {}, "
            "status: {}".format(
                do_metrics,
                do_sample,
                rate,
                source,
                bucket_rate,
                bucket_cap,
                decision_type,
                auth,
                status_msg,
                auth_msg,
                status
            )
        )
        return _LiboboeDecision(
            do_metrics,
            do_sample,
            rate,
            source,
            bucket_rate,
            bucket_cap,
            decision_type,
            auth,
            status_msg,
            auth_msg,
            status
        )

    def otel_decision_from_liboboe(
        self,
        liboboe_decision: _LiboboeDecision
    ) -> Decision:
        """Formats OTel decision from liboboe decision"""
        decision = Decision.DROP
        if liboboe_decision.do_metrics:
            # TODO: need to eck what record only actually means and how metrics work in OTel
            decision = Decision.RECORD_ONLY
        if liboboe_decision.do_sample:
            decision = Decision.RECORD_AND_SAMPLE
        logger.debug("OTel decision created: {}".format(decision))
        return decision

    def create_xtraceoptions_response_value(
        self,
        decision: _LiboboeDecision,
        parent_span_context: SpanContext,
        xtraceoptions: XTraceOptions
    ) -> str:
        """Use decision and xtraceoptions to create sanitized xtraceoptions
        response kv with W3C tracestate-allowed delimiters:
        EQUALS_W3C_SANITIZED instead of EQUALS
        COMMA_W3C_SANITIZED instead of COMMA
        """
        response = []

        if xtraceoptions.signature:
            response.append(EQUALS_W3C_SANITIZED.join([
                self._XTRACEOPTIONS_RESP_AUTH,
                decision.auth_msg
            ]))

        if not decision.auth or decision.auth < 1:
            trigger_msg = ""
            if xtraceoptions.trigger_trace:
                # If a traceparent header was provided then oboe does not generate the message
                tracestring = None
                if parent_span_context.is_valid and parent_span_context.is_remote:
                    tracestring = W3CTransformer.traceparent_from_context(
                        parent_span_context
                    )

                if tracestring and decision.decision_type == 0:
                    trigger_msg = self._XTRACEOPTIONS_RESP_TRIGGER_IGNORED
                else:
                    trigger_msg = decision.status_msg
            else:
                trigger_msg = self.XTRACEOPTIONS_TRIGGER_NOT_REQUESTED
            response.append(EQUALS_W3C_SANITIZED.join([
                self._XTRACEOPTIONS_RESP_TRIGGER_TRACE,
                trigger_msg
            ]))

        if xtraceoptions.ignored:
            response.append(
                EQUALS_W3C_SANITIZED.join([
                    self._XTRACEOPTIONS_RESP_IGNORED,
                    (COMMA_W3C_SANITIZED.join(decision.ignored))
                ])
            )

        return ";".join(response)

    def create_new_trace_state(
        self,
        decision: _LiboboeDecision,
        parent_span_context: SpanContext,
        xtraceoptions: Optional[XTraceOptions] = None,
    ) -> TraceState:
        """Creates new TraceState based on trace decision, parent span id,
        and x-trace-options if provided"""
        trace_state = TraceState([(
            SW_TRACESTATE_KEY,
            W3CTransformer.sw_from_span_and_decision(
                parent_span_context.span_id,
                W3CTransformer.trace_flags_from_int(decision.do_sample)
            )
        )])
        if xtraceoptions and xtraceoptions.trigger_trace:
            trace_state = trace_state.add(
                XTraceOptions.get_sw_xtraceoptions_response_key(),
                self.create_xtraceoptions_response_value(
                    decision,
                    parent_span_context,
                    xtraceoptions
                )
            )
        logger.debug("Created new trace_state: {}".format(trace_state))
        return trace_state

    def calculate_trace_state(
        self,
        decision: _LiboboeDecision,
        parent_span_context: SpanContext,
        xtraceoptions: Optional[XTraceOptions] = None,
    ) -> TraceState:
        """Calculates trace_state based on parent span context, trace decision,
        and x-trace-options if provided -- for non-existent or remote parent
        spans only."""
        # No valid parent i.e. root span, or parent is remote
        if not parent_span_context.is_valid:
            trace_state = self.create_new_trace_state(
                decision,
                parent_span_context,
                xtraceoptions
            )
        else:
            trace_state = parent_span_context.trace_state
            if not trace_state:
                # tracestate nonexistent/non-parsable
                trace_state = self.create_new_trace_state(
                    decision,
                    parent_span_context,
                    xtraceoptions
                )
            else:
                # Update trace_state with span_id and sw trace_flags
                trace_state = trace_state.update(
                    SW_TRACESTATE_KEY,
                    W3CTransformer.sw_from_span_and_decision(
                        parent_span_context.span_id,
                        W3CTransformer.trace_flags_from_int(decision.do_sample)
                    )
                )
                # Update trace_state with x-trace-options-response
                # Not a propagated header, so always an add
                if xtraceoptions and xtraceoptions.trigger_trace:
                    trace_state = trace_state.add(
                        XTraceOptions.get_sw_xtraceoptions_response_key(),
                        self.create_xtraceoptions_response_value(
                            decision,
                            parent_span_context,
                            xtraceoptions
                        )
                    )
                logger.debug("Updated trace_state: {}".format(trace_state))
        return trace_state

    def calculate_attributes(
        self,
        attributes: Attributes,
        decision: _LiboboeDecision,
        trace_state: TraceState,
        parent_span_context: SpanContext
    ) -> Attributes or None:
        """Calculates Attributes or None based on trace decision, trace state,
        parent span context, and existing attributes.

        For non-existent or remote parent spans only."""
        logger.debug("Received attributes: {}".format(attributes))

        # Don't set attributes if not tracing
        if self.otel_decision_from_liboboe(decision) == Decision.DROP:
            logger.debug("Trace decision is to drop - not setting attributes")
            return None
        # Trace's root span has no valid traceparent nor tracestate
        # so we don't set additional attributes
        if not parent_span_context.is_valid or not trace_state:
            logger.debug("No valid traceparent or no tracestate - not setting attributes")
            return None

        # Set attributes with self._SW_TRACESTATE_ROOT_KEY and self._SW_TRACESTATE_CAPTURE_KEY
        if not attributes:
            attributes = {
                self._SW_TRACESTATE_CAPTURE_KEY: trace_state.to_header()
            }
            # Only set self._SW_TRACESTATE_ROOT_KEY on the entry (root) span for this service
            sw_value = parent_span_context.trace_state.get(SW_TRACESTATE_KEY, None)
            if sw_value:
                attributes[self._SW_TRACESTATE_ROOT_KEY] = sw_value

            logger.debug("Created new attributes: {}".format(attributes))
        else:
            # Copy existing MappingProxyType KV into new_attributes for modification
            # attributes may have other vendor info etc
            new_attributes = {}
            for k,v in attributes.items():
                new_attributes[k] = v

            if not new_attributes.get(self._SW_TRACESTATE_CAPTURE_KEY, None):
                # Add new self._SW_TRACESTATE_CAPTURE_KEY KV
                new_attributes[self._SW_TRACESTATE_CAPTURE_KEY] = trace_state.to_header()
            else:
                # Update existing self._SW_TRACESTATE_CAPTURE_KEY KV
                attr_trace_state = TraceState.from_header(
                    new_attributes[self._SW_TRACESTATE_CAPTURE_KEY]
                )
                attr_trace_state.update(
                    SW_TRACESTATE_KEY,
                    W3CTransformer.sw_from_span_and_decision(
                        parent_span_context.span_id,
                        W3CTransformer.trace_flags_from_int(decision.do_sample)
                    )
                )
                new_attributes[self._SW_TRACESTATE_CAPTURE_KEY] = attr_trace_state.to_header()

            attributes = new_attributes
            logger.debug("Set updated attributes: {}".format(attributes))
        
        # attributes must be immutable for SamplingResult
        return MappingProxyType(attributes)

    def should_sample(
        self,
        parent_context: Optional[OtelContext],
        trace_id: int,
        name: str,
        kind: SpanKind = None,
        attributes: Attributes = None,
        links: Sequence["Link"] = None,
        trace_state: "TraceState" = None,
    ) -> "SamplingResult":
        """
        Calculates SamplingResult based on calculation of new/continued trace
        decision, new/updated trace state, and new/updated attributes.
        """
        parent_span_context = get_current_span(
            parent_context
        ).get_span_context()
        xtraceoptions = XTraceOptions(parent_context)

        decision = self.calculate_liboboe_decision(
            parent_span_context,
            parent_context,
            xtraceoptions
        )

        # Always calculate trace_state for propagation
        trace_state = self.calculate_trace_state(
            decision,
            parent_span_context,
            xtraceoptions
        )
        attributes = self.calculate_attributes(
            attributes,
            decision,
            trace_state,
            parent_span_context
        )
        decision = self.otel_decision_from_liboboe(decision)

        return SamplingResult(
            decision,
            attributes if decision != Decision.DROP else None,
            trace_state,
        )


class ParentBasedSwSampler(ParentBased):
    """
    Sampler that respects its parent span's sampling decision, but otherwise
    samples according to the configurations from the NH/AO backend.
    """
    def __init__(self):
        """
        Uses _SwSampler/liboboe if no parent span.
        Uses _SwSampler/liboboe if parent span is_remote.
        Uses OTEL defaults if parent span is_local.
        """
        super().__init__(
            root=_SwSampler(),
            remote_parent_sampled=_SwSampler(),
            remote_parent_not_sampled=_SwSampler()
        )

    def should_sample(
        self,
        parent_context: Optional["Context"],
        trace_id: int,
        name: str,
        kind: SpanKind = None,
        attributes: Attributes = None,
        links: Sequence["Link"] = None,
        trace_state: "TraceState" = None
    ) -> "SamplingResult":

        return super().should_sample(
            parent_context,
            trace_id,
            name,
            kind,
            attributes,
            links,
            trace_state
        )
