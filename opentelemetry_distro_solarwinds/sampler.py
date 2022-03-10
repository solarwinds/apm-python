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
from opentelemetry_distro_solarwinds.ot_ao_transformer import transform_id

logger = logging.getLogger(__name__)

class _SwSampler(Sampler):
    """SolarWinds custom opentelemetry sampler which obeys configuration options provided by the NH/AO Backend."""
    def __init__(
        self,
        is_root_span: bool = False
    ):
        self._attributes = None
        self._decision = None
        self._do_metrics = None
        self._do_sample = None
        self._is_root_span = is_root_span
        self._parent_span_context = None
        self._span_id = None
        self._traceparent = None
        self._trace_state = None

    def get_description(self) -> str:
        return "SolarWinds custom opentelemetry sampler"

    def oboe_to_otel_decision(self) -> None:
        """Helper to make OTel decision from oboe outputs"""
        decision = Decision.DROP
        if self._do_metrics:
            # TODO: need to eck what record only actually means and how metrics work in OTel
            decision = Decision.RECORD_ONLY
        if self._do_sample:
            decision = Decision.RECORD_AND_SAMPLE
        return decision

    def make_trace_decision(self) -> None:
        """Helper to make oboe trace decision"""
        in_xtrace = self._traceparent
        tracestate = f"{self._span_id:016X}-{self._parent_span_context.trace_flags:02X}".lower()
        logger.debug(f"Making oboe decision with in_xtrace {in_xtrace}, tracestate {tracestate}")

        self._do_metrics, self._do_sample, \
        _, _, _, _, _, _, _, _, _ = Context.getDecisions(
            in_xtrace,
            tracestate
        )

    def set_trace_state(self) -> None:
        """Helper to set trace_state for sampling result based on parent span.
        Makes trace decision if needed
        """
        # traceparent none (root span) or not valid
        # or tracestate none or not parsable
        # or tracestate does not include valid sw
        if not self._parent_span_context.is_valid \
            or not self._trace_state \
            or not self._trace_state.get("sw", None):

            # New sampling decision
            self.make_trace_decision()

            # New tracestate with result of sampling decision
            self._trace_state = TraceState([(
                "sw",
                f"{self._span_id:016X}-{self._do_sample:02X}".lower()
            )])
            logger.debug(f"New trace_state: {self._trace_state}")

        # tracestate has valid sw included
        else:
            # Continue existing sw sampling decision
            self._do_sample = self._trace_state.get("sw").split('-')[1]
            if not self._do_sample in ["00", "01"]:
                raise Exception(f"Something went wrong checking tracestate: {self._do_sample}")

            # Update trace_state with span_id and sw trace_flags
            self._trace_state = self._trace_state.update(
                "sw",
                f"{self._span_id:016X}-{self._do_sample}".lower()
            )
            logger.debug(f"Updated trace_state: {self._trace_state}")

    def set_decision(self) -> None:
        """Helper to set OTel decision for sampling result"""
        self._decision = self.oboe_to_otel_decision()
        logger.debug(f"decision for otel: {self._decision}")

    def set_attributes(self) -> None:
        """Helper to set attributes based on parent span"""
        # Set attributes with sw.tracestate_parent_id and sw.w3c.tracestate
        logger.debug(f"Received attributes: {self._attributes}")
        if not self._attributes:
            self._attributes = {
                "sw.parent_span_id": f"{self._span_id:016X}".lower(),
                "sw.tracestate_parent_id": f"{self._span_id:016X}".lower(),
                "sw.w3c.tracestate": self._trace_state.to_header()
            }
            logger.debug(f"Set new attributes: {self._attributes}")
        else:
            # Copy existing MappingProxyType KV into new_attributes for modification
            # attributes may have other vendor info etc
            new_attributes = {}
            for k,v in self._attributes.items():
                new_attributes[k] = v

            # Add or Update sw KV in sw.w3c.tracestate
            if not new_attributes.get("sw.w3c.tracestate", None) or new_attributes.get("sw.w3c.tracestate"):
                new_attributes["sw.w3c.tracestate"] = self._trace_state.to_header()
            else:
                attr_trace_state = TraceState.from_header(new_attributes["sw.w3c.tracestate"])
                attr_trace_state.update(
                    "sw",
                    f"{self._span_id:016X}-{self._do_sample}".lower()
                )
                new_attributes["sw.w3c.tracestate"] = attr_trace_state.to_header()

            new_attributes["sw.parent_span_id"] = f"{self._span_id:016X}".lower()
            # Only set sw.tracestate_parent_id on the entry (root) span for this service
            # TODO: Or only at root span for the trace?
            #       Or if sw.tracestate_parent_id is not set?
            # if self._is_root_span:
            new_attributes["sw.tracestate_parent_id"] = f"{self._span_id:016X}".lower()

            # Replace
            self._attributes = new_attributes
            logger.debug(f"Set updated attributes: {self._attributes}")
        
        # attributes must be immutable
        self._attributes = MappingProxyType(self._attributes)

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
        # TraceContextTextMapPropagator extracts trace_state etc to SpanContext
        self._parent_span_context = get_current_span(
            parent_context
        ).get_span_context()
        self._traceparent = transform_id(self._parent_span_context)
        self._span_id = self._parent_span_context.span_id
        self._trace_state = self._parent_span_context.trace_state
        self._attributes = attributes

        # Set args for new SamplingResult
        self.set_trace_state()
        self.set_decision()
        self.set_attributes()

        # Return result to start_span caller
        # start_span creates a new SpanContext and Span after sampling_result
        return SamplingResult(
            self._decision,
            self._attributes if self._decision != Decision.DROP else None,
            self._trace_state,
        )


class ParentBasedSwSampler(ParentBased):
    """
    Sampler that respects its parent span's sampling decision, but otherwise
    samples according to the configurations from the NH/AO backend.
    """
    def __init__(self):
        super().__init__(
            # Use liboboe if no parent span
            root=_SwSampler(is_root_span=True),
            # Use liboboe if parent span is_remote and sampled
            remote_parent_sampled=_SwSampler(),
            # Use OTEL default if parent span is_remote and NOT sampled (never sample)
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
