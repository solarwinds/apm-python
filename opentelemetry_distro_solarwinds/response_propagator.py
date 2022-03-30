import logging
import typing

from opentelemetry import trace
from opentelemetry.context.context import Context
from opentelemetry.instrumentation.propagators import ResponsePropagator
from opentelemetry.propagators import textmap

from opentelemetry_distro_solarwinds.w3c_transformer import traceparent_from_context

logger = logging.getLogger(__file__)

class SolarWindsTraceResponsePropagator(ResponsePropagator):
    """
    """
    _HTTP_HEADER_ACCESS_CONTROL_EXPOSE_HEADERS = "Access-Control-Expose-Headers"
    _XTRACE_HEADER_NAME = "x-trace"
    _XTRACEOPTIONS_RESPONSE_HEADER_NAME = "x-trace-options-response"
    
    def inject(
        self,
        carrier: textmap.CarrierT,
        context: typing.Optional[Context] = None,
        setter: textmap.Setter = textmap.default_setter,
    ) -> None:
        """Injects x-trace and options-response into the HTTP response carrier."""
        span = trace.get_current_span(context)
        span_context = span.get_span_context()
        if span_context == trace.INVALID_SPAN_CONTEXT:
            return
        
        x_trace = traceparent_from_context(span_context)

        # TODO: Should be based on x-trace-options tt
        sampled = 'trigger-trace='
        if span_context.trace_flags:
            sampled += 'ok'
        else:
            sampled += 'rate-exceeded'

        exposed_headers = "{0},{1}".format(
            self._XTRACE_HEADER_NAME,
            self._XTRACEOPTIONS_RESPONSE_HEADER_NAME
        )
        setter.set(
            carrier,
            self._XTRACE_HEADER_NAME,
            x_trace,
        )
        setter.set(
            carrier,
            self._XTRACEOPTIONS_RESPONSE_HEADER_NAME,
            sampled,
        )
        setter.set(
            carrier,
            self._HTTP_HEADER_ACCESS_CONTROL_EXPOSE_HEADERS,
            exposed_headers,
        )