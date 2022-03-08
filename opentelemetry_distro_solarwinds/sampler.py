""" This module provides a SolarWinds-specific sampler.

The custom sampler will fetch sampling configurations for the SolarWinds backend.
"""

import logging
from types import MappingProxyType
from typing import Optional, Sequence

from opentelemetry.sdk.trace.sampling import (Decision, ParentBased, Sampler,
                                              SamplingResult)
from opentelemetry.trace import SpanKind, get_current_span
from opentelemetry.trace.span import TraceState
from opentelemetry.util.types import Attributes

from opentelemetry_distro_solarwinds.extension.oboe import Context

logger = logging.getLogger(__name__)


def oboe_to_otel_decision(do_metrics, do_sample):
    """Helper to make OTel decision from oboe outputs"""
    decision = Decision.DROP
    if do_metrics:
        # TODO: need to eck what record only actually means and how metrics work in OTel
        decision = Decision.RECORD_ONLY
    if do_sample:
        decision = Decision.RECORD_AND_SAMPLE
    return decision

class _SwSampler(Sampler):
    """SolarWinds custom opentelemetry sampler which obeys configuration options provided by the NH/AO Backend."""
    def get_description(self) -> str:
        return "SolarWinds custom opentelemetry sampler"

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
        Use liboboe trace decision for returned OTel SamplingResult
        """

        parent_span_context = get_current_span(
            parent_context
        ).get_span_context()

        # (0) Debugging
        # import ipdb
        # ipdb.set_trace()
        # Unique the first time then always same
        # logger.debug(f"trace_id: {trace_id}")
        # logger.debug(f"trace_id as 032X: {trace_id:032X}".lower())
        # get_current_span > get_value > get_current() gets current context in execution
        # logger.debug(f"parent_context: {parent_context}")
        logger.debug(f"parent_span_context: {parent_span_context}")
        # [] at django-a, non-empty at django-b (from custom propagator?)
        # logger.debug(f"parent_span_context.trace_state: {parent_span_context.trace_state}")
        # False at django-a, True at django-b
        logger.debug(f"parent_span_context.is_valid: {parent_span_context.is_valid}")
        # # False at django-a, True at django-b
        # # At this point with super() init of ParentBased
        # # we shouldn't need to check this here
        # logger.debug(f"parent_span_context.is_remote: {parent_span_context.is_remote}")
        
        do_metrics = None
        do_sample = None
        trace_state = parent_span_context.trace_state

        # traceparent none (root span) or not valid
        # or
        # tracestate none or not parsable
        # or
        # tracestate does not include valid sw
        if not parent_span_context.is_valid \
            or not trace_state \
            or not trace_state.get("sw", None):

            # New sampling decision
            do_metrics, do_sample, \
            _, _, _, _, _, _, _, _, _ = Context.getDecisions(
                f"{trace_id:032X}".lower(),
                repr(trace_state)           # ???
            )

            # # Debugging
            # trace_id_hex_str = f"{trace_id:032X}".lower()
            # trace_state_str = repr(trace_state)
            # logger.debug(f"getDecisions with {trace_id_hex_str} and {trace_state_str}: {do_sample}")

            # New tracestate with sampling decision
            trace_state = TraceState([(
                "sw",
                f"{parent_span_context.span_id:016X}-{do_sample:02X}".lower()
            )])
            logger.debug(f"New trace_state: {trace_state}")

        # tracestate has valid sw included
        else:
            # Continue existing sw sampling decision
            do_sample = trace_state.get("sw").split('-')[1]
            if not do_sample in ["00", "01"]:
                raise Exception(f"Something went wrong checking tracestate: {do_sample}")

            # Update trace_state with span_id and sw trace_flags
            trace_state = trace_state.update(
                "sw",
                f"{parent_span_context.span_id:016X}-{do_sample}".lower()
            )
            logger.debug(f"Updated trace_state: {trace_state}")
        
        decision = oboe_to_otel_decision(do_metrics, do_sample)
        logger.debug(f"decision for otel: {decision}")

        # TODO
        # Set attributes with sw.tracestate_parent_id and sw.w3c.tracestate
        attributes = {
            "sw.tracestate_parent_id": f"{parent_span_context.span_id:016X}".lower(),
            "sw.w3c.tracestate": trace_state
        }
        logger.debug(f"attributes: {attributes}")

        # Return result to start_span caller
        # start_span creates a new SpanContext and Span after sampling_result
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
        super().__init__(
            # Use liboboe if no parent span
            root=_SwSampler(),
            # Use liboboe if parent span is_remote
            remote_parent_sampled=_SwSampler(),
            remote_parent_not_sampled=_SwSampler(),
            # Use OTEL defaults if parent span is_local
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
