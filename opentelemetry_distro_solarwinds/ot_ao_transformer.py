"""Provides functionality to transform OpenTelemetry Data to SolarWinds AppOptics data.
"""

import logging
import os

logger = logging.getLogger(__file__)


def transform_id(span_context):
    """Generates a liboboe W3C compatible trace_context from provided OTel span context."""
    xtr = "00-{0:032X}-{1:016X}-{2:02X}".format(span_context.trace_id,
                                            span_context.span_id,
                                            span_context.trace_flags)
    logger.debug("Generated trace_context %s from span context %s", xtr,
                 span_context)
    return xtr
