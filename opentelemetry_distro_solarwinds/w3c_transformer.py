"""Provides functionality to transform OpenTelemetry Data to SolarWinds AppOptics data.
"""

import logging
from opentelemetry.context.context import Context

logger = logging.getLogger(__file__)

def span_id_from_int(span_id: int) -> str:
    """Formats span ID as 16-byte hexadecimal string"""
    return "{:016x}".format(span_id)

def trace_flags_from_int(trace_flags: int) -> str:
    """Formats trace flags as 8-bit field"""
    return "{:02x}".format(trace_flags)

def traceparent_from_context(span_context: Context) -> str:
    """Generates a liboboe W3C compatible trace_context from provided OTel span context."""
    xtr = "00-{0:032X}-{1:016X}-{2:02X}".format(span_context.trace_id,
                                            span_context.span_id,
                                            span_context.trace_flags)
    logger.debug("Generated traceparent %s from %s", xtr,
                 span_context)
    return xtr

def sw_from_context(span_context: Context) -> str:
    """Formats tracestate sw value from SpanContext
    as 16-byte span_id with 8-bit trace_flags.
    
    Example: 1122334455667788-01"""
    return "{0:016x}-{1:02x}".format(span_context.span_id,
                                     span_context.trace_flags)

def sw_from_span_and_decision(span_id: int, decision: str) -> str:
    """Formats tracestate sw value from span_id and liboboe decision
    as 16-byte span_id with 8-bit trace_flags.
    
    Example: 1122334455667788-01"""
    return "{0:016x}-{1}".format(span_id, decision)
