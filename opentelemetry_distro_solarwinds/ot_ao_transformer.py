"""Provides functionality to transform OpenTelemetry Data to SolarWinds AppOptics data.
"""

import logging

logger = logging.getLogger(__file__)


def transform_id(span_context):
    """Generates an AppOptics X-Trace ID from the provided OpenTelemetry span context."""
    xtr = "2B00000000{0:032X}{1:016X}0{2}".format(span_context.trace_id,
                                                  span_context.span_id,
                                                  span_context.trace_flags)
    logger.debug("Generated X-Trace %s from span context %s", xtr,
                 span_context)
    return xtr
