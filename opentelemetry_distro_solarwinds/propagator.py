import logging
import re
import typing

from opentelemetry import trace
from opentelemetry.context.context import Context
from opentelemetry.propagators import textmap
from opentelemetry.trace.span import TraceState

from opentelemetry_distro_solarwinds.w3c_transformer import (
    span_id_from_int,
    trace_flags_from_int
)

logger = logging.getLogger(__file__)

class SolarWindsPropagator(textmap.TextMapPropagator):
    """Extracts and injects SolarWinds tracestate header

    See also https://www.w3.org/TR/trace-context-1/
    """
    _TRACEPARENT_HEADER_NAME = "traceparent"
    _TRACESTATE_HEADER_NAME = "tracestate"
    _TRACEPARENT_HEADER_FORMAT = (
        "^[ \t]*([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})"
        + "(-.*)?[ \t]*$"
    )
    _TRACEPARENT_HEADER_FORMAT_RE = re.compile(_TRACEPARENT_HEADER_FORMAT)

    def extract(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        getter: textmap.Getter = textmap.default_getter,
    ) -> Context:
        """Extracts sw tracestate from carrier into SpanContext
        
        Must be used in composite with TraceContextTextMapPropagator"""
        return context

    def inject(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        setter: textmap.Setter = textmap.default_setter,
    ) -> None:
        """Injects sw tracestate from SpanContext into carrier for HTTP request.

        Must be used in composite with TraceContextTextMapPropagator"""
        span = trace.get_current_span(context)
        span_context = span.get_span_context()
        span_id = span_id_from_int(span_context.span_id)
        trace_flags = trace_flags_from_int(span_context.trace_flags)
        trace_state = span_context.trace_state

        # Prepare carrier with context's or new tracestate
        if trace_state:
            # Check if trace_state already contains sw KV
            if "sw" in trace_state.keys():
                # If so, modify current span_id and trace_flags, and move to beginning of list
                logger.debug(f"Updating trace state with {span_id}-{trace_flags}")
                trace_state = trace_state.update("sw", f"{span_id}-{trace_flags}")

            else:
                # If not, add sw KV to beginning of list
                logger.debug(f"Adding KV to trace state with {span_id}-{trace_flags}")
                trace_state.add("sw", f"{span_id}-{trace_flags}")
        else:
            logger.debug(f"Creating new trace state with {span_id}-{trace_flags}")
            trace_state = TraceState([("sw", f"{span_id}-{trace_flags}")])

        setter.set(
            carrier, self._TRACESTATE_HEADER_NAME, trace_state.to_header()
        )

    @property
    def fields(self) -> typing.Set[str]:
        """Returns a set with the fields set in `inject`"""
        return {
            self._TRACEPARENT_HEADER_NAME,
            self._TRACESTATE_HEADER_NAME
        }
