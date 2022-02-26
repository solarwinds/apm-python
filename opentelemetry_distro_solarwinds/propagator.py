import logging
import re
import typing

from opentelemetry import trace
from opentelemetry.context.context import Context
from opentelemetry.propagators import textmap
from opentelemetry.trace.span import TraceState

logger = logging.getLogger(__file__)

class SolarWindsFormat(textmap.TextMapPropagator):
    """
    Extracts and injects SolarWinds tracestate header

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
        """
        Extracts sw tracestate from carrier into SpanContext
        """
        # TODO: Is this needed if this is always used
        #       in composite with TraceContextTextMapPropagator?
        #       If not, return context?
        # TODO: If so, are basic validity checks needed?
        
        # Get span_id, trace_flags from carrier's traceparent header
        traceparent_header = getter.get(carrier, self._TRACEPARENT_HEADER_NAME)
        if not traceparent_header:
            return context
        match = re.search(self._TRACEPARENT_HEADER_FORMAT_RE, traceparent_header[0])
        if not match:
            return context
        version = match.group(1)
        trace_id = match.group(2)
        span_id = match.group(3)
        trace_flags = match.group(4)

        # Prepare context with carrier's tracestate
        tracestate_header = getter.get(carrier, self._TRACESTATE_HEADER_NAME)
        # TODO: Should sw tracestate be added/updated here?
        if tracestate_header is None:
            tracestate = None
        else:
            tracestate = TraceState.from_header(tracestate_header)

        span_context = trace.SpanContext(
            trace_id=int(trace_id, 16),
            span_id=int(span_id, 16),
            is_remote=True,
            trace_flags=trace.TraceFlags(trace_flags),
            trace_state=tracestate,
        )
        return trace.set_span_in_context(
            trace.NonRecordingSpan(span_context), context
        )

    def inject(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        setter: textmap.Setter = textmap.default_setter,
    ) -> None:
        """
        Injects sw tracestate from SpanContext into carrier for HTTP request

        See also: https://www.w3.org/TR/trace-context-1/#mutating-the-tracestate-field
        """
        # TODO: Are basic validity checks necessary if this is always used
        #       in composite with TraceContextTextMapPropagator?
        span = trace.get_current_span(context)
        span_context = span.get_span_context()
        span_id = span_context.span_id
        trace_state = span_context.trace_state
        trace_flags = span_context.trace_flags

        # TODO: This isn't working
        # Prepare carrier with context's or new tracestate
        if trace_state:
            # Check if trace_state already contains sw KV
            if "sw" in trace_state.keys():
                # If so, modify current span_id and trace_flags, and move to beginning of list
                logger.debug(f"Updating trace state with {span_id}-{trace_flags}")
                trace_state.update("sw", f"{span_id}-{trace_flags}")
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
        """
        Returns a set with the fields set in `inject`
        """
        return {self._TRACEPARENT_HEADER_NAME, self._TRACESTATE_HEADER_NAME}
