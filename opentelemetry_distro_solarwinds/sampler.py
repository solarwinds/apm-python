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

from opentelemetry_distro_solarwinds.extension.oboe import Context
from opentelemetry_distro_solarwinds.traceoptions import XTraceOptions
from opentelemetry_distro_solarwinds.w3c_transformer import (
    trace_flags_from_int,
    traceparent_from_context,
    sw_from_span_and_decision
)

logger = logging.getLogger(__name__)


class _LiboboeDecision():
    """Convenience representation of a liboboe decision"""
    def __init__(
        self,
        do_metrics: str,
        do_sample: str
    ):
        # TODO all liboboe outputs
        self.do_metrics = do_metrics
        self.do_sample = do_sample


class _SwSampler(Sampler):
    """SolarWinds custom opentelemetry sampler which obeys configuration options provided by the NH/AO Backend."""

    def get_description(self) -> str:
        return "SolarWinds custom opentelemetry sampler"

    def calculate_liboboe_decision(
        self,
        parent_span_context: SpanContext,
        parent_context: Optional[OtelContext] = None,
    ) -> _LiboboeDecision:
        """Calculates oboe trace decision based on parent span context, for
        non-existent or remote parent spans only."""
        tracestring = traceparent_from_context(parent_span_context)
        sw_member_value = parent_span_context.trace_state.get("sw")

        # TODO: config --> enable/disable tracing, sample_rate, tt mode
        tracing_mode = 1
        sample_rate = 1000000
        trigger_tracing_mode_disabled = 0

        xtraceoptions = XTraceOptions("", parent_context)
        logger.debug("parent_context is {0}".format(parent_context))
        logger.debug("xtraceoptions is {0}".format(xtraceoptions))

        if xtraceoptions.trigger_trace:
            trigger_trace = 1
        else:
            trigger_trace = 0
        timestamp = xtraceoptions.ts
        signature = None
        options = str(xtraceoptions)

        logger.debug(
            "Creating new oboe decision with "
            "tracestring: {0}, "
            "sw_member_value: {1}, "
            "tracing_mode: {2}, "
            "sample_rate: {3}, "
            "trigger_trace: {4}, "
            "trigger_tracing_mode_disabled: {5}, "
            "options: {6}, "
            "signature: {7}, "
            "timestamp: {8}".format(
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
            rate, source, bucket_rate, bucket_cap, \
            type, auth, status_msg, auth_msg, status = Context.getDecisions(
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
            "do_metrics: {0}, "
            "do_sample: {1}, "
            "rate: {2}, "
            "source: {3}, "
            "bucket_rate: {4}, "
            "bucket_cap: {5}, "
            "type: {6}, "
            "auth: {7}, "
            "status_msg: {8}, "
            "auth_msg: {9}, "
            "status: {10}".format(
                do_metrics,
                do_sample,
                rate,
                source,
                bucket_rate,
                bucket_cap,
                type,
                auth,
                status_msg,
                auth_msg,
                status
            )
        )
        return _LiboboeDecision(do_metrics, do_sample)

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
        logger.debug("OTel decision created: {0}".format(decision))
        return decision

    def create_new_trace_state(
        self,
        decision: _LiboboeDecision,
        parent_span_context: SpanContext
    ) -> TraceState:
        """Creates new TraceState based on trace decision and parent span id."""
        trace_state = TraceState([(
            "sw",
            sw_from_span_and_decision(
                parent_span_context.span_id,
                trace_flags_from_int(decision.do_sample)
            )
        )])
        logger.debug("Created new trace_state: {0}".format(trace_state))
        return trace_state

    def calculate_trace_state(
        self,
        decision: _LiboboeDecision,
        parent_span_context: SpanContext
    ) -> TraceState:
        """Calculates trace_state based on parent span context and trace decision,
        for non-existent or remote parent spans only."""
        # No valid parent i.e. root span, or parent is remote
        if not parent_span_context.is_valid:
            trace_state = self.create_new_trace_state(decision, parent_span_context)
        else:
            trace_state = parent_span_context.trace_state
            if not trace_state:
                # tracestate nonexistent/non-parsable
                trace_state = self.create_new_trace_state(decision, parent_span_context)
            else:
                # Update trace_state with span_id and sw trace_flags
                trace_state = trace_state.update(
                    "sw",
                    sw_from_span_and_decision(
                        parent_span_context.span_id,
                        trace_flags_from_int(decision.do_sample)
                    )
                )
                logger.debug("Updated trace_state: {0}".format(trace_state))
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
        logger.debug("Received attributes: {0}".format(attributes))

        # Don't set attributes if not tracing
        if self.otel_decision_from_liboboe(decision) == Decision.DROP:
            logger.debug("Trace decision is to drop - not setting attributes")
            return None
        # Trace's root span has no valid traceparent nor tracestate
        # so we don't set additional attributes
        if not parent_span_context.is_valid or not trace_state:
            logger.debug("No valid traceparent or no tracestate - not setting attributes")
            return None

        # Set attributes with sw.tracestate_parent_id and sw.w3c.tracestate
        if not attributes:
            attributes = {
                "sw.w3c.tracestate": trace_state.to_header()
            }
            # Only set sw.tracestate_parent_id on the entry (root) span for this service
            sw_value = parent_span_context.trace_state.get("sw", None)
            if sw_value:
                attributes["sw.tracestate_parent_id"] = sw_value

            logger.debug("Created new attributes: {0}".format(attributes))
        else:
            # Copy existing MappingProxyType KV into new_attributes for modification
            # attributes may have other vendor info etc
            new_attributes = {}
            for k,v in attributes.items():
                new_attributes[k] = v

            if not new_attributes.get("sw.w3c.tracestate", None):
                # Add new sw.w3c.tracestate KV
                new_attributes["sw.w3c.tracestate"] = trace_state.to_header()
            else:
                # Update existing sw.w3c.tracestate KV
                attr_trace_state = TraceState.from_header(
                    new_attributes["sw.w3c.tracestate"]
                )
                attr_trace_state.update(
                    "sw",
                    sw_from_span_and_decision(
                        parent_span_context.span_id,
                        trace_flags_from_int(decision.do_sample)
                    )
                )
                new_attributes["sw.w3c.tracestate"] = attr_trace_state.to_header()

            attributes = new_attributes
            logger.debug("Set updated attributes: {0}".format(attributes))
        
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

        decision = self.calculate_liboboe_decision(
            parent_span_context,
            parent_context
        )

        # Always calculate trace_state for propagation
        trace_state = self.calculate_trace_state(
            decision,
            parent_span_context
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
