"""Provides functionality to transform OpenTelemetry Data to SolarWinds Observability data.
"""

import logging
from opentelemetry.sdk.trace import SpanContext

logger = logging.getLogger(__name__)

class W3CTransformer():
    """Transforms inputs to W3C-compliant data for SolarWinds context propagation"""

    _DECISION = "{}"
    _SPAN_ID_HEX = "{:016x}"
    _TRACE_FLAGS_HEX = "{:02x}"
    _TRACE_ID_HEX = "{:032x}"
    _VERSION = "00"

    @classmethod
    def span_id_from_int(cls, span_id: int) -> str:
        """Formats span ID as 16-byte hexadecimal string"""
        return cls._SPAN_ID_HEX.format(span_id)

    @classmethod
    def span_id_from_sw(cls, sw: str) -> str:
        """Formats span ID from sw tracestate value"""
        return sw.split("-")[0]

    @classmethod
    def trace_flags_from_int(cls, trace_flags: int) -> str:
        """Formats trace flags as 8-bit field"""
        return cls._TRACE_FLAGS_HEX.format(trace_flags)

    @classmethod
    def traceparent_from_context(cls, span_context: SpanContext) -> str:
        """Generates a liboboe W3C compatible trace_context from
        provided OTel span context."""
        template = "-".join([
            cls._VERSION,
            cls._TRACE_ID_HEX,
            cls._SPAN_ID_HEX,
            cls._TRACE_FLAGS_HEX
        ])
        xtr = template.format(
            span_context.trace_id,
            span_context.span_id,
            span_context.trace_flags
        )
        logger.debug("Generated traceparent {} from {}".format(xtr, span_context))
        return xtr

    @classmethod
    def sw_from_context(cls, span_context: SpanContext) -> str:
        """Formats tracestate sw value from SpanContext as 16-byte span_id
        with 8-bit trace_flags.
        
        Example: 1a2b3c4d5e6f7g8h-01"""
        sw = "-".join([cls._SPAN_ID_HEX, cls._TRACE_FLAGS_HEX])
        return sw.format(span_context.span_id, span_context.trace_flags)

    @classmethod
    def sw_from_span_and_decision(cls, span_id: int, decision: str) -> str:
        """Formats tracestate sw value from span_id and liboboe decision
        as 16-byte span_id with 8-bit trace_flags.
        
        Example: 1a2b3c4d5e6f7g8h-01"""
        sw = "-".join([cls._SPAN_ID_HEX, cls._DECISION])
        return sw.format(span_id, decision)
