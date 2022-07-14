""" This module provides a SolarWinds-specific sampler.

The custom sampler will fetch sampling configurations for the SolarWinds backend.
"""

import logging
from types import MappingProxyType
from typing import Optional, Sequence, Dict, TYPE_CHECKING

from opentelemetry.context.context import Context as OtelContext
from opentelemetry.sdk.trace.sampling import (Decision, ParentBased, Sampler,
                                              SamplingResult)
from opentelemetry.trace import Link, SpanKind, get_current_span
from opentelemetry.trace.span import SpanContext, TraceState
from opentelemetry.util.types import Attributes

from solarwinds_apm.apm_constants import (
    INTL_SWO_COMMA_W3C_SANITIZED,
    INTL_SWO_EQUALS_W3C_SANITIZED,
    INTL_SWO_TRACESTATE_KEY
)
from solarwinds_apm.apm_config import OboeTracingMode
from solarwinds_apm.traceoptions import XTraceOptions
from solarwinds_apm.w3c_transformer import W3CTransformer

if TYPE_CHECKING:
    from solarwinds_apm.apm_config import SolarWindsApmConfig
    from solarwinds_apm.extension.oboe import Context

logger = logging.getLogger(__name__)


class _SwSampler(Sampler):
    """SolarWinds custom opentelemetry sampler which obeys configuration options provided by the NH/AO Backend."""

    _INTERNAL_BUCKET_CAPACITY = "BucketCapacity"
    _INTERNAL_BUCKET_RATE = "BucketRate"
    _INTERNAL_SAMPLE_RATE = "SampleRate"
    _INTERNAL_SAMPLE_SOURCE = "SampleSource"
    _INTERNAL_SW_KEYS = "SWKeys"
    _LIBOBOE_CONTINUED = -1
    _SW_TRACESTATE_CAPTURE_KEY = "sw.w3c.tracestate"
    _SW_TRACESTATE_ROOT_KEY = "sw.tracestate_parent_id"
    _UNSET = -1
    _XTRACEOPTIONS_RESP_AUTH = "auth"
    _XTRACEOPTIONS_RESP_IGNORED = "ignored"
    _XTRACEOPTIONS_RESP_TRIGGER_IGNORED = "ignored"
    _XTRACEOPTIONS_RESP_TRIGGER_NOT_REQUESTED = "not-requested"
    _XTRACEOPTIONS_RESP_TRIGGER_TRACE = "trigger-trace"

    def __init__(self, apm_config: "SolarWindsApmConfig"):
        self.apm_config = apm_config
        self.context = None
        if self.apm_config.agent_enabled:
            from solarwinds_apm.extension.oboe import Context
            self.context = Context
        else:
            from solarwinds_apm.apm_noop import Context
            self.context = Context

    def get_description(self) -> str:
        return "SolarWinds custom opentelemetry sampler"

    def calculate_liboboe_decision(
        self,
        parent_span_context: SpanContext,
        xtraceoptions: Optional[XTraceOptions] = None,
    ) -> Dict:
        """Calculates oboe trace decision based on parent span context and APM config."""
        tracestring = None
        if parent_span_context.is_valid and parent_span_context.is_remote:
            tracestring = W3CTransformer.traceparent_from_context(
                parent_span_context
            )
        sw_member_value = parent_span_context.trace_state.get(INTL_SWO_TRACESTATE_KEY)

        # 'tracing_mode' is not supported in NH Python, so give as unset
        tracing_mode = self._UNSET

        trigger_trace_mode = OboeTracingMode.get_oboe_trigger_trace_mode(
            self.apm_config.get("trigger_trace")
        )
        # 'sample_rate' is legacy and not supported in NH Python, so give as unset
        sample_rate = self._UNSET

        options = None
        trigger_trace_request = 0
        signature = None
        timestamp = None
        if xtraceoptions:
            options = xtraceoptions.options_header
            trigger_trace_request = xtraceoptions.trigger_trace
            signature = xtraceoptions.signature
            timestamp = xtraceoptions.ts

        logger.debug(
            "Creating new oboe decision with "
            "tracestring: {}, "
            "sw_member_value: {}, "
            "tracing_mode: {}, "
            "sample_rate: {}, "
            "trigger_trace_request: {}, "
            "trigger_trace_mode: {}, "
            "options: {}, "
            "signature: {}, "
            "timestamp: {}".format(
            tracestring,
            sw_member_value,
            tracing_mode,
            sample_rate,
            trigger_trace_request,
            trigger_trace_mode,
            options,
            signature,
            timestamp
        ))
        do_metrics, do_sample, \
            rate, source, bucket_rate, bucket_cap, decision_type, \
            auth, status_msg, auth_msg, status = self.context.getDecisions(
                tracestring,
                sw_member_value,
                tracing_mode,
                sample_rate,
                trigger_trace_request,
                trigger_trace_mode,
                options,
                signature,
                timestamp
            )
        decision = {
            "do_metrics": do_metrics,
            "do_sample": do_sample,
            "rate": rate,
            "source": source,
            "bucket_rate": bucket_rate,
            "bucket_cap": bucket_cap,
            "decision_type": decision_type,
            "auth": auth,
            "status_msg": status_msg,
            "auth_msg": auth_msg,
            "status": status,
        }
        logger.debug("Got liboboe decision outputs: {}".format(decision))
        return decision

    def is_decision_continued(
        self,
        liboboe_decision: Dict
    ) -> bool:
        """Returns True if liboboe decision is a continued one, else False"""
        for val in [
            liboboe_decision["rate"],
            liboboe_decision["source"],
            liboboe_decision["bucket_rate"],
            liboboe_decision["bucket_cap"]
        ]:
            if val != self._LIBOBOE_CONTINUED:
                return False
        return True

    def otel_decision_from_liboboe(
        self,
        liboboe_decision: Dict
    ) -> Decision:
        """Formats OTel decision from liboboe decision"""
        decision = Decision.DROP
        if liboboe_decision["do_sample"]:
            decision = Decision.RECORD_AND_SAMPLE  # even if not do_metrics
        elif liboboe_decision["do_metrics"]:
            decision = Decision.RECORD_ONLY
        logger.debug("OTel decision created: {}".format(decision))
        return decision

    def create_xtraceoptions_response_value(
        self,
        decision: Dict,
        parent_span_context: SpanContext,
        xtraceoptions: XTraceOptions
    ) -> str:
        """Use decision and xtraceoptions to create sanitized xtraceoptions
        response kv with W3C tracestate-allowed delimiters:
        EQUALS_W3C_SANITIZED instead of EQUALS
        COMMA_W3C_SANITIZED instead of COMMA
        """
        response = []

        if xtraceoptions.signature and decision["auth_msg"]:
            response.append(INTL_SWO_EQUALS_W3C_SANITIZED.join([
                self._XTRACEOPTIONS_RESP_AUTH,
                decision["auth_msg"]
            ]))

        if not decision["auth"] or decision["auth"] < 1:
            trigger_msg = ""
            if xtraceoptions.trigger_trace:
                # If a traceparent header was provided then oboe does not generate the message
                tracestring = None
                if parent_span_context.is_valid and parent_span_context.is_remote:
                    tracestring = W3CTransformer.traceparent_from_context(
                        parent_span_context
                    )

                if tracestring and decision["decision_type"] == 0:
                    trigger_msg = self._XTRACEOPTIONS_RESP_TRIGGER_IGNORED
                else:
                    trigger_msg = decision["status_msg"]
            else:
                trigger_msg = self._XTRACEOPTIONS_RESP_TRIGGER_NOT_REQUESTED
            response.append(INTL_SWO_EQUALS_W3C_SANITIZED.join([
                self._XTRACEOPTIONS_RESP_TRIGGER_TRACE,
                trigger_msg
            ]))

        if xtraceoptions.ignored:
            response.append(
                INTL_SWO_EQUALS_W3C_SANITIZED.join([
                    self._XTRACEOPTIONS_RESP_IGNORED,
                    (INTL_SWO_COMMA_W3C_SANITIZED.join(xtraceoptions.ignored))
                ])
            )

        return ";".join(response)

    def create_new_trace_state(
        self,
        decision: Dict,
        parent_span_context: SpanContext,
        xtraceoptions: Optional[XTraceOptions] = None,
    ) -> TraceState:
        """Creates new TraceState based on trace decision, parent span id,
        and x-trace-options if provided"""
        trace_state = TraceState([(
            INTL_SWO_TRACESTATE_KEY,
            W3CTransformer.sw_from_span_and_decision(
                parent_span_context.span_id,
                W3CTransformer.trace_flags_from_int(decision["do_sample"])
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
        decision: Dict,
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
                    INTL_SWO_TRACESTATE_KEY,
                    W3CTransformer.sw_from_span_and_decision(
                        parent_span_context.span_id,
                        W3CTransformer.trace_flags_from_int(decision["do_sample"])
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

    def remove_response_from_sw(
        self,
        trace_state: TraceState
    ) -> TraceState:
        """Remove xtraceoptions response from tracestate"""
        return trace_state.delete(XTraceOptions.get_sw_xtraceoptions_response_key())

    def add_tracestate_capture_to_attributes_dict(
        self,
        attributes_dict: dict,
        decision: Dict,
        trace_state: TraceState,
        parent_span_context: SpanContext,
    ) -> dict:
        """Calculate and add SW tracestate capture to attributes_dict,
        which is a dict not an Attributes/MappingProxy object"""
        tracestate_capture = attributes_dict.get(self._SW_TRACESTATE_CAPTURE_KEY, None)
        if not tracestate_capture:
            trace_state_no_response = self.remove_response_from_sw(trace_state)
        else:
            # Must retain all potential tracestate pairs for attributes
            attr_trace_state = TraceState.from_header([
                tracestate_capture
            ])
            new_attr_trace_state = attr_trace_state.update(
                INTL_SWO_TRACESTATE_KEY,
                W3CTransformer.sw_from_span_and_decision(
                    parent_span_context.span_id,
                    W3CTransformer.trace_flags_from_int(decision["do_sample"])
                )
            )
            trace_state_no_response = self.remove_response_from_sw(new_attr_trace_state)
        attributes_dict[self._SW_TRACESTATE_CAPTURE_KEY] = trace_state_no_response.to_header()
        return attributes_dict

    def calculate_attributes(
        self,
        span_name: str,
        attributes: Attributes,
        decision: Dict,
        trace_state: TraceState,
        parent_span_context: SpanContext,
        xtraceoptions: XTraceOptions
    ) -> Attributes or None:
        """Calculates Attributes or None based on trace decision, trace state,
        parent span context, xtraceoptions, and existing attributes."""
        logger.debug("Received attributes: {}".format(attributes))
        # Don't set attributes if not tracing
        otel_decision = self.otel_decision_from_liboboe(decision)
        if not Decision.is_sampled(otel_decision):
            logger.debug("Trace decision not is_sampled - not setting attributes")
            return None
        
        new_attributes = {}

        # Always (root or is_remote) set _INTERNAL_SW_KEYS if injected
        internal_sw_keys = xtraceoptions.sw_keys
        if internal_sw_keys:
            new_attributes[self._INTERNAL_SW_KEYS] = internal_sw_keys
    
        # Always (root or is_remote) set service entry internal KVs       
        new_attributes[self._INTERNAL_BUCKET_CAPACITY] = "{}".format(decision["bucket_cap"])
        new_attributes[self._INTERNAL_BUCKET_RATE] = "{}".format(decision["bucket_rate"])
        new_attributes[self._INTERNAL_SAMPLE_RATE] = decision["rate"]
        new_attributes[self._INTERNAL_SAMPLE_SOURCE] = decision["source"]
        logger.debug(
            "Set attributes with service entry internal KVs: {}".format(new_attributes)
        )

        # Trace's root span has no valid traceparent nor tracestate
        # so we can't calculate remaining attributes
        if not parent_span_context.is_valid or not trace_state:
            logger.debug(
                "No valid traceparent or no tracestate - returning attributes: {}"
                .format(new_attributes)
            )

            if new_attributes:
                # attributes must be immutable for SamplingResult
                return MappingProxyType(new_attributes)
            else:
                return None

        if not attributes:
            # _SW_TRACESTATE_ROOT_KEY is set once per trace, if possible
            sw_value = parent_span_context.trace_state.get(INTL_SWO_TRACESTATE_KEY, None)
            if sw_value:
                new_attributes[self._SW_TRACESTATE_ROOT_KEY]= W3CTransformer.span_id_from_sw(sw_value)
        else:
            # Copy existing MappingProxyType KV into new_attributes for modification.
            # attributes may have other vendor info etc
            for k,v in attributes.items():
                new_attributes[k] = v

        new_attributes = self.add_tracestate_capture_to_attributes_dict(
            new_attributes,
            decision,
            trace_state,
            parent_span_context,
        )

        logger.debug("Setting attributes: {}".format(new_attributes))

        # attributes must be immutable for SamplingResult
        return MappingProxyType(new_attributes)

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

        liboboe_decision = self.calculate_liboboe_decision(
            parent_span_context,
            xtraceoptions
        )

        # Always calculate trace_state for propagation
        new_trace_state = self.calculate_trace_state(
            liboboe_decision,
            parent_span_context,
            xtraceoptions
        )
        new_attributes = self.calculate_attributes(
            name,
            attributes,
            liboboe_decision,
            new_trace_state,
            parent_span_context,
            xtraceoptions
        )
        otel_decision = self.otel_decision_from_liboboe(liboboe_decision)

        return SamplingResult(
            otel_decision,
            new_attributes if Decision.is_sampled(otel_decision) else None,
            new_trace_state,
        )


class ParentBasedSwSampler(ParentBased):
    """
    Sampler that respects its parent span's sampling decision, but otherwise
    samples according to the configurations from the NH/AO backend.

    Requires "SolarWindsApmConfig".
    """
    def __init__(self, apm_config: "SolarWindsApmConfig"):
        """
        Uses _SwSampler/liboboe if no parent span.
        Uses _SwSampler/liboboe if parent span is_remote.
        Uses OTEL defaults if parent span is_local.
        """
        super().__init__(
            root=_SwSampler(apm_config),
            remote_parent_sampled=_SwSampler(apm_config),
            remote_parent_not_sampled=_SwSampler(apm_config)
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
