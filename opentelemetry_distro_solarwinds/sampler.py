""" This module provides a SolarWinds-specific sampler.

The custom sampler will fetch sampling configurations for the SolarWinds backend.
"""

import logging
import re
from types import MappingProxyType
from typing import Optional, Sequence

from opentelemetry.sdk.trace.sampling import (Decision, ParentBased, Sampler,
                                              SamplingResult)
from opentelemetry.trace import Link, SpanKind, get_current_span
from opentelemetry.trace.span import SpanContext, TraceState
from opentelemetry.util.types import Attributes

from opentelemetry_distro_solarwinds.extension.oboe import Context
from opentelemetry_distro_solarwinds.w3c_transformer import (
    span_id_from_int,
    trace_flags_from_int,
    traceparent_from_context,
    sw_from_context,
    sw_from_span_and_decision
)

SW_FORMAT = "^\w{16}-0[0|1]$"
logger = logging.getLogger(__name__)


class _LiboboeDecision():
    """Represents a liboboe decision"""
    def __init__(
        self,
        do_metrics: str,
        do_sample: str
    ):
        self.do_metrics = do_metrics
        self.do_sample = do_sample


class _SwSampler(Sampler):
    """SolarWinds custom opentelemetry sampler which obeys configuration options provided by the NH/AO Backend."""
    def __init__(self, is_root_span: bool = False):
        # TODO use or remove
        self._is_root_span = is_root_span

    def get_description(self) -> str:
        return "SolarWinds custom opentelemetry sampler"

    def create_new_liboboe_decision(
        self,
        parent_span_context: SpanContext
    ) -> _LiboboeDecision:
        """Creates new liboboe decision using parent span context."""
        in_xtrace = traceparent_from_context(parent_span_context)
        tracestate = sw_from_context(parent_span_context)
        logger.debug("Making oboe decision with in_xtrace {0}, tracestate {1}".format(
            in_xtrace,
            tracestate
        ))
        do_metrics, do_sample, \
            _, _, _, _, _, _, _, _, _ = Context.getDecisions(
                in_xtrace,
                tracestate
            )
        return _LiboboeDecision(do_metrics, do_sample)

    def continue_liboboe_decision(
        self,
        parent_span_context: SpanContext
    ) -> _LiboboeDecision:
        """Creates liboboe decision to continue parent trace state decision"""
        trace_state = parent_span_context.trace_state
        try:
            sw_value = trace_state.get("sw")
        except AttributeError:
            logger.warning("Cannot continue decision if sw not in \
                tracestate ({0}). Making new decision.".format(trace_state))
            return self.create_new_liboboe_decision(parent_span_context)
        if not re.match(SW_FORMAT, sw_value):
            logger.warning("Cannot continue decision if tracestate sw not \
                in format <16_byte_span_id>-<8_bit_trace_flags>, nor if \
                trace_flags is anything but 01 or 00 ({0}). Making \
                new decision.".format(trace_state))
            return self.create_new_liboboe_decision(parent_span_context)

        do_sample = sw_value.split("-")[1]
        # TODO how do metrics work in OTel
        do_metrics = None
        logger.debug("Continuing decision as do_metrics: {0}, do_sample: {1}".format(
            do_metrics,
            do_sample
        ))
        return _LiboboeDecision(do_metrics, do_sample)

    def calculate_liboboe_decision(
        self,
        parent_span_context: SpanContext
    ) -> _LiboboeDecision:
        """Calculates oboe trace decision based on parent span context."""
        # No (valid) parent i.e. root span
        if not parent_span_context or not parent_span_context.is_valid:
            decision = self.create_new_liboboe_decision(parent_span_context)
        else:
            # tracestate nonexistent/non-parsable, or no sw KV
            trace_state = parent_span_context.trace_state
            if not trace_state or not trace_state.get("sw", None):
                decision = self.create_new_liboboe_decision(parent_span_context)
            # tracestate has sw KV
            else:
                decision = self.continue_liboboe_decision(parent_span_context)
        return decision

    def otel_decision_from_liboboe(
        self,
        liboboe_decision: _LiboboeDecision
    ) -> None:
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
        """Calculates trace_state based on parent span context and trace decision"""
        # No valid parent i.e. root span
        if not parent_span_context.is_valid:
            trace_state = self.create_new_trace_state(decision, parent_span_context)
        else:
            # tracestate nonexistent/non-parsable, or no sw KV
            trace_state = parent_span_context.trace_state
            if not trace_state or not trace_state.get("sw", None):
                trace_state = self.create_new_trace_state(decision, parent_span_context)
            # tracestate has sw KV
            else:
                # Update trace_state with span_id and sw trace_flags
                trace_state = trace_state.update(
                    "sw",
                    sw_from_span_and_decision(
                        parent_span_context.span_id,
                        decision.do_sample
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
        parent span context, and existing attributes."""
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
                "sw.tracestate_parent_id": span_id_from_int(
                    parent_span_context.span_id
                ),
                "sw.w3c.tracestate": trace_state.to_header()
            }
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
                        decision.do_sample
                    )
                )
                new_attributes["sw.w3c.tracestate"] = attr_trace_state.to_header()

            # Only set sw.tracestate_parent_id on the entry (root) span for this service
            new_attributes["sw.tracestate_parent_id"] = span_id_from_int(
                parent_span_context.span_id
            )

            attributes = new_attributes
            logger.debug("Set updated attributes: {0}".format(attributes))
        
        # attributes must be immutable for SamplingResult
        return MappingProxyType(attributes)

    def should_sample(
        self,
        parent_context: Optional["Context"],
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

        decision = self.calculate_liboboe_decision(parent_span_context)

        # TODO Set differently if not decision.RECORD_AND_SAMPLE
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
        Uses _SwSampler/liboboe if parent span is_remote and sampled.
        Uses OTEL default if parent span is_remote and NOT sampled (never sample).
        Uses OTEL defaults if parent span is_local.
        """
        super().__init__(
            root=_SwSampler(is_root_span=True),
            remote_parent_sampled=_SwSampler()
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
